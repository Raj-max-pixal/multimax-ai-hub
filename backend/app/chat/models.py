"""
Chat Domain Models.

Defines SQLAlchemy ORM models for chat sessions, messages, and attachments.
Follows the same patterns as workspace/models.py and auth/models.py.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
    BigInteger,
    Index,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class MessageRole(str, PyEnum):
    """Roles for chat messages."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatSession(Base):
    """A chat session within a workspace."""

    __tablename__ = "chat_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(
        String(36),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = Column(String(255), default="New Chat")
    created_by = Column(String(36), nullable=False, index=True)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    workspace = relationship("Workspace", back_populates="chat_sessions")
    messages = relationship(
        "Message", back_populates="session", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_chat_session_workspace", "workspace_id"),
        Index("idx_chat_session_created_by", "created_by"),
        Index("idx_chat_session_deleted", "deleted_at"),
    )

    @property
    def is_deleted(self) -> bool:
        """Check if the session has been soft-deleted."""
        return self.deleted_at is not None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "title": self.title,
            "created_by": self.created_by,
            "metadata": self.metadata_json or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }


class Message(Base):
    """A message within a chat session."""

    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(
        String(36),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role = Column(Enum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    model = Column(String(255), default="")
    tokens = Column(Integer, nullable=True)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    session = relationship("ChatSession", back_populates="messages")
    attachments = relationship(
        "Attachment", back_populates="message", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_message_session", "session_id"),
        Index("idx_message_created", "session_id", "created_at"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "role": self.role.value if self.role else None,
            "content": self.content,
            "model": self.model,
            "tokens": self.tokens,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Attachment(Base):
    """A file attachment linked to a message."""

    __tablename__ = "attachments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id = Column(
        String(36),
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    filename = Column(String(255), nullable=False)
    file_type = Column(String(127), default="application/octet-stream")
    file_size = Column(BigInteger, default=0)
    path = Column(String(1024), nullable=False)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    message = relationship("Message", back_populates="attachments")

    __table_args__ = (
        Index("idx_attachment_message", "message_id"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "message_id": self.message_id,
            "filename": self.filename,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "path": self.path,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }