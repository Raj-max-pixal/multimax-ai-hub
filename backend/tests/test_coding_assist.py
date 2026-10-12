from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.ai.exceptions import InvalidApiKeyError, InvalidModelError, RateLimitError, ProviderUnavailableError
from app.auth.dependencies import _get_auth_service, get_current_user_id
from app.coding.api import CODING_TASKS, router
from app.core.database import get_db_session


@pytest.fixture
def coding_client():
    manager = SimpleNamespace(
        generate=AsyncMock(return_value=SimpleNamespace(content="Useful coding result", model="gemini-test")),
        get_provider_names=lambda: ["ollama", "gemini"],
        get_provider=lambda name: SimpleNamespace(config=SimpleNamespace(default_model="gemini-test")),
    )
    app = FastAPI()
    app.include_router(router)
    app.state.multimax = SimpleNamespace(ai_manager=manager)
    app.dependency_overrides[get_current_user_id] = lambda: "test-user"
    app.dependency_overrides[_get_auth_service] = lambda: SimpleNamespace()
    with TestClient(app) as client:
        yield client, manager, app


@pytest.mark.parametrize("task", list(CODING_TASKS))
def test_all_coding_tools_route_to_configured_provider(coding_client, task):
    client, manager, _ = coding_client
    result = client.post("/api/v1/coding/assist", json={
        "task": task, "prompt": "Help with addition", "code": "def add(a, b): return a + b", "language": "Python",
    })
    assert result.status_code == 200
    assert result.json()["answer"] == "Useful coding result"
    call = manager.generate.call_args
    assert call.kwargs["provider_name"] == "gemini"
    assert CODING_TASKS[task] in call.args[0].messages[0]["content"]
    assert "def add" in call.args[0].messages[0]["content"]


def test_coding_requires_login(coding_client):
    client, manager, app = coding_client
    app.dependency_overrides.pop(get_current_user_id)
    result = client.post("/api/v1/coding/assist", json={"task": "generate", "prompt": "hello"})
    assert result.status_code == 401
    manager.generate.assert_not_called()


@pytest.mark.parametrize("body", [
    {"task": "unsupported", "prompt": "hi"},
    {"task": "fix", "prompt": "  ", "code": "\n"},
    {"task": "fix", "prompt": "a" * 8001},
])
def test_invalid_requests_do_not_call_model(coding_client, body):
    client, manager, _ = coding_client
    assert client.post("/api/v1/coding/assist", json=body).status_code == 422
    manager.generate.assert_not_called()


def test_code_only_requests_and_credential_redaction(coding_client):
    client, manager, _ = coding_client
    manager.generate.return_value.content = 'API_KEY="private-output"'
    result = client.post("/api/v1/coding/assist", json={"task": "review", "code": 'API_KEY="private-input"', "model": "phi3:latest"})
    assert result.status_code == 200
    assert "private-output" not in result.text
    assert "private-input" not in manager.generate.call_args.args[0].messages[0]["content"]
    assert manager.generate.call_args.kwargs["provider_name"] == "ollama"


@pytest.mark.parametrize("error,status", [
    (RuntimeError("credential=private-value"), 502),
    (InvalidApiKeyError(message="private-value"), 503),
    (InvalidModelError(message="private-value"), 400),
    (RateLimitError(message="private-value"), 429),
    (TimeoutError("private-value"), 504),
])
def test_provider_errors_are_actionable_without_exposing_details(coding_client, error, status):
    client, manager, _ = coding_client
    manager.generate.side_effect = error
    result = client.post("/api/v1/coding/assist", json={"task": "fix", "prompt": "fix this"})
    assert result.status_code == status
    assert "private-value" not in result.text
    assert result.json()["detail"]


def test_empty_model_answer_is_a_retryable_failure(coding_client):
    client, manager, _ = coding_client
    manager.generate.return_value.content = "  "
    assert client.post("/api/v1/coding/assist", json={"task": "fix", "prompt": "help"}).status_code == 502


@pytest.mark.parametrize("recovers", [False, True])
def test_temporary_provider_outage_retries_once(coding_client, recovers):
    client, manager, _ = coding_client
    error = ProviderUnavailableError()
    cause = RuntimeError("upstream error")
    cause.response = SimpleNamespace(status_code=503)
    error.__cause__ = cause
    manager.generate.side_effect = [error, manager.generate.return_value if recovers else error]
    result = client.post("/api/v1/coding/assist", json={"task": "explain", "code": "print(1)"})
    assert result.status_code == (200 if recovers else 503)
    assert manager.generate.call_count == 2


@pytest.mark.parametrize("fenced", [False, True])
def test_reviewed_patch_read_apply_and_conflict(coding_client, tmp_path, monkeypatch, fenced):
    client, manager, app = coding_client
    source = tmp_path / "add.py"
    source.write_text("def add(a, b): return a - b\n", encoding="utf-8")
    monkeypatch.setattr("app.coding.api._project_root", lambda project_id: tmp_path)
    monkeypatch.setattr("app.coding.api._authorized_project", AsyncMock())
    record = SimpleNamespace(size_bytes=source.stat().st_size)
    monkeypatch.setattr("app.coding.api._indexed_file", AsyncMock(return_value=record))
    session = AsyncMock()
    session.scalars.return_value = SimpleNamespace(all=lambda: [])
    app.dependency_overrides[get_db_session] = lambda: session
    payload = '{"summary":"Correct addition","content":"def add(a, b): return a + b\\n"}'
    manager.generate.return_value.content = f"```json\n{payload}\n```" if fenced else payload
    result = client.post("/api/v1/coding/projects/project/assist", json={
        "mode": "patch", "prompt": "Fix addition", "path": "add.py", "model": "gemini-test",
    })
    assert result.status_code == 200
    proposal = result.json()
    assert "+def add" in proposal["diff"] and "-def add" in proposal["diff"]
    assert "a - b" in source.read_text()  # Proposal alone never writes.
    apply = {"path": proposal["path"], "content": proposal["proposed_content"], "original_sha256": proposal["original_sha256"]}
    assert client.post("/api/v1/coding/projects/project/apply", json=apply).status_code == 200
    assert "a + b" in source.read_text()
    assert client.post("/api/v1/coding/projects/project/apply", json=apply).status_code == 409
