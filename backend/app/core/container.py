"""
Dependency Injection Container.

Provides a simple, type-safe DI container for managing application dependencies.
Promotes loose coupling and testability by resolving dependencies at runtime.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional, Type, TypeVar

from app.core.config import Settings, get_settings
from app.core.logger import get_logger

T = TypeVar("T")

logger = get_logger("app.core.container")


class Container:
    """Simple Dependency Injection container.

    Usage:
        container = Container()
        container.register(MyService, MyServiceImpl())
        my_service = container.resolve(MyService)
    """

    def __init__(self):
        self._registry: Dict[str, Any] = {}
        self._singletons: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}

    def register(self, interface: Type[T], implementation: T) -> None:
        """Register a concrete implementation for an interface."""
        key = self._get_key(interface)
        self._registry[key] = implementation

    def register_singleton(self, interface: Type[T], implementation: T) -> None:
        """Register a singleton instance."""
        key = self._get_key(interface)
        self._singletons[key] = implementation

    def register_factory(self, interface: Type[T], factory: Callable[..., T]) -> None:
        """Register a factory function that creates instances."""
        key = self._get_key(interface)
        self._factories[key] = factory

    def resolve(self, interface: Type[T], **kwargs) -> T:
        """Resolve an instance for the given interface."""
        key = self._get_key(interface)

        # Check singletons first
        if key in self._singletons:
            return self._singletons[key]

        # Check factories
        if key in self._factories:
            instance = self._factories[key](**kwargs)
            return instance

        # Check registry
        if key in self._registry:
            return self._registry[key]

        raise KeyError(f"No implementation registered for {interface.__name__}")

    def has(self, interface: Type[T]) -> bool:
        """Check if an implementation is registered."""
        key = self._get_key(interface)
        return key in self._registry or key in self._singletons or key in self._factories

    def clear(self) -> None:
        """Clear all registrations (useful for testing)."""
        self._registry.clear()
        self._singletons.clear()
        self._factories.clear()

    @staticmethod
    def _get_key(interface: Type[T]) -> str:
        return f"{interface.__module__}.{interface.__name__}"


# Global container instance
_container: Optional[Container] = None


def get_container() -> Container:
    """Return the global DI container (create if not yet initialized)."""
    global _container
    if _container is None:
        _container = _create_default_container()
    return _container


def _create_default_container() -> Container:
    """Create and populate the default container with core services."""
    container = Container()

    # Register Settings as singleton
    settings = get_settings()
    container.register_singleton(Settings, settings)

    logger.info("Default DI container created with core services")
    return container