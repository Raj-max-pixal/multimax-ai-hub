"""
Document-specific exception classes.

Migrated from legacy services/exceptions.py domain-specific errors.
"""

from __future__ import annotations

from app.core.exceptions import MultimaxError


class DocumentError(MultimaxError):
    """Base exception for document module errors."""

    def __init__(self, message: str, code: str = "DOCUMENT_ERROR", details: dict | None = None) -> None:
        super().__init__(message, code=code, details=details)


class DocumentNotFoundError(DocumentError):
    """Raised when a document is not found."""

    def __init__(self, document_id: str, details: dict | None = None) -> None:
        super().__init__(
            message=f"Document not found: {document_id}",
            code="DOCUMENT_NOT_FOUND",
            details=details or {"document_id": document_id},
        )


class DocumentUploadError(DocumentError):
    """Raised when document upload fails."""

    def __init__(self, reason: str, details: dict | None = None) -> None:
        super().__init__(
            message=f"Document upload failed: {reason}",
            code="DOCUMENT_UPLOAD_ERROR",
            details=details,
        )


class DocumentProcessingError(DocumentError):
    """Raised when document text extraction or indexing fails."""

    def __init__(self, document_id: str, reason: str, details: dict | None = None) -> None:
        super().__init__(
            message=f"Document processing failed for {document_id}: {reason}",
            code="DOCUMENT_PROCESSING_ERROR",
            details=details or {"document_id": document_id},
        )


class ChunkNotFoundError(DocumentError):
    """Raised when a document chunk is not found."""

    def __init__(self, chunk_id: str, details: dict | None = None) -> None:
        super().__init__(
            message=f"Chunk not found: {chunk_id}",
            code="CHUNK_NOT_FOUND",
            details=details or {"chunk_id": chunk_id},
        )


class EmbeddingError(DocumentError):
    """Raised when embedding generation or search fails."""

    def __init__(self, reason: str, details: dict | None = None) -> None:
        super().__init__(
            message=f"Embedding operation failed: {reason}",
            code="EMBEDDING_ERROR",
            details=details,
        )


__all__ = [
    "DocumentError",
    "DocumentNotFoundError",
    "DocumentUploadError",
    "DocumentProcessingError",
    "ChunkNotFoundError",
    "EmbeddingError",
]