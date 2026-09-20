import json

import httpx
import pytest

from app.ai.base import GenerationRequest, ProviderConfig
from app.ai.providers.gemini import GeminiProvider


def make_provider(handler: httpx.MockTransport) -> GeminiProvider:
    provider = GeminiProvider(
        ProviderConfig(
            name="gemini",
            api_key="test-key",
            default_model="gemini-3.6-flash",
        )
    )
    provider._http_client = httpx.AsyncClient(
        base_url=GeminiProvider.DEFAULT_BASE_URL,
        transport=handler,
        headers={"x-goog-api-key": "test-key"},
    )
    return provider


def test_payload_filters_empty_messages_and_maps_roles() -> None:
    provider = GeminiProvider(ProviderConfig(name="gemini", api_key="test-key"))
    payload = provider._payload(
        GenerationRequest(
            model="gemini-3.6-flash",
            messages=[
                {"role": "system", "content": " Be concise. "},
                {"role": "user", "content": "   "},
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi"},
            ],
        )
    )

    assert payload["systemInstruction"]["parts"][0]["text"] == "Be concise."
    assert payload["contents"] == [
        {"role": "user", "parts": [{"text": "Hello"}]},
        {"role": "model", "parts": [{"text": "Hi"}]},
    ]


@pytest.mark.asyncio
async def test_generate_maps_response_and_usage() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["x-goog-api-key"] == "test-key"
        assert request.url.path.endswith("/models/gemini-3.6-flash:generateContent")
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {
                        "content": {"parts": [{"text": "Hello from Gemini"}]},
                        "finishReason": "STOP",
                    }
                ],
                "usageMetadata": {
                    "promptTokenCount": 3,
                    "candidatesTokenCount": 4,
                    "totalTokenCount": 7,
                },
            },
        )

    provider = make_provider(httpx.MockTransport(handler))
    response = await provider.generate(
        GenerationRequest(
            model="gemini-3.6-flash",
            messages=[{"role": "user", "content": "Hello"}],
        )
    )
    await provider.close()

    assert response.content == "Hello from Gemini"
    assert response.provider == "gemini"
    assert response.tokens_total == 7


@pytest.mark.asyncio
async def test_stream_emits_text_chunks() -> None:
    async def handler(_: httpx.Request) -> httpx.Response:
        chunks = [
            {"candidates": [{"content": {"parts": [{"text": "Hello "}]}}]},
            {"candidates": [{"content": {"parts": [{"text": "world"}]}}]},
        ]
        body = "".join(f"data: {json.dumps(chunk)}\n\n" for chunk in chunks)
        return httpx.Response(200, text=body)

    provider = make_provider(httpx.MockTransport(handler))
    request = GenerationRequest(
        model="gemini-3.6-flash",
        messages=[{"role": "user", "content": "Hello"}],
    )
    tokens = [token async for token in provider.stream(request)]
    await provider.close()

    assert tokens == ["Hello ", "world"]
