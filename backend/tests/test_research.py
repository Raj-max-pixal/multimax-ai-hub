from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.auth.dependencies import _get_auth_service, get_current_user_id
from app.research import api
from app.ai.exceptions import RateLimitError


@pytest.fixture
def research_client(monkeypatch):
    search = AsyncMock(return_value=[{"title": "Evidence", "url": "https://example.org/paper", "snippet": "Observed result."}])
    monkeypatch.setattr(api, "search_web", search)
    manager = SimpleNamespace(
        generate=AsyncMock(return_value=SimpleNamespace(content="Evidence supports this [1].", model="gemini-test")),
        get_provider_names=lambda: ["gemini"],
        get_provider=lambda _: SimpleNamespace(config=SimpleNamespace(default_model="gemini-test")),
    )
    app = FastAPI()
    app.include_router(api.router)
    app.state.multimax = SimpleNamespace(ai_manager=manager)
    app.dependency_overrides[get_current_user_id] = lambda: "test-user"
    app.dependency_overrides[_get_auth_service] = lambda: SimpleNamespace(get_current_user=AsyncMock(return_value=None))
    with TestClient(app) as client:
        yield client, app, manager, search


@pytest.mark.parametrize("mode", list(api.MODES))
def test_all_modes_use_evidence_and_configured_provider(research_client, mode):
    client, _, manager, search = research_client
    response = client.post("/api/research/search", json={"query": " test question ", "mode": mode})
    assert response.status_code == 200
    assert len(response.json()["sources"]) == 1  # Deduplicate broader searches.
    assert response.json()["model"] == "gemini-test"
    assert search.await_count == (2 if mode in {"deep", "report"} else 1)
    assert search.call_args.args[1] == (mode == "news")
    generation = manager.generate.call_args.args[0]
    assert api.MODES[mode] in generation.system_prompt
    assert "Observed result." in generation.messages[0]["content"]
    assert manager.generate.call_args.kwargs["provider_name"] == "gemini"


def test_authentication_required(research_client):
    client, app, manager, search = research_client
    app.dependency_overrides[get_current_user_id] = get_current_user_id
    assert client.post("/api/research/search", json={"query": "hello"}).status_code == 401
    search.assert_not_called()
    manager.generate.assert_not_called()


@pytest.mark.parametrize("payload", [{"query": " "}, {"query": "a" * 2001}, {"query": "test", "mode": "unknown"}, {"query": "test", "max_sources": 11}])
def test_invalid_input(research_client, payload):
    client, _, manager, search = research_client
    assert client.post("/api/research/search", json=payload).status_code == 422
    search.assert_not_called()


@pytest.mark.parametrize("failure", [[], httpx.ConnectError("private-upstream-detail"), TimeoutError()])
def test_search_failure_never_fabricates_sources(research_client, failure):
    client, _, manager, search = research_client
    if isinstance(failure, Exception):
        search.side_effect = failure
    else:
        search.return_value = failure
    response = client.post("/api/research/search", json={"query": "test"})
    assert response.status_code == 503
    assert "private-upstream-detail" not in response.text
    manager.generate.assert_not_called()


@pytest.mark.parametrize("failure,status", [(RateLimitError(message="secret"), 429), (TimeoutError(), 504), (RuntimeError("secret"), 502)])
def test_model_errors_are_safe_and_retryable(research_client, failure, status):
    client, _, manager, _ = research_client
    manager.generate.side_effect = failure
    response = client.post("/api/research/search", json={"query": "test"})
    assert response.status_code == status
    assert "secret" not in response.text


def test_empty_answer_and_source_limit(research_client):
    client, _, manager, search = research_client
    search.return_value = [{"title": "Source", "url": f"https://example.org/{i}", "snippet": "data"} for i in range(12)]
    response = client.post("/api/research/search", json={"query": "test", "max_sources": 3, "model": "local-model"})
    assert len(response.json()["sources"]) == 3
    assert manager.generate.call_args.kwargs["provider_name"] == "ollama"
    manager.generate.return_value.content = " "
    assert client.post("/api/research/search", json={"query": "test"}).status_code == 502


@pytest.mark.parametrize("url", ["javascript:alert(1)", "file:///etc/passwd", "http://localhost/test", "http://127.0.0.1/test", "http://10.0.0.1/", "https://user:token@example.org", "https://example.org\\@localhost/", "http://[::1]/"])
def test_unsafe_source_urls_are_rejected(url):
    assert api.source_url(url) is None


def test_search_html_parser_and_redirect_unwrapping():
    parser = api.SearchParser()
    parser.feed('<a href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.org%2Fpaper" class="result__a">A <b>study</b></a><div class="result__snippet">Evidence &amp; details</div>')
    assert parser.results == [{"title": "A study", "url": "https://example.org/paper", "snippet": "Evidence & details"}]


@pytest.mark.asyncio
async def test_search_transport_is_bounded(monkeypatch):
    original = httpx.AsyncClient
    def respond(request):
        assert request.url.host == "html.duckduckgo.com"
        assert request.url.params["df"] == "w"
        return httpx.Response(200, content=b"x" * 2_000_001)
    monkeypatch.setattr(api.httpx, "AsyncClient", lambda **kwargs: original(transport=httpx.MockTransport(respond), **kwargs))
    with pytest.raises(api.HTTPException) as error:
        await api.search_web("test", recent=True)
    assert error.value.status_code == 502


@pytest.mark.asyncio
async def test_search_challenge_is_not_treated_as_evidence(monkeypatch):
    original = httpx.AsyncClient
    monkeypatch.setattr(api.httpx, "AsyncClient", lambda **kwargs: original(
        transport=httpx.MockTransport(lambda _: httpx.Response(202, text="challenge-form")), **kwargs,
    ))
    with pytest.raises(api.HTTPException) as error:
        await api.search_web("test")
    assert error.value.status_code == 503
    assert "verification challenge" in error.value.detail
