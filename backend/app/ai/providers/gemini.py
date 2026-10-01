"""Google Gemini provider implemented with the Gemini REST API."""

from __future__ import annotations

import json
import time
from typing import Any, AsyncGenerator, Dict, List, Optional

import httpx

from app.ai.base import (
    BaseProvider,
    GenerationRequest,
    GenerationResponse,
    HealthStatus,
    ModelInfo,
    ProviderConfig,
)
from app.ai.exceptions import (
    InvalidApiKeyError,
    InvalidModelError,
    ProviderUnavailableError,
    RateLimitError,
)


class GeminiProvider(BaseProvider):
    """Provider for Google Gemini text-generation models."""

    DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self._base_url = (config.base_url or self.DEFAULT_BASE_URL).rstrip("/")
        self._http_client: Optional[httpx.AsyncClient] = None
        self._models = [
            ModelInfo(
                id="gemini-3.6-flash",
                name="Gemini 3.6 Flash",
                description="Fast, high-quality model for chat and agent workloads",
                max_tokens=65536,
            ),
            ModelInfo(
                id="gemini-3.5-flash-lite",
                name="Gemini 3.5 Flash-Lite",
                description="Low-latency, cost-efficient Gemini model",
                max_tokens=65536,
            ),
            ModelInfo(
                id="gemini-3.1-pro-preview",
                name="Gemini 3.1 Pro Preview",
                description="Advanced reasoning model for complex tasks",
                max_tokens=65536,
            ),
        ]

    def _get_client(self) -> httpx.AsyncClient:
        if self._http_client is None or self._http_client.is_closed:
            key = (self._config.api_key or "").strip()
            if not key:
                raise InvalidApiKeyError(provider_name=self._name)
            self._http_client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=httpx.Timeout(self._config.timeout or 60.0),
                headers={"x-goog-api-key": key},
            )
        return self._http_client

    @staticmethod
    def _model_name(model: str) -> str:
        return model.removeprefix("models/").strip().removesuffix(":latest")

    @staticmethod
    def _text(result: Dict[str, Any]) -> str:
        return "".join(
            part.get("text", "")
            for candidate in result.get("candidates", [])
            for part in candidate.get("content", {}).get("parts", [])
        )

    def _payload(self, request: GenerationRequest) -> Dict[str, Any]:
        contents: List[Dict[str, Any]] = []
        system: List[str] = []
        if request.system_prompt and request.system_prompt.strip():
            system.append(request.system_prompt.strip())

        for message in request.messages:
            content = str(message.get("content", "")).strip()
            if not content:
                continue
            role = str(message.get("role", "user")).lower()
            if role == "system":
                system.append(content)
            else:
                contents.append(
                    {
                        "role": "model" if role == "assistant" else "user",
                        "parts": [{"text": content}],
                    }
                )

        if not contents:
            raise ProviderUnavailableError(
                provider_name=self._name,
                message="Gemini request contains no non-empty chat messages",
            )

        generation: Dict[str, Any] = {
            "temperature": request.temperature,
            "topP": request.top_p,
            "topK": request.top_k,
        }
        if request.max_tokens:
            generation["maxOutputTokens"] = request.max_tokens
        if request.stop_sequences:
            generation["stopSequences"] = request.stop_sequences

        payload: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": generation,
        }
        if system:
            payload["systemInstruction"] = {
                "parts": [{"text": "\n\n".join(system)}]
            }
        return payload

    def _map_http_error(self, error: httpx.HTTPStatusError, model: str) -> None:
        status = error.response.status_code
        if status in (401, 403):
            raise InvalidApiKeyError(
                provider_name=self._name,
                message="Gemini rejected the configured API key",
            ) from error
        if status == 404:
            raise InvalidModelError(model=model, provider_name=self._name) from error
        if status == 429:
            raise RateLimitError(provider_name=self._name) from error
        raise ProviderUnavailableError(
            provider_name=self._name,
            message=f"Gemini API returned HTTP {status}",
        ) from error

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        model = self._model_name(request.model or self._config.default_model)
        start = time.monotonic()
        try:
            response = await self._get_client().post(
                f"/models/{model}:generateContent",
                json=self._payload(request),
            )
            response.raise_for_status()
            result = response.json()
        except httpx.HTTPStatusError as error:
            self._map_http_error(error, model)
            raise
        except httpx.RequestError as error:
            raise ProviderUnavailableError(
                provider_name=self._name,
                message=f"Cannot connect to Gemini: {error}",
            ) from error

        usage = result.get("usageMetadata", {})
        candidates = result.get("candidates", [])
        finish_reason = (
            candidates[0].get("finishReason", "stop").lower()
            if candidates
            else "stop"
        )
        return GenerationResponse(
            content=self._text(result),
            model=model,
            provider=self._name,
            finish_reason=finish_reason,
            tokens_prompt=usage.get("promptTokenCount"),
            tokens_completion=usage.get("candidatesTokenCount"),
            tokens_total=usage.get("totalTokenCount"),
            latency_ms=round((time.monotonic() - start) * 1000, 2),
        )

    async def stream(
        self, request: GenerationRequest
    ) -> AsyncGenerator[str, None]:
        model = self._model_name(request.model or self._config.default_model)
        try:
            async with self._get_client().stream(
                "POST",
                f"/models/{model}:streamGenerateContent",
                params={"alt": "sse"},
                json=self._payload(request),
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    payload = line.removeprefix("data:").strip()
                    if not payload or payload == "[DONE]":
                        continue
                    try:
                        token = self._text(json.loads(payload))
                    except json.JSONDecodeError:
                        continue
                    if token:
                        yield token
        except httpx.HTTPStatusError as error:
            self._map_http_error(error, model)
        except httpx.RequestError as error:
            raise ProviderUnavailableError(
                provider_name=self._name,
                message=f"Cannot connect to Gemini: {error}",
            ) from error

    async def health_check(self) -> HealthStatus:
        start = time.monotonic()
        if not (self._config.api_key or "").strip():
            return HealthStatus(
                available=False,
                provider=self._name,
                error="No API key configured",
            )
        try:
            response = await self._get_client().get("/models", timeout=10.0)
            response.raise_for_status()
            models_available = len(response.json().get("models", []))
            return HealthStatus(
                available=True,
                provider=self._name,
                latency_ms=round((time.monotonic() - start) * 1000, 2),
                models_available=models_available,
            )
        except Exception as error:
            return HealthStatus(
                available=False,
                provider=self._name,
                latency_ms=round((time.monotonic() - start) * 1000, 2),
                error=str(error),
            )

    async def list_models(self) -> List[ModelInfo]:
        return self._models

    async def close(self) -> None:
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
            self._http_client = None
