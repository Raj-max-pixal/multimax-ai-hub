"""
Document Pydantic schemas for API request/response validation.

Migrated from legacy schemas and services.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# --------------------------------------------------------------------------- #
# Request Schemas
# --------------------------------------------------------------------------- #


class DocumentUploadRequest(BaseModel):
    """Metadata for a document upload."""

    workspace_id: Optional[int] = Field(None, description="Workspace to associate the document with")
    filename: Optional[str] = Field(None, description="Override filename")


class DocumentChatRequest(BaseModel):
    """Request to chat with a document using RAG."""

    document_id: UUID = Field(..., description="Document ID to query")
    query: str = Field(..., min_length=1, max_length=4096, description="User query")
    top_k: int = Field(5, ge=1, le=50, description="Number of chunks to retrieve")
    conversation_id: Optional[int] = Field(None, description="Conversation ID for context")


# --------------------------------------------------------------------------- #
# Response Schemas
# --------------------------------------------------------------------------- #


class DocumentResponse(BaseModel):
    """Serialized document metadata."""

    id: UUID
    filename: str
    original_filename: str
    file_size: int
    mime_type: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    workspace_id: Optional[int] = None
    user_id: int
    chunk_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UploadResponse(BaseModel):
    """Response after a successful document upload."""

    message: str = "Document uploaded successfully"
    document: DocumentResponse


class DocumentListResponse(BaseModel):
    """Paginated list of documents."""

    items: List[DocumentResponse]
    total: int
    page: int = 1
    page_size: int = 20


class DocumentChunkResponse(BaseModel):
    """A single document chunk with relevance score."""

    chunk_id: UUID
    document_id: UUID
    chunk_index: int
    content: str
    score: float = Field(0.0, description="Relevance score from vector search")


class DocumentChatResponse(BaseModel):
    """Response from a RAG chat query."""

    answer: str
    sources: List[DocumentChunkResponse]
    conversation_id: Optional[int] = None


# --------------------------------------------------------------------------- #
# Internal Schemas
# --------------------------------------------------------------------------- #


class ChunkData(BaseModel):
    """Internal representation of a chunk with embedding data."""

    content: str
    index: int
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embedding: Optional[List[float]] = None


class DocumentIndexData(BaseModel):
    """Data needed to index a document."""

    document_id: UUID
    chunks: List[ChunkData]


__all__ = [
    "DocumentUploadRequest",
    "DocumentChatRequest",
    "DocumentResponse",
    "UploadResponse",
    "DocumentListResponse",
    "DocumentChunkResponse",
    "DocumentChatResponse",
    "ChunkData",
    "DocumentIndexData",
]