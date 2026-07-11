"""
Workspace API Routes.

FastAPI router for workspace and project management endpoints.
All routes require authentication (implemented via FastAPI dependency).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.workspace.models import Workspace, WorkspaceMember, WorkspaceRole, Project
from app.workspace.service import WorkspaceService

router = APIRouter(prefix="/api/v1/workspaces", tags=["workspaces"])


# Stub auth dependency - will be replaced with real auth in Phase 1
async def get_current_user_id() -> str:
    """Temporary stub for authentication.

    TODO: Replace with actual auth dependency in Phase 1.
    """
    return "system"


def get_workspace_service() -> WorkspaceService:
    return WorkspaceService()


# --------------------------------------------------------------------------- #
# Workspace Endpoints
# --------------------------------------------------------------------------- #


@router.post("", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_workspace(
    body: Dict[str, Any],
    user_id: str = Depends(get_current_user_id),
    service: WorkspaceService = Depends(get_workspace_service),
):
    """Create a new workspace."""
    workspace = await service.create_workspace(
        name=body["name"],
        owner_id=user_id,
        description=body.get("description", ""),
        is_personal=body.get("is_personal", False),
        settings=body.get("settings"),
    )
    return workspace.to_dict()


@router.get("", response_model=Dict[str, Any])
async def list_workspaces(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
    service: WorkspaceService = Depends(get_workspace_service),
):
    """List all workspaces for the current user."""
    workspaces, total = await service.get_user_workspaces(
        user_id=user_id, skip=skip, limit=limit
    )
    return {
        "items": [w.to_dict() for w in workspaces],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/{workspace_id}", response_model=Dict[str, Any])
async def get_workspace(
    workspace_id: str,
    user_id: str = Depends(get_current_user_id),
    service: WorkspaceService = Depends(get_workspace_service),
):
    """Get a workspace by ID."""
    workspace = await service.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return workspace.to_dict()


@router.patch("/{workspace_id}", response_model=Dict[str, Any])
async def update_workspace(
    workspace_id: str,
    body: Dict[str, Any],
    user_id: str = Depends(get_current_user_id),
    service: WorkspaceService = Depends(get_workspace_service),
):
    """Update a workspace."""
    workspace = await service.update_workspace(
        workspace_id=workspace_id, data=body, user_id=user_id
    )
    if not workspace:
        raise HTTPException(
            status_code=403, detail="Not authorized to update this workspace"
        )
    return workspace.to_dict()


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    workspace_id: str,
    user_id: str = Depends(get_current_user_id),
    service: WorkspaceService = Depends(get_workspace_service),
):
    """Delete a workspace."""
    deleted = await service.delete_workspace(workspace_id=workspace_id, user_id=user_id)
    if not deleted:
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this workspace"
        )


# --------------------------------------------------------------------------- #
# Member Endpoints
# --------------------------------------------------------------------------- #


@router.post("/{workspace_id}/members", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def add_member(
    workspace_id: str,
    body: Dict[str, Any],
    user_id: str = Depends(get_current_user_id),
    service: WorkspaceService = Depends(get_workspace_service),
):
    """Add a member to a workspace."""
    member = await service.add_member(
        workspace_id=workspace_id,
        user_id=body["user_id"],
        role=WorkspaceRole(body.get("role", "viewer")),
        added_by=user_id,
    )
    if not member:
        raise HTTPException(
            status_code=403, detail="Not authorized or member already exists"
        )
    return member.to_dict()


@router.get("/{workspace_id}/members", response_model=List[Dict[str, Any]])
async def list_members(
    workspace_id: str,
    user_id: str = Depends(get_current_user_id),
    service: WorkspaceService = Depends(get_workspace_service),
):
    """List all members of a workspace."""
    members = await service.get_members(
        workspace_id=workspace_id, user_id=user_id
    )
    if members is None:
        raise HTTPException(
            status_code=403, detail="Not authorized to view members"
        )
    return [m.to_dict() for m in members]


@router.delete("/{workspace_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    workspace_id: str,
    member_id: str,
    user_id: str = Depends(get_current_user_id),
    service: WorkspaceService = Depends(get_workspace_service),
):
    """Remove a member from a workspace."""
    removed = await service.remove_member(
        workspace_id=workspace_id, user_id=member_id, removed_by=user_id
    )
    if not removed:
        raise HTTPException(
            status_code=403, detail="Not authorized or member not found"
        )


# --------------------------------------------------------------------------- #
# Project Endpoints
# --------------------------------------------------------------------------- #


@router.post("/{workspace_id}/projects", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_project(
    workspace_id: str,
    body: Dict[str, Any],
    user_id: str = Depends(get_current_user_id),
    service: WorkspaceService = Depends(get_workspace_service),
):
    """Create a project within a workspace."""
    project = await service.create_project(
        workspace_id=workspace_id,
        name=body["name"],
        user_id=user_id,
        description=body.get("description", ""),
        project_type=body.get("project_type", "general"),
    )
    if not project:
        raise HTTPException(
            status_code=403, detail="Not authorized to create projects in this workspace"
        )
    return project.to_dict()


@router.get("/{workspace_id}/projects", response_model=Dict[str, Any])
async def list_projects(
    workspace_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
    service: WorkspaceService = Depends(get_workspace_service),
):
    """List all projects in a workspace."""
    result = await service.get_workspace_projects(
        workspace_id=workspace_id, user_id=user_id, skip=skip, limit=limit
    )
    if result is None:
        raise HTTPException(
            status_code=403, detail="Not authorized to view projects"
        )
    projects, total = result
    return {
        "items": [p.to_dict() for p in projects],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/projects/{project_id}", response_model=Dict[str, Any])
async def get_project(
    project_id: str,
    user_id: str = Depends(get_current_user_id),
    service: WorkspaceService = Depends(get_workspace_service),
):
    """Get a project by ID."""
    project = await service.get_project(project_id=project_id, user_id=user_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project.to_dict()


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    user_id: str = Depends(get_current_user_id),
    service: WorkspaceService = Depends(get_workspace_service),
):
    """Delete a project."""
    deleted = await service.delete_project(project_id=project_id, user_id=user_id)
    if not deleted:
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this project"
        )