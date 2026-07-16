"""
Ollama Provider — Local models via Ollama HTTP API.

Implements real HTTP calls to Ollama's REST API for generate,
stream, health check, and model listing.
"""

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
from app.ai.exceptions import InvalidModelError, ProviderUnavailableError


class OllamaProvider(BaseProvider):
    """Provider for locally-hosted Ollama models.

    Communicates with the Ollama HTTP API at the configured base_url.
    Supports all Ollama models (llama3.1, mistral, codellama, phi3, etc.).
    """

    CHAT_ENDPOINT = "/api/chat"
    TAGS_ENDPOINT = "/api/tags"

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self._base_url = (config.base_url or "http://localhost:11434").rstrip("/")
        self._http_client: Optional[httpx.AsyncClient] = None
        self._models_cache: List[ModelInfo] = []
        self._models_cache_ts: float = 0
        self._cache_ttl: float = 60.0  # seconds

    def _get_client(self) -> httpx.AsyncClient:
        """Get or create the shared HTTP client."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=httpx.Timeout(self._config.timeout or 120.0),
            )
        return self._http_client

    def _build_request_data(self, request: GenerationRequest) -> Dict[str, Any]:
        """Build the JSON payload for Ollama's /api/chat endpoint."""
        messages: List[Dict[str, str]] = []

        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})

        messages.extend(request.messages)

        data: Dict[str, Any] = {
            "model": request.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": request.temperature,
                "top_p": request.top_p,
                "top_k": request.top_k,
            },
        }

        if request.max_tokens:
            data["options"]["num_predict"] = request.max_tokens  # type: ignore[attr-defined]

        if request.stop_sequences:
            data["options"]["stop"] = request.stop_sequences  # type: ignore[attr-defined]

        return data

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Call Ollama /api/chat with a non-streaming request."""
        client = self._get_client()
        data = self._build_request_data(request)
        data["stream"] = False

        start = time.monotonic()

        try:
            response = await client.post(self.CHAT_ENDPOINT, json=data)
            response.raise_for_status()
            result = response.json()
        except httpx.ConnectError as e:
            raise ProviderUnavailableError(
                f"Cannot connect to Ollama at {self._base_url}: {e}"
            )
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise InvalidModelError(f"Model '{request.model}' not found in Ollama")
            raise ProviderUnavailableError(f"Ollama API error: {e}")

        elapsed = (time.monotonic() - start) * 1000

        message = result.get("message", {})
        content = message.get("content", "")

        # Parse token counts from response if available
        tokens_prompt = None
        tokens_completion = None
        if "prompt_eval_count" in result:
            tokens_prompt = result["prompt_eval_count"]
        if "eval_count" in result:
            tokens_completion = result["eval_count"]

        return GenerationResponse(
            content=content,
            model=request.model,
            provider=self._name,
            finish_reason=result.get("done_reason", "stop"),
            tokens_prompt=tokens_prompt,
            tokens_completion=tokens_completion,
            tokens_total=(tokens_prompt or 0) + (tokens_completion or 0)
            if tokens_prompt is not None and tokens_completion is not None
            else None,
            latency_ms=round(elapsed, 2),
        )

    async def stream(
        self, request: GenerationRequest
    ) -> AsyncGenerator[str, None]:
        """Stream tokens from Ollama /api/chat with stream=True.

        Yields individual content tokens as they arrive via SSE.
        """
        client = self._get_client()
        data = self._build_request_data(request)
        data["stream"] = True

        try:
            async with client.stream("POST", self.CHAT_ENDPOINT, json=data) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        chunk = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    if "message" in chunk:
                        msg = chunk["message"]
                        if "content" in msg and msg["content"]:
                            yield msg["content"]

                    # If done, break (though response stream closes naturally)
                    if chunk.get("done", False):
                        break

        except httpx.ConnectError as e:
            raise ProviderUnavailableError(
                f"Cannot connect to Ollama at {self._base_url}: {e}"
            )
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise InvalidModelError(f"Model '{request.model}' not found in Ollama")
            raise ProviderUnavailableError(f"Ollama API error: {e}")

    async def health_check(self) -> HealthStatus:
        """Check if Ollama is reachable and responding."""
        start = time.monotonic()
        client = self._get_client()

        try:
            # Ping the tags endpoint as a lightweight health check
            response = await client.get(self.TAGS_ENDPOINT, timeout=5.0)
            response.raise_for_status()
            tags_data = response.json()
            models_count = len(tags_data.get("models", []))
            elapsed = (time.monotonic() - start) * 1000

            return HealthStatus(
                available=True,
                provider=self._name,
                latency_ms=round(elapsed, 2),
                models_available=models_count,
            )
        except Exception as e:
            elapsed = (time.monotonic() - start) * 1000
            return HealthStatus(
                available=False,
                provider=self._name,
                latency_ms=round(elapsed, 2),
                models_available=0,
                error=str(e),
            )

    async def list_models(self) -> List[ModelInfo]:
        """Fetch available models from Ollama /api/tags.

        Results are cached for self._cache_ttl seconds.
        """
        now = time.monotonic()
        if self._models_cache and (now - self._models_cache_ts) < self._cache_ttl:
            return self._models_cache

        client = self._get_client()

        try:
            response = await client.get(self.TAGS_ENDPOINT, timeout=10.0)
            response.raise_for_status()
            tags_data = response.json()
        except Exception:
            # Fall back to default known models if Ollama is unreachable
            return self._get_default_models()

        models: List[ModelInfo] = []
        for model_entry in tags_data.get("models", []):
            model_name = model_entry.get("name", "unknown")
            # Strip the :latest tag for cleaner IDs
            clean_name = model_name.split(":")[0] if ":" in model_name else model_name
            models.append(
                ModelInfo(
                    id=clean_name,
                    name=model_name,
                    description=f"Ollama model: {model_name}",
                    max_tokens=8192,
                    supports_streaming=True,
                    supports_system_prompt=self._supports_system(clean_name),
                )
            )

        self._models_cache = models
        self._models_cache_ts = now
        return models

    def _get_default_models(self) -> List[ModelInfo]:
        """Return a default set of common Ollama models."""
        return [
            ModelInfo(
                id="llama3.1", name="llama3.1:latest",
                description="Meta's latest open model (8B)",
                max_tokens=8192, supports_streaming=True, supports_system_prompt=True,
            ),
            ModelInfo(
                id="mistral", name="mistral:latest",
                description="Mistral AI's open model (7B)",
                max_tokens=8192, supports_streaming=True, supports_system_prompt=True,
            ),
            ModelInfo(
                id="codellama", name="codellama:latest",
                description="Code-specialized Llama variant",
                max_tokens=8192, supports_streaming=True, supports_system_prompt=True,
            ),
            ModelInfo(
                id="phi3", name="phi3:latest",
                description="Microsoft's small language model",
                max_tokens=4096, supports_streaming=True, supports_system_prompt=False,
            ),
        ]

    @staticmethod
    def _supports_system(model_id: str) -> bool:
        """Determine if a model supports system prompts."""
        known_no_system = {"phi3", "phi-3", "tinyllama"}
        return model_id.lower() not in known_no_system

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
            self._http_client = None