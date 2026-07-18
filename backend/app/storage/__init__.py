"""
Storage Module — File Storage Management.

Provides file upload/download, metadata management, and quota tracking
for the Multimax AI Hub application. Follows the domain module pattern
for automatic discovery and registration by the ModuleLoader.
"""

from __future__ import annotations

from typing import Any

from app.core.module_loader import ModuleInfo
from app.storage.api import router as storage_router
from app.storage.service import StorageService

module_info = ModuleInfo(
    name="storage",
    package="app.storage",
    description="File upload, download, metadata management, and storage quota tracking",
    version="1.0.0",
    dependencies=["core"],
    enabled=True,
)


def register(app: Any, container: Any) -> None:
    """Register the storage module with the FastAPI application.

    Called by the ModuleLoader during application startup.
    """
    # Include the storage API router
    app.include_router(storage_router)

    # Register storage service as a singleton in the DI container
    container.register_singleton(StorageService, StorageService())


__all__ = [
    "module_info",
    "register",
    "StorageService",
    "storage_router",
]
