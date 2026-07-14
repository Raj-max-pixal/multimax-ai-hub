"""
Provider Registry for AI Model Providers.

Manages registration and discovery of AI providers. Providers register
themselves with a unique name, and the registry handles lifecycle,
configuration, and lookup.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Type

from app.ai.base import BaseProvider, ProviderConfig
from app.ai.exceptions import (
    InvalidModelError,
    ProviderConfigurationError,
    ProviderUnavailableError,
)
from app.core.logger import get_logger

logger = get_logger("app.ai.provider_registry")


class ProviderRegistry:
    """Registry for AI providers.

    Providers are registered by name and can be looked up at runtime.
    The registry also manages provider configuration and lifecycle.
    """

    def __init__(self) -> None:
        self._providers: Dict[str, BaseProvider] = {}
        self._configs: Dict[str, ProviderConfig] = {}
        self._default_provider: Optional[str] = None

    # ------------------------------------------------------------------ #
    # Registration
    # ------------------------------------------------------------------ #

    def register(
        self,
        name: str,
        provider: BaseProvider,
        make_default: bool = False,
    ) -> None:
        """Register a provider instance.

        Args:
            name: Unique name for this provider (e.g. 'gemini', 'ollama').
            provider: Initialized provider instance.
            make_default: If True, set this as the default provider.

        Raises:
            ValueError: If a provider with the same name is already registered.
        """
        if name in self._providers:
            raise ValueError(f"Provider '{name}' is already registered")

        self._providers[name] = provider
        self._configs[name] = provider.config
        logger.info(f"Registered provider: {name}")

        if make_default or self._default_provider is None:
            self._default_provider = name
            logger.info(f"Default provider set to: {name}")

    def unregister(self, name: str) -> None:
        """Unregister a provider by name.

        Args:
            name: Name of the provider to unregister.

        Raises:
            KeyError: If the provider is not found.
        """
        if name not in self._providers:
            raise KeyError(f"Provider '{name}' is not registered")

        del self._providers[name]
        del self._configs[name]
        logger.info(f"Unregistered provider: {name}")

        if self._default_provider == name:
            self._default_provider = next(iter(self._providers)) if self._providers else None

    # ------------------------------------------------------------------ #
    # Lookup
    # ------------------------------------------------------------------ #

    def get_provider(self, name: Optional[str] = None) -> BaseProvider:
        """Get a provider by name, or return the default provider.

        Args:
            name: Provider name. If None, returns the default provider.

        Returns:
            The requested provider instance.

        Raises:
            ProviderUnavailableError: If no providers are registered.
            KeyError: If the named provider does not exist.
        """
        if not self._providers:
            raise ProviderUnavailableError(
                provider_name="none",
                message="No AI providers are registered",
            )

        provider_name = name or self._default_provider
        if provider_name is None:
            raise ProviderUnavailableError(
                provider_name="unknown",
                message="No default provider is set and no provider name was specified",
            )

        if provider_name not in self._providers:
            raise KeyError(
                f"Provider '{provider_name}' is not registered. "
                f"Available providers: {list(self._providers.keys())}"
            )

        return self._providers[provider_name]

    def get_config(self, name: Optional[str] = None) -> ProviderConfig:
        """Get the configuration for a provider.

        Args:
            name: Provider name. If None, returns default provider config.

        Returns:
            ProviderConfig for the requested provider.
        """
        provider = self.get_provider(name)
        return provider.config

    def has_provider(self, name: str) -> bool:
        """Check if a provider is registered."""
        return name in self._providers

    # ------------------------------------------------------------------ #
    # Properties
    # ------------------------------------------------------------------ #

    @property
    def provider_names(self) -> List[str]:
        """Get list of all registered provider names."""
        return list(self._providers.keys())

    @property
    def default_provider(self) -> Optional[str]:
        """Get the default provider name."""
        return self._default_provider

    @default_provider.setter
    def default_provider(self, name: str) -> None:
        """Set the default provider."""
        if name not in self._providers:
            raise KeyError(
                f"Cannot set default: provider '{name}' is not registered. "
                f"Available: {list(self._providers.keys())}"
            )
        self._default_provider = name

    @property
    def provider_count(self) -> int:
        """Get the number of registered providers."""
        return len(self._providers)

    def __repr__(self) -> str:
        return (
            f"ProviderRegistry(providers={list(self._providers.keys())}, "
            f"default={self._default_provider})"
        )