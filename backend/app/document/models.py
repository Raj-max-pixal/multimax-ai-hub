"""
Document Domain Models.

Defines Pydantic models for document metadata (not SQLAlchemy ORM).
The legacy implementation used an in-memory list; we preserve that behavior.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class DocumentRecord:
    """In-memory document metadata record matching legacy documents_db format."""

    id: str
    filename: str
    saved_filename: str
    file_type: str
    file_size: int
    chunk_count: int
    status: str = "processed"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "filename": self.filename,
            "saved_filename": self.saved_filename,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "chunk_count": self.chunk_count,
            "status": self.status,
        }


@dataclass
class ChunkRecord:
    """A single text chunk with metadata."""

    chunk_id: str
    text: str
    index: int
    document_id: Optional[str] = None