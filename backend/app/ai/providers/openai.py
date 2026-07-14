"""
OpenAI Provider — OpenAI-compatible API models.

Skeleton implementation. No real API calls are made.
Will be integrated with the OpenAI Python SDK in a later milestone.
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


class OpenAIProvider(BaseProvider):
    """Provider for OpenAI-compatible API models.

    Supports OpenAI's official API and any OpenAI-compatible
    endpoints (e.g., Azure OpenAI, Together AI, Groq).

    Supported models (will be expanded in the future):
        - gpt-4o
        - gpt-4o-mini
        - gpt-4-turbo
        - gpt-3.5-turbo
    """

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self._models: List[ModelInfo] = [
            ModelInfo(
                id="gpt-4o",
                name="GPT-4o",
                description="OpenAI's flagship multimodal model",
                max_tokens=16384,
                supports_streaming=True,
                supports_system_prompt=True,
            ),
            ModelInfo(
                id="gpt-4o-mini",
                name="GPT-4o Mini",
                description="Cost-efficient small model",
                max_tokens=16384,
                supports_streaming=True,
                supports_system_prompt=True,
            ),
            ModelInfo(
                id="gpt-4-turbo",
                name="GPT-4 Turbo",
                description="High-capacity model with vision",
                max_tokens=4096,
                supports_streaming=True,
                supports_system_prompt=True,
            ),
            ModelInfo(
                id="gpt-3.5-turbo",
                name="GPT-3.5 Turbo",
                description="Fast and cost-effective model",
                max_tokens=4096,
                supports_streaming=True,
                supports_system_prompt=True,
            ),
        ]

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Placeholder — will call OpenAI Chat Completions API."""
        raise NotImplementedError(
            "OpenAI generate() is not yet implemented. "
            "This will be integrated with the OpenAI Python SDK in a later milestone."
        )

    async def stream(
        self, request: GenerationRequest
    ) -> AsyncGenerator[str, None]:
        """Placeholder — will stream from OpenAI Chat Completions API."""
        raise NotImplementedError(
            "OpenAI stream() is not yet implemented. "
            "This will be integrated with the OpenAI Python SDK in a later milestone."
        )
        if False:
            yield ""  # pragma: no cover

    async def health_check(self) -> HealthStatus:
        """Placeholder health check — checks if API key is configured."""
        start = time.monotonic()
        has_api_key = bool(self._config.api_key)
        elapsed = (time.monotonic() - start) * 1000
        return HealthStatus(
            available=has_api_key,
            provider=self._name,
            latency_ms=round(elapsed, 2),
            models_available=len(self._models),
            error=None if has_api_key else "No API key configured",
        )

    async def list_models(self) -> List[ModelInfo]:
        """Return the list of supported OpenAI-compatible models."""
        return self._models