"""
Ollama Provider — Local models via Ollama.

Skeleton implementation. No real API calls are made.
Will be integrated with Ollama's HTTP API in a later milestone.
"""

from __future__ import annotations

import time
from typing import AsyncGenerator, List

from app.ai.base import (
    BaseProvider,
    GenerationRequest,
    GenerationResponse,
    HealthStatus,
    ModelInfo,
    ProviderConfig,
)


class OllamaProvider(BaseProvider):
    """Provider for locally-hosted Ollama models.

    Supported models (will be expanded in the future):
        - llama3.1
        - mistral
        - codellama
        - phi3
    """

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self._models: List[ModelInfo] = [
            ModelInfo(
                id="llama3.1",
                name="Llama 3.1",
                description="Meta's latest open model (8B)",
                max_tokens=8192,
                supports_streaming=True,
                supports_system_prompt=True,
            ),
            ModelInfo(
                id="mistral",
                name="Mistral",
                description="Mistral AI's open model (7B)",
                max_tokens=8192,
                supports_streaming=True,
                supports_system_prompt=True,
            ),
            ModelInfo(
                id="codellama",
                name="Code Llama",
                description="Code-specialized Llama variant",
                max_tokens=8192,
                supports_streaming=True,
                supports_system_prompt=True,
            ),
            ModelInfo(
                id="phi3",
                name="Phi-3",
                description="Microsoft's small language model",
                max_tokens=4096,
                supports_streaming=True,
                supports_system_prompt=False,
            ),
        ]

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Placeholder — will call Ollama /api/generate."""
        raise NotImplementedError(
            "Ollama generate() is not yet implemented. "
            "This will be integrated with the Ollama HTTP API in a later milestone."
        )

    async def stream(
        self, request: GenerationRequest
    ) -> AsyncGenerator[str, None]:
        """Placeholder — will stream from Ollama /api/generate."""
        raise NotImplementedError(
            "Ollama stream() is not yet implemented. "
            "This will be integrated with the Ollama HTTP API in a later milestone."
        )
        if False:
            yield ""  # pragma: no cover

    async def health_check(self) -> HealthStatus:
        """Placeholder health check — checks if Ollama endpoint is reachable."""
        start = time.monotonic()
        # Simulate connectivity check (will ping base_url in the future)
        has_base_url = bool(self._config.base_url)
        elapsed = (time.monotonic() - start) * 1000
        return HealthStatus(
            available=has_base_url,
            provider=self._name,
            latency_ms=round(elapsed, 2),
            models_available=len(self._models),
            error=None if has_base_url else "No base URL configured",
        )

    async def list_models(self) -> List[ModelInfo]:
        """Return the list of supported Ollama models."""
        return self._models