"""
Chat Pydantic Schemas.

Request/response schemas for the chat module.
Follows the same conventions as auth/schemas.py and the existing project style.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class CreateChatSessionRequest(BaseModel):
    """Request schema for creating a new chat session."""
    workspace_id: str = Field(..., description="The workspace this session belongs to")
    title: str = Field("New Chat", max_length=255, description="Display title for the session")
    created_by: str = Field(..., description="User ID of the creator")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata")

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        v = v.strip()
        if not v:
            return "New Chat"
        return v


class RenameChatSessionRequest(BaseModel):
    """Request schema for renaming a chat session."""
    title: str = Field(..., min_length=1, max_length=255, description="New title for the session")

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Title must not be empty after trimming whitespace")
        return v


class CreateMessageRequest(BaseModel):
    """Request schema for creating a new message in a session."""
    session_id: str = Field(..., description="The session this message belongs to")
    role: str = Field(..., pattern=r"^(user|assistant|system)$", description="Message role")
    content: str = Field(..., description="Message content text")
    model: Optional[str] = Field(None, max_length=255, description="Model identifier")
    tokens: Optional[int] = Field(None, ge=0, description="Token count")

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Message content must not be empty")
        return v


class ChatSessionResponse(BaseModel):
    """Response schema for a chat session."""
    id: str
    workspace_id: str
    title: str
    created_by: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    deleted_at: Optional[str] = None

    @classmethod
    def from_orm_model(cls, session: Any) -> "ChatSessionResponse":
        """Build response from a ChatSession ORM instance."""
        return cls(
            id=session.id,
            workspace_id=session.workspace_id,
            title=session.title,
            created_by=session.created_by,
            metadata=session.metadata_json or {},
            created_at=session.created_at.isoformat() if session.created_at else None,
            updated_at=session.updated_at.isoformat() if session.updated_at else None,
            deleted_at=session.deleted_at.isoformat() if session.deleted_at else None,
        )


class CreateChatSessionResponse(BaseModel):
    """Response schema after creating a chat session."""
    id: str
    workspace_id: str
    title: str
    created_by: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @classmethod
    def from_orm_model(cls, session: Any) -> "CreateChatSessionResponse":
        """Build response from a ChatSession ORM instance."""
        return cls(
            id=session.id,
            workspace_id=session.workspace_id,
            title=session.title,
            created_by=session.created_by,
            metadata=session.metadata_json or {},
            created_at=session.created_at.isoformat() if session.created_at else None,
            updated_at=session.updated_at.isoformat() if session.updated_at else None,
        )


class ChatSessionListResponse(BaseModel):
    """Response schema for listing chat sessions."""
    sessions: List[ChatSessionResponse]
    total: int


class MessageResponse(BaseModel):
    """Response schema for a single message."""
    id: str
    session_id: str
    role: str
    content: str
    model: Optional[str] = None
    tokens: Optional[int] = None
    created_at: Optional[str] = None

    @classmethod
    def from_orm_model(cls, message: Any) -> "MessageResponse":
        """Build response from a Message ORM instance."""
        return cls(
            id=message.id,
            session_id=message.session_id,
            role=message.role.value if message.role else "",
            content=message.content,
            model=message.model or None,
            tokens=message.tokens,
            created_at=message.created_at.isoformat() if message.created_at else None,
        )


class MessageListResponse(BaseModel):
    """Response schema for listing messages in a session."""
    messages: List[MessageResponse]
    total: int


class CreateAttachmentRequest(BaseModel):
    """Request schema for creating a new attachment."""
    message_id: str = Field(..., description="The message this attachment belongs to")
    filename: str = Field(..., max_length=255, description="Original filename")
    file_type: str = Field("application/octet-stream", max_length=127, description="MIME type")
    file_size: int = Field(0, ge=0, description="Size in bytes")
    path: str = Field(..., max_length=1024, description="Storage path for the file")

    @field_validator("filename")
    @classmethod
    def validate_filename(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Filename must not be empty")
        return v


class AttachmentResponse(BaseModel):
    """Response schema for a single attachment."""
    id: str
    message_id: str
    filename: str
    file_type: str
    file_size: int
    path: str
    created_at: Optional[str] = None

    @classmethod
    def from_orm_model(cls, attachment: Any) -> "AttachmentResponse":
        """Build response from an Attachment ORM instance."""
        return cls(
            id=attachment.id,
            message_id=attachment.message_id,
            filename=attachment.filename,
            file_type=attachment.file_type,
            file_size=attachment.file_size,
            path=attachment.path,
            created_at=attachment.created_at.isoformat() if attachment.created_at else None,
        )


class AttachmentListResponse(BaseModel):
    """Response schema for listing attachments."""
    attachments: List[AttachmentResponse]
    total: int
