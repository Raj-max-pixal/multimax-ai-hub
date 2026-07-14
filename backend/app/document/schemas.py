"""
Document Pydantic Schemas.

API request and response models for document endpoints.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# --------------------------------------------------------------------------- #
# Request Schemas
# --------------------------------------------------------------------------- #


class DocumentChatRequest(BaseModel):
    """Request body for chatting with documents."""

    query: str = Field(..., min_length=1)
    document_ids: List[str] = Field(..., min_length=1)
    model: Optional[str] = "phi3:latest"


# --------------------------------------------------------------------------- #
# Response Schemas
# --------------------------------------------------------------------------- #


class DocumentResponse(BaseModel):
    """Response payload for a single document."""

    id: str
    filename: str
    saved_filename: str
    file_type: str
    file_size: int
    chunk_count: int
    status: str = "processed"


class UploadResponse(BaseModel):
    """Response payload for document upload."""

    documents: List[DocumentResponse]
    message: str


class DocumentListResponse(BaseModel):
    """Response payload for listing documents."""

    documents: List[DocumentResponse]