"""
Qwen Provider — Alibaba Qwen models.

Skeleton implementation. No real API calls are made.
Will be integrated with DashScope SDK in a later milestone.
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


class QwenProvider(BaseProvider):
    """Provider for Alibaba Qwen models via DashScope.

    Supported models (will be expanded in the future):
        - qwen-max
        - qwen-plus
        - qwen-turbo
        - qwen2.5-72b-instruct
    """

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self._models: List[ModelInfo] = [
            ModelInfo(
                id="qwen-max",
                name="Qwen-Max",
                description="Alibaba's largest Qwen model",
                max_tokens=8192,
                supports_streaming=True,
                supports_system_prompt=True,
            ),
            ModelInfo(
                id="qwen-plus",
                name="Qwen-Plus",
                description="Balanced performance and cost",
                max_tokens=8192,
                supports_streaming=True,
                supports_system_prompt=True,
            ),
            ModelInfo(
                id="qwen-turbo",
                name="Qwen-Turbo",
                description="Fast and cost-effective",
                max_tokens=8192,
                supports_streaming=True,
                supports_system_prompt=True,
            ),
            ModelInfo(
                id="qwen2.5-72b-instruct",
                name="Qwen2.5 72B Instruct",
                description="Open-weight high-performance model",
                max_tokens=8192,
                supports_streaming=True,
                supports_system_prompt=True,
            ),
        ]

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Placeholder — will call DashScope API for text generation."""
        raise NotImplementedError(
            "Qwen generate() is not yet implemented. "
            "This will be integrated with DashScope SDK in a later milestone."
        )

    async def stream(
        self, request: GenerationRequest
    ) -> AsyncGenerator[str, None]:
        """Placeholder — will stream from DashScope API."""
        raise NotImplementedError(
            "Qwen stream() is not yet implemented. "
            "This will be integrated with DashScope SDK in a later milestone."
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
        """Return the list of supported Qwen models."""
        return self._models