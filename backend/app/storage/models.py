"""
Storage Module — SQLAlchemy Models.

Tracks stored files, their metadata, and storage quotas.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.sqlite import BOOLEAN
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class StoredFile(Base):
    """Represents a file stored in the system."""

    __tablename__ = "stored_files"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    filename: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False, unique=True)
    content_type: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    storage_backend: Mapped[str] = mapped_column(String(50), default="local")
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    workspace_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("workspaces.id"), nullable=True)
    is_public: Mapped[bool] = mapped_column(BOOLEAN, default=False)
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<StoredFile(id={self.id}, filename='{self.original_filename}', size={self.file_size_bytes})>"


class StorageQuota(Base):
    """Tracks storage usage and limits per user or workspace."""

    __tablename__ = "storage_quotas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scope: Mapped[str] = mapped_column(String(20), nullable=False)  # "user" or "workspace"
    scope_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    max_bytes: Mapped[int] = mapped_column(BigInteger, default=500 * 1024 * 1024)  # 500 MB default
    used_bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        return (
            f"<StorageQuota(scope={self.scope}, scope_id={self.scope_id}, "
            f"used={self.used_bytes}/{self.max_bytes})>"
        )


__all__ = [
    "StoredFile",
    "StorageQuota",
]