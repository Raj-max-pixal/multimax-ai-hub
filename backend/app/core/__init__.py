"""
Core Platform Package.

This package provides the foundational infrastructure for the Multimax AI Hub.
All domain modules depend on this package, but this package has zero
domain-level dependencies.

Components:
    - Config: Environment-aware configuration management
    - Container: Dependency Injection container
    - Logger: Structured logging with JSON support
    - Events: Persistent Event Bus with retry + dead letter queue
    - ModuleLoader: Dynamic module discovery and loading
    - Database: Async SQLAlchemy session management
    - Exceptions: Base exception classes
"""

from app.core.config import Settings, get_settings
from app.core.container import Container, get_container
from app.core.logger import get_logger, setup_logging
from app.core.events import (
    EventBus,
    Event,
    EventHandler,
    InMemoryEventBus,
    PostgresEventBus,
)
from app.core.database import (
    DatabaseManager,
    get_db_session,
    Base,
)
from app.core.exceptions import (
    MultimaxError,
    NotFoundError,
    ConfigurationError,
    AuthenticationError,
    AuthorizationError,
    ValidationError,
    DuplicateError,
    ExternalServiceError,
    RateLimitError,
)
from app.core.module_loader import ModuleLoader
from app.core.plugin_manager import PluginManager, PluginInterface

__all__ = [
    # Config
    "Settings",
    "get_settings",
    # Container
    "Container",
    "get_container",
    # Logger
    "get_logger",
    "setup_logging",
    # Events
    "EventBus",
    "Event",
    "EventHandler",
    "InMemoryEventBus",
    "PostgresEventBus",
    # Database
    "DatabaseManager",
    "get_db_session",
    "Base",
    # Exceptions
    "MultimaxError",
    "NotFoundError",
    "ConfigurationError",
    "AuthenticationError",
    "AuthorizationError",
    "ValidationError",
    "DuplicateError",
    "ExternalServiceError",
    "RateLimitError",
    # Plugins & Modules
    "ModuleLoader",
    "PluginManager",
    "PluginInterface",
]