"""
Workspace Service.

Business logic for workspace and project management.
Handles CRUD operations, membership, and file management.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.core.database import get_database
from app.workspace.models import Workspace, WorkspaceMember, WorkspaceRole, Project, ProjectFile

logger = get_logger("app.workspace.service")


class WorkspaceService:
    """Service for workspace management operations."""

    def __init__(self):
        self._db = get_database()

    async def create_workspace(
        self,
        name: str,
        owner_id: str,
        description: str = "",
        is_personal: bool = False,
        settings: Optional[Dict[str, Any]] = None,
    ) -> Workspace:
        """Create a new workspace for a user."""
        async with self._db.session() as session:
            workspace = Workspace(
                id=str(uuid4()),
                name=name,
                description=description,
                owner_id=owner_id,
                is_personal=is_personal,
                settings=settings or {},
            )
            session.add(workspace)
            await session.flush()

            # Add owner as a member
            member = WorkspaceMember(
                id=str(uuid4()),
                workspace_id=workspace.id,
                user_id=owner_id,
                role=WorkspaceRole.OWNER,
            )
            session.add(member)

            logger.info(f"Workspace created: {workspace.id} (owner: {owner_id})")
            return workspace

    async def get_workspace(self, workspace_id: str) -> Optional[Workspace]:
        """Get a workspace by ID."""
        async with self._db.session() as session:
            result = await session.execute(
                select(Workspace).where(Workspace.id == workspace_id)
            )
            return result.scalar_one_or_none()

    async def get_user_workspaces(
        self, user_id: str, skip: int = 0, limit: int = 50
    ) -> tuple[List[Workspace], int]:
        """Get all workspaces a user belongs to."""
        async with self._db.session() as session:
            # Subquery: workspace IDs where user is a member
            member_subq = (
                select(WorkspaceMember.workspace_id)
                .where(WorkspaceMember.user_id == user_id)
                .subquery()
            )

            query = (
                select(Workspace)
                .where(Workspace.id.in_(select(member_subq.c.workspace_id)))
                .offset(skip)
                .limit(limit)
                .order_by(Workspace.updated_at.desc())
            )
            count_query = (
                select(func.count())
                .select_from(Workspace)
                .where(Workspace.id.in_(select(member_subq.c.workspace_id)))
            )

            result = await session.execute(query)
            workspaces = list(result.scalars().all())

            count_result = await session.execute(count_query)
            total = count_result.scalar() or 0

            return workspaces, total

    async def update_workspace(
        self, workspace_id: str, data: Dict[str, Any], user_id: str
    ) -> Optional[Workspace]:
        """Update a workspace. Only owner/admin can update."""
        async with self._db.session() as session:
            workspace = await self._get_workspace_with_permission(
                session, workspace_id, user_id, [WorkspaceRole.OWNER, WorkspaceRole.ADMIN]
            )
            if not workspace:
                return None

            for key, value in data.items():
                if hasattr(workspace, key) and key not in ("id", "owner_id", "created_at"):
                    setattr(workspace, key, value)

            session.add(workspace)
            return workspace

    async def delete_workspace(self, workspace_id: str, user_id: str) -> bool:
        """Delete a workspace. Only owner can delete."""
        async with self._db.session() as session:
            workspace = await self._get_workspace_with_permission(
                session, workspace_id, user_id, [WorkspaceRole.OWNER]
            )
            if not workspace:
                return False

            await session.delete(workspace)
            logger.info(f"Workspace deleted: {workspace_id}")
            return True

    async def add_member(
        self, workspace_id: str, user_id: str, role: WorkspaceRole, added_by: str
    ) -> Optional[WorkspaceMember]:
        """Add a member to a workspace."""
        async with self._db.session() as session:
            # Only owner/admin can add members
            workspace = await self._get_workspace_with_permission(
                session, workspace_id, added_by, [WorkspaceRole.OWNER, WorkspaceRole.ADMIN]
            )
            if not workspace:
                return None

            # Check if already a member
            existing = await session.execute(
                select(WorkspaceMember).where(
                    WorkspaceMember.workspace_id == workspace_id,
                    WorkspaceMember.user_id == user_id,
                )
            )
            if existing.scalar_one_or_none():
                logger.warning(f"User {user_id} is already a member of workspace {workspace_id}")
                return None

            member = WorkspaceMember(
                id=str(uuid4()),
                workspace_id=workspace_id,
                user_id=user_id,
                role=role,
            )
            session.add(member)
            return member

    async def remove_member(
        self, workspace_id: str, user_id: str, removed_by: str
    ) -> bool:
        """Remove a member from a workspace."""
        async with self._db.session() as session:
            workspace = await self._get_workspace_with_permission(
                session, workspace_id, removed_by, [WorkspaceRole.OWNER, WorkspaceRole.ADMIN]
            )
            if not workspace:
                return False

            result = await session.execute(
                delete(WorkspaceMember).where(
                    WorkspaceMember.workspace_id == workspace_id,
                    WorkspaceMember.user_id == user_id,
                )
            )
            return result.rowcount > 0

    async def get_members(
        self, workspace_id: str, user_id: str
    ) -> Optional[List[WorkspaceMember]]:
        """Get all members of a workspace."""
        async with self._db.session() as session:
            # Must be a member to view members
            membership = await self._check_membership(session, workspace_id, user_id)
            if not membership:
                return None

            result = await session.execute(
                select(WorkspaceMember).where(
                    WorkspaceMember.workspace_id == workspace_id
                )
            )
            return list(result.scalars().all())

    # ------------------------------------------------------------------ #
    # Project Operations
    # ------------------------------------------------------------------ #

    async def create_project(
        self,
        workspace_id: str,
        name: str,
        user_id: str,
        description: str = "",
        project_type: str = "general",
    ) -> Optional[Project]:
        """Create a new project within a workspace."""
        async with self._db.session() as session:
            membership = await self._check_membership(
                session, workspace_id, user_id, [WorkspaceRole.OWNER, WorkspaceRole.ADMIN, WorkspaceRole.EDITOR]
            )
            if not membership:
                return None

            project = Project(
                id=str(uuid4()),
                workspace_id=workspace_id,
                name=name,
                description=description,
                project_type=project_type,
            )
            session.add(project)
            return project

    async def get_project(self, project_id: str, user_id: str) -> Optional[Project]:
        """Get a project by ID."""
        async with self._db.session() as session:
            result = await session.execute(
                select(Project).where(Project.id == project_id)
            )
            project = result.scalar_one_or_none()
            if not project:
                return None

            membership = await self._check_membership(session, project.workspace_id, user_id)
            if not membership:
                return None

            return project

    async def get_workspace_projects(
        self, workspace_id: str, user_id: str, skip: int = 0, limit: int = 50
    ) -> Optional[tuple[List[Project], int]]:
        """Get all projects in a workspace."""
        async with self._db.session() as session:
            membership = await self._check_membership(session, workspace_id, user_id)
            if not membership:
                return None

            query = (
                select(Project)
                .where(Project.workspace_id == workspace_id)
                .offset(skip)
                .limit(limit)
                .order_by(Project.updated_at.desc())
            )
            count_query = (
                select(func.count())
                .select_from(Project)
                .where(Project.workspace_id == workspace_id)
            )

            result = await session.execute(query)
            projects = list(result.scalars().all())

            count_result = await session.execute(count_query)
            total = count_result.scalar() or 0

            return projects, total

    async def delete_project(self, project_id: str, user_id: str) -> bool:
        """Delete a project."""
        async with self._db.session() as session:
            result = await session.execute(
                select(Project).where(Project.id == project_id)
            )
            project = result.scalar_one_or_none()
            if not project:
                return False

            membership = await self._check_membership(
                session, project.workspace_id, user_id, [WorkspaceRole.OWNER, WorkspaceRole.ADMIN]
            )
            if not membership:
                return False

            await session.delete(project)
            return True

    # ------------------------------------------------------------------ #
    # Internal Helpers
    # ------------------------------------------------------------------ #

    async def _check_membership(
        self,
        session: AsyncSession,
        workspace_id: str,
        user_id: str,
        allowed_roles: Optional[List[WorkspaceRole]] = None,
    ) -> Optional[WorkspaceMember]:
        """Check if a user is a member of a workspace."""
        query = select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
        )
        if allowed_roles:
            query = query.where(WorkspaceMember.role.in_(allowed_roles))

        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def _get_workspace_with_permission(
        self,
        session: AsyncSession,
        workspace_id: str,
        user_id: str,
        allowed_roles: List[WorkspaceRole],
    ) -> Optional[Workspace]:
        """Get a workspace and verify user permissions."""
        result = await session.execute(
            select(Workspace).where(Workspace.id == workspace_id)
        )
        workspace = result.scalar_one_or_none()
        if not workspace:
            return None

        membership = await self._check_membership(session, workspace_id, user_id, allowed_roles)
        if not membership:
            return None

        return workspace