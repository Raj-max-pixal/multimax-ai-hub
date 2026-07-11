"""
Workspace Engine Module.

Manages user workspaces, projects, and file storage.
Each workspace is an isolated environment with its own
settings, memory, and configuration.
"""

from app.workspace.models import (
    Workspace,
    WorkspaceMember,
    WorkspaceSettings,
    Project,
    ProjectFile,
    WorkspaceRole,
)
from app.workspace.service import WorkspaceService
from app.workspace.api import router

module_info = {
    "name": "workspace",
    "package": "app.workspace",
    "description": "Workspace and project management",
    "version": "0.1.0",
    "dependencies": ["core"],
    "enabled": True,
}

__all__ = [
    "Workspace",
    "WorkspaceMember",
    "WorkspaceSettings",
    "Project",
    "ProjectFile",
    "WorkspaceRole",
    "WorkspaceService",
    "router",
    "module_info",
]