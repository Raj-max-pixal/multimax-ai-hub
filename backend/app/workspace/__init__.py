"""
Workspace Engine Module.

Manages user workspaces, projects, and file storage.
Each workspace is an isolated environment with its own
settings, memory, and configuration.
"""

from __future__ import annotations

from typing import Any

from app.core.module_loader import ModuleInfo
from app.workspace.models import (
    Workspace,
    WorkspaceMember,
    Project,
    ProjectFile,
    WorkspaceRole,
)
from app.workspace.service import WorkspaceService
from app.workspace.api import router

module_info = ModuleInfo(
    name="workspace",
    package="app.workspace",
    description="Workspace and project management",
    version="0.1.0",
    dependencies=["core"],
    enabled=True,
)


def register(app: Any, container: Any) -> None:
    """Register the workspace module with the FastAPI application.

    Called by the ModuleLoader during application startup.
    """
    # Include the workspace API router
    app.include_router(router)

    # Register workspace service in the DI container
    from app.workspace.service import WorkspaceService
    container.register_singleton(WorkspaceService, WorkspaceService())


__all__ = [
    "Workspace",
    "WorkspaceMember",
    "Project",
    "ProjectFile",
    "WorkspaceRole",
    "WorkspaceService",
    "router",
    "module_info",
    "register",
]
