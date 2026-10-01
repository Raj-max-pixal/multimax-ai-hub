"""
Document database models.

Migrated from legacy services/storage_service.py and services/document_service.py.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, Index
from sqlalchemy.orm import relationship

from app.core.database import Base


class Document(Base):
    """Represents an uploaded document in the system."""

    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String(512), nullable=False)
    original_filename = Column(String(512), nullable=False)
    file_path = Column(String(1024), nullable=False)
    file_size = Column(Integer, nullable=False, default=0)
    mime_type = Column(String(128), nullable=True)
    status = Column(String(32), nullable=False, default="uploaded")  # uploaded, processing, indexed, error
    error_message = Column(Text, nullable=True)
    workspace_id = Column(
        String(36),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    workspace = relationship("Workspace", back_populates="documents", lazy="selectin")
    user = relationship("User", back_populates="documents", lazy="selectin")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan", lazy="selectin")

    __table_args__ = (
        Index("idx_document_workspace_status", "workspace_id", "status"),
        Index("idx_document_user_created", "user_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<DocumentRecord id={self.id} filename={self.filename}>"


class DocumentChunk(Base):
    """Stores text chunks extracted from documents for RAG."""

    __tablename__ = "document_chunks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(
        String(36),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Text, nullable=True)  # JSON-serialized list of floats
    metadata_json = Column(Text, nullable=True)  # Arbitrary metadata as JSON
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    document = relationship("Document", back_populates="chunks", lazy="selectin")

    __table_args__ = (
        Index("idx_document_chunk_order", "document_id", "chunk_index", unique=True),
    )

    def __repr__(self) -> str:
        return f"<DocumentChunk id={self.id} doc_id={self.document_id} index={self.chunk_index}>"


class DocumentShare(Base):
    """Tracks document sharing between users."""

    __tablename__ = "document_shares"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    shared_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    shared_with_user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    permission = Column(String(32), nullable=False, default="read")  # read, write, admin
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    document = relationship("Document", lazy="selectin")
    shared_by = relationship("User", foreign_keys=[shared_by_user_id], lazy="selectin")
    shared_with = relationship("User", foreign_keys=[shared_with_user_id], lazy="selectin")

    __table_args__ = (
        Index(
            "idx_document_share_recipient",
            "document_id",
            "shared_with_user_id",
            unique=True,
        ),
    )


__all__ = [
    "Document",
    "DocumentChunk",
    "DocumentShare",
]
