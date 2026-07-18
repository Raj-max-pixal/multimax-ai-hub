"""
Storage Module — Business Logic Service.

Handles file upload/download, metadata management, and quota tracking.
"""

from __future__ import annotations

import os
import shutil
import uuid
from pathlib import Path
from typing import Any, BinaryIO, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logger import get_logger
from app.storage.exceptions import FileNotFoundError_, QuotaExceededError, StorageError
from app.storage.models import StoredFile
from app.storage.repositories import StoredFileRepository, StorageQuotaRepository

logger = get_logger("storage.service")

UPLOAD_DIR = get_settings().upload_dir or "uploads"


class StorageService:
    """File storage operations: upload, retrieve, delete, quota."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._file_repo: StoredFileRepository | None = None
        self._quota_repo: StorageQuotaRepository | None = None

    @property
    def file_repo(self) -> StoredFileRepository:
        if self._file_repo is None:
            self._file_repo = StoredFileRepository(self._session)
        return self._file_repo

    @property
    def quota_repo(self) -> StorageQuotaRepository:
        if self._quota_repo is None:
            self._quota_repo = StorageQuotaRepository(self._session)
        return self._quota_repo

    async def upload_file(
        self,
        *,
        file_obj: BinaryIO,
        original_filename: str,
        content_type: Optional[str] = None,
        file_size: int = 0,
        user_id: int,
        workspace_id: Optional[int] = None,
        is_public: bool = False,
        metadata_json: Optional[dict[str, Any]] = None,
    ) -> StoredFile:
        """Upload a file to local storage and create a DB record.

        Args:
            file_obj: Open file binary stream.
            original_filename: Original user-provided filename.
            content_type: MIME type (optional).
            file_size: File size in bytes.
            user_id: Owner user ID.
            workspace_id: Optional workspace association.
            is_public: Whether file is publicly accessible.
            metadata_json: Optional extra metadata.

        Returns:
            The created StoredFile record.

        Raises:
            QuotaExceededError: If user/workspace quota would be exceeded.
            StorageError: On write failure.
        """
        # Check quota
        await self._check_quota("user", user_id, file_size)
        if workspace_id:
            await self._check_quota("workspace", workspace_id, file_size)

        # Generate unique server-side filename
        ext = Path(original_filename).suffix
        server_filename = f"{uuid.uuid4().hex}{ext}"
        subdir = str(user_id)
        dest_dir = Path(UPLOAD_DIR) / subdir
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = dest_dir / server_filename

        # Write file to disk
        try:
            with open(dest_path, "wb") as buf:
                shutil.copyfileobj(file_obj, buf)
        except OSError as e:
            raise StorageError(f"Failed to write file: {e}") from e

        # Create DB record
        record = StoredFile(
            id=str(uuid.uuid4()),
            filename=server_filename,
            original_filename=original_filename,
            file_path=str(dest_path),
            content_type=content_type,
            file_size_bytes=file_size,
            storage_backend="local",
            user_id=user_id,
            workspace_id=workspace_id,
            is_public=is_public,
            metadata_json=metadata_json,
        )
        created = await self.file_repo.create(record)

        # Update quota
        await self.quota_repo.add_bytes("user", user_id, file_size)
        if workspace_id:
            await self.quota_repo.add_bytes("workspace", workspace_id, file_size)

        logger.info(f"Uploaded file {created.id} ({original_filename}, {file_size} bytes)")
        return created

    async def get_file(self, file_id: str) -> StoredFile:
        """Fetch a file record by ID (raises if not found)."""
        return await self.file_repo.get_by_id_or_raise(file_id)

    async def get_file_path(self, file_id: str) -> str:
        """Get the on-disk path for a file, verifying it exists."""
        record = await self.file_repo.get_by_id_or_raise(file_id)
        if not os.path.exists(record.file_path):
            raise FileNotFoundError_(file_id)
        return record.file_path

    async def list_files(
        self,
        user_id: int,
        *,
        workspace_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[StoredFile], int]:
        """List files for a user with pagination."""
        return await self.file_repo.get_by_user(
            user_id,
            workspace_id=workspace_id,
            page=page,
            page_size=page_size,
        )

    async def delete_file(self, file_id: str) -> None:
        """Delete a file record and its on-disk file."""
        record = await self.file_repo.get_by_id_or_raise(file_id)

        # Remove from disk
        if os.path.exists(record.file_path):
            os.remove(record.file_path)
            logger.info(f"Deleted file from disk: {record.file_path}")

        # Remove DB record
        user_id = record.user_id
        workspace_id = record.workspace_id
        file_size = record.file_size_bytes

        await self.file_repo.delete(file_id)

        # Update quota
        await self.quota_repo.subtract_bytes("user", user_id, file_size)
        if workspace_id:
            await self.quota_repo.subtract_bytes("workspace", workspace_id, file_size)

    async def get_storage_info(self, user_id: int) -> dict[str, Any]:
        """Get storage summary for a user."""
        total_files = await self.file_repo.count_by_user(user_id)
        total_bytes = await self.file_repo.total_bytes_by_user(user_id)
        quota = await self.quota_repo.get_quota("user", user_id)

        quota_data = None
        if quota:
            quota_data = {
                "scope": "user",
                "scope_id": user_id,
                "used_bytes": quota.used_bytes,
                "max_bytes": quota.max_bytes,
                "used_percent": round(quota.used_bytes / max(quota.max_bytes, 1) * 100, 2),
            }

        return {
            "total_files": total_files,
            "total_bytes": total_bytes,
            "quota": quota_data,
        }

    async def _check_quota(self, scope: str, scope_id: int, additional_bytes: int) -> None:
        """Raise QuotaExceededError if adding bytes would exceed the limit."""
        quota = await self.quota_repo.get_or_create_quota(scope, scope_id)
        if quota.used_bytes + additional_bytes > quota.max_bytes:
            raise QuotaExceededError(
                scope=scope,
                scope_id=scope_id,
                used=quota.used_bytes,
                limit=quota.max_bytes,
                requested=additional_bytes,
            )


__all__ = [
    "StorageService",
]