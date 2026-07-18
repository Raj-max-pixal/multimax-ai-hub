"""
Storage Module — Pydantic Schemas.

Defines the API contract for file storage operations.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class StoredFileBase(BaseModel):
    """Base schema with common file metadata fields."""

    original_filename: str = Field(..., max_length=512)
    content_type: Optional[str] = None
    file_size_bytes: int = 0
    is_public: bool = False
    metadata_json: Optional[Dict[str, Any]] = None


class StoredFileCreate(StoredFileBase):
    """Schema for uploading a new file."""

    workspace_id: Optional[int] = None


class StoredFileUpdate(BaseModel):
    """Schema for updating file metadata."""

    original_filename: Optional[str] = None
    is_public: Optional[bool] = None
    metadata_json: Optional[Dict[str, Any]] = None


class StoredFileResponse(StoredFileBase):
    """Schema returned to clients after a file operation."""

    id: str
    filename: str
    file_path: str
    storage_backend: str
    user_id: Optional[int] = None
    workspace_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class StoredFileListResponse(BaseModel):
    """Paginated list of stored files."""

    items: list[StoredFileResponse]
    total: int
    page: int
    page_size: int


class StorageQuotaResponse(BaseModel):
    """Schema for storage quota information."""

    scope: str
    scope_id: int
    used_bytes: int
    max_bytes: int
    used_percent: float

    model_config = {"from_attributes": True}


class StorageInfoResponse(BaseModel):
    """Overall storage summary."""

    total_files: int
    total_bytes: int
    quota: Optional[StorageQuotaResponse] = None


__all__ = [
    "StoredFileBase",
    "StoredFileCreate",
    "StoredFileUpdate",
    "StoredFileResponse",
    "StoredFileListResponse",
    "StorageQuotaResponse",
    "StorageInfoResponse",
]