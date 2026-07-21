"""
AI Manager — Facade for all AI operations.

The AI Manager is the single entry point for all AI-related operations.
Application code (services, APIs) communicates only with AIManager.
It delegates to the appropriate provider via the ProviderRegistry.
"""

from __future__ import annotations

from typing import AsyncGenerator, Dict, List, Optional

from app.ai.base import (
    BaseProvider,
    GenerationRequest,
    GenerationResponse,
    HealthStatus,
    ModelInfo,
)
from app.ai.exceptions import (
    InvalidModelError,
    ProviderUnavailableError,
)
from app.ai.provider_registry import ProviderRegistry
from app.core.logger import get_logger

logger = get_logger("app.ai.manager")


class AIManager:
    """Central facade for AI model operations.

    Application code calls AIManager methods; it handles provider
    selection, request routing, and error translation.

    Example:
        manager = container.get_ai_manager()
        response = await manager.generate_text("gemini", "Hello!")
    """

    def __init__(self, registry: Optional[ProviderRegistry] = None) -> None:
        self._registry = registry or ProviderRegistry()

    # ------------------------------------------------------------------ #
    # Properties
    # ------------------------------------------------------------------ #

    @property
    def registry(self) -> ProviderRegistry:
        """Get the underlying provider registry."""
        return self._registry

    # ------------------------------------------------------------------ #
    # Generation
    # ------------------------------------------------------------------ #

    async def generate(
        self,
        request: GenerationRequest,
        provider_name: Optional[str] = None,
    ) -> GenerationResponse:
        """Generate a complete response from a model.

        Args:
            request: Generation parameters.
            provider_name: Optional provider name. Uses default if None.

        Returns:
            The model's response with metadata.

        Raises:
            ProviderUnavailableError: If the provider cannot be reached.
            InvalidModelError: If the model is not supported.
        """
        provider = self._registry.get_provider(provider_name)
        logger.debug(
            f"Generating with provider={provider.name}, model={request.model}"
        )
        return await provider.generate(request)

    async def stream(
        self,
        request: GenerationRequest,
        provider_name: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """Stream a response from a model token by token.

        Args:
            request: Generation parameters.
            provider_name: Optional provider name. Uses default if None.

        Yields:
            Content tokens as they arrive.

        Raises:
            ProviderUnavailableError: If the provider cannot be reached.
            InvalidModelError: If the model is not supported.
        """
        provider = self._registry.get_provider(provider_name)
        logger.debug(
            f"Streaming with provider={provider.name}, model={request.model}"
        )
        async for token in provider.stream(request):
            yield token

    # ------------------------------------------------------------------ #
    # Provider Management
    # ------------------------------------------------------------------ #

    def get_provider(self, name: Optional[str] = None) -> BaseProvider:
        """Get a provider instance by name.

        Args:
            name: Provider name. If None, returns the default provider.

        Returns:
            The requested provider instance.
        """
        return self._registry.get_provider(name)

    def get_provider_names(self) -> List[str]:
        """Get the list of registered provider names."""
        return self._registry.provider_names

    def get_default_provider(self) -> Optional[str]:
        """Get the name of the default provider."""
        return self._registry.default_provider

    def set_default_provider(self, name: str) -> None:
        """Set the default provider by name.

        Args:
            name: Provider name to set as default.
        """
        self._registry.default_provider = name

    # ------------------------------------------------------------------ #
    # Model Discovery
    # ------------------------------------------------------------------ #

    async def list_models(
        self,
        provider_name: Optional[str] = None,
    ) -> List[ModelInfo]:
        """List available models from a provider.

        Args:
            provider_name: Provider to query. If None, queries all providers.

        Returns:
            List of ModelInfo objects.
        """
        if provider_name:
            provider = self._registry.get_provider(provider_name)
            return await provider.list_models()

        # Aggregate models from all providers
        all_models: List[ModelInfo] = []
        for name in self._registry.provider_names:
            try:
                provider = self._registry.get_provider(name)
                models = await provider.list_models()
                all_models.extend(models)
            except Exception as e:
                logger.warning(f"Failed to list models for provider '{name}': {e}")
        return all_models

    async def get_model_info(
        self,
        model_id: str,
        provider_name: Optional[str] = None,
    ) -> Optional[ModelInfo]:
        """Get information about a specific model.

        Args:
            model_id: The model ID to look up.
            provider_name: Optional provider to search. Searches all if None.

        Returns:
            ModelInfo if found, None otherwise.
        """
        models = await self.list_models(provider_name)
        for model in models:
            if model.id == model_id:
                return model
        return None

    # ------------------------------------------------------------------ #
    # Health
    # ------------------------------------------------------------------ #

    async def health_check(
        self,
        provider_name: Optional[str] = None,
    ) -> Dict[str, HealthStatus]:
        """Check health of one or all providers.

        Args:
            provider_name: Optional specific provider to check.
                          If None, checks all registered providers.

        Returns:
            Dict mapping provider names to HealthStatus.
        """
        if provider_name:
            provider = self._registry.get_provider(provider_name)
            return {provider_name: await provider.health_check()}

        results: Dict[str, HealthStatus] = {}
        for name in self._registry.provider_names:
            try:
                provider = self._registry.get_provider(name)
                results[name] = await provider.health_check()
            except Exception as e:
                logger.warning(f"Health check failed for provider '{name}': {e}")
                results[name] = HealthStatus(
                    available=False,
                    provider=name,
                    error=str(e),
                )
        return results


# Alias for backward compatibility — verification scripts look for AIProviderManager
AIProviderManager = AIManager

__all__ = [
    "AIManager",
    "AIProviderManager",
]