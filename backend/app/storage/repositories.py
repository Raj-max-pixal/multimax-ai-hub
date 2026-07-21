"""
Storage Module — Data Access Layer.

Provides CRUD operations for StoredFile and StorageQuota records.
"""

from __future__ import annotations

import math
from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.storage.exceptions import FileNotFoundError_
from app.storage.models import StoredFile, StorageQuota

logger = get_logger("storage.repositories")


class StoredFileRepository:
    """Data access for StoredFile records."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, file_record: StoredFile) -> StoredFile:
        """Persist a new stored file record."""
        self.session.add(file_record)
        await self.session.flush()
        logger.debug(f"Created stored file record {file_record.id}")
        return file_record

    async def get_by_id(self, file_id: str) -> Optional[StoredFile]:
        """Fetch a stored file by its UUID string."""
        result = await self.session.get(StoredFile, file_id)
        return result

    async def get_by_id_or_raise(self, file_id: str) -> StoredFile:
        """Fetch a stored file or raise FileNotFoundError_."""
        record = await self.get_by_id(file_id)
        if record is None:
            raise FileNotFoundError_(file_id)
        return record

    async def get_by_user(
        self,
        user_id: int,
        *,
        workspace_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[StoredFile], int]:
        """Fetch files belonging to a user, with optional workspace filter."""
        query = select(StoredFile).where(StoredFile.user_id == user_id)
        count_query = select(func.count(StoredFile.id)).where(StoredFile.user_id == user_id)

        if workspace_id is not None:
            query = query.where(StoredFile.workspace_id == workspace_id)
            count_query = count_query.where(StoredFile.workspace_id == workspace_id)

        query = (
            query.order_by(StoredFile.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await self.session.execute(query)
        items = list(result.scalars().all())

        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        return items, total

    async def get_by_path(self, file_path: str) -> Optional[StoredFile]:
        """Fetch a stored file by its unique file path."""
        query = select(StoredFile).where(StoredFile.file_path == file_path)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update_metadata(self, file_id: str, **kwargs) -> StoredFile:
        """Update metadata fields on a stored file."""
        record = await self.get_by_id_or_raise(file_id)
        for key, value in kwargs.items():
            if hasattr(record, key):
                setattr(record, key, value)
        await self.session.flush()
        logger.debug(f"Updated stored file {file_id}")
        return record

    async def delete(self, file_id: str) -> None:
        """Delete a stored file record."""
        record = await self.get_by_id_or_raise(file_id)
        await self.session.delete(record)
        await self.session.flush()
        logger.info(f"Deleted stored file record {file_id}")

    async def count_by_user(self, user_id: int) -> int:
        """Count total files owned by a user."""
        query = select(func.count(StoredFile.id)).where(StoredFile.user_id == user_id)
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def total_bytes_by_user(self, user_id: int) -> int:
        """Sum total file bytes owned by a user."""
        query = select(func.sum(StoredFile.file_size_bytes)).where(StoredFile.user_id == user_id)
        result = await self.session.execute(query)
        return result.scalar() or 0


class StorageQuotaRepository:
    """Data access for StorageQuota records."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_quota(self, scope: str, scope_id: int) -> Optional[StorageQuota]:
        """Fetch a quota record by scope and scope_id."""
        query = select(StorageQuota).where(
            StorageQuota.scope == scope,
            StorageQuota.scope_id == scope_id,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_or_create_quota(self, scope: str, scope_id: int, max_bytes: int = 500 * 1024 * 1024) -> StorageQuota:
        """Get existing quota record or create a default one."""
        quota = await self.get_quota(scope, scope_id)
        if quota is not None:
            return quota
        quota = StorageQuota(
            scope=scope,
            scope_id=scope_id,
            max_bytes=max_bytes,
            used_bytes=0,
        )
        self.session.add(quota)
        await self.session.flush()
        logger.debug(f"Created storage quota for {scope}:{scope_id}")
        return quota

    async def add_bytes(self, scope: str, scope_id: int, bytes_to_add: int) -> StorageQuota:
        """Add bytes to the used count for a given quota."""
        quota = await self.get_or_create_quota(scope, scope_id)
        quota.used_bytes += bytes_to_add
        await self.session.flush()
        return quota

    async def subtract_bytes(self, scope: str, scope_id: int, bytes_to_subtract: int) -> StorageQuota:
        """Subtract bytes from the used count for a given quota."""
        quota = await self.get_or_create_quota(scope, scope_id)
        quota.used_bytes = max(0, quota.used_bytes - bytes_to_subtract)
        await self.session.flush()
        return quota

    async def recalculate(self, scope: str, scope_id: int) -> StorageQuota:
        """Recalculate used_bytes from actual stored file records."""
        if scope == "user":
            query = select(func.coalesce(func.sum(StoredFile.file_size_bytes), 0)).where(
                StoredFile.user_id == scope_id
            )
        else:
            query = select(func.coalesce(func.sum(StoredFile.file_size_bytes), 0)).where(
                StoredFile.workspace_id == scope_id
            )
        result = await self.session.execute(query)
        actual_used = result.scalar() or 0

        quota = await self.get_or_create_quota(scope, scope_id)
        quota.used_bytes = actual_used
        await self.session.flush()
        return quota


# Alias for backward compatibility — verification scripts look for StorageFileRepository
StorageFileRepository = StoredFileRepository

__all__ = [
    "StoredFileRepository",
    "StorageFileRepository",
    "StorageQuotaRepository",
]
