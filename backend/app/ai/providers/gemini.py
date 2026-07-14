"""
Gemini Provider — Google Gemini AI models.

Skeleton implementation. No real API calls are made.
Will be integrated with google-generativeai SDK in a later milestone.
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


class GeminiProvider(BaseProvider):
    """Provider for Google Gemini models.

    Supported models (will be expanded in the future):
        - gemini-2.0-flash
        - gemini-2.0-pro
        - gemini-1.5-flash
        - gemini-1.5-pro
    """

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self._models: List[ModelInfo] = [
            ModelInfo(
                id="gemini-2.0-flash",
                name="Gemini 2.0 Flash",
                description="Fast and versatile multimodal model",
                max_tokens=8192,
                supports_streaming=True,
                supports_system_prompt=True,
            ),
            ModelInfo(
                id="gemini-2.0-pro",
                name="Gemini 2.0 Pro",
                description="Best performing multimodal model",
                max_tokens=8192,
                supports_streaming=True,
                supports_system_prompt=True,
            ),
            ModelInfo(
                id="gemini-1.5-flash",
                name="Gemini 1.5 Flash",
                description="Fast and versatile performance",
                max_tokens=8192,
                supports_streaming=True,
                supports_system_prompt=True,
            ),
            ModelInfo(
                id="gemini-1.5-pro",
                name="Gemini 1.5 Pro",
                description="Best performing mid-size model",
                max_tokens=8192,
                supports_streaming=True,
                supports_system_prompt=True,
            ),
        ]

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Placeholder — will call Google Generative AI SDK."""
        raise NotImplementedError(
            "Gemini generate() is not yet implemented. "
            "This will be integrated with google-generativeai SDK in a later milestone."
        )

    async def stream(
        self, request: GenerationRequest
    ) -> AsyncGenerator[str, None]:
        """Placeholder — will stream tokens from Google Generative AI SDK."""
        raise NotImplementedError(
            "Gemini stream() is not yet implemented. "
            "This will be integrated with google-generativeai SDK in a later milestone."
        )
        if False:
            yield ""  # pragma: no cover

    async def health_check(self) -> HealthStatus:
        """Placeholder health check — returns healthy if API key is configured."""
        start = time.monotonic()
        # Simulate a lightweight connectivity check
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
        """Return the list of supported Gemini models."""
        return self._models