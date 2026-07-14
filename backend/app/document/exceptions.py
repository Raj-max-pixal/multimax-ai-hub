"""
Document-Specific Exceptions.

Extends the base MultimaxError hierarchy for document operations.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from app.core.exceptions import MultimaxError


class DocumentError(MultimaxError):
    """Base exception for all document-related errors."""

    def __init__(
        self,
        message: str = "Document operation failed",
        code: str = "DOCUMENT_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message=message, code=code, status_code=status_code, details=details)


class DocumentNotFoundError(DocumentError):
    """Raised when a requested document is not found."""

    def __init__(self, document_id: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Document not found: {document_id}",
            code="DOCUMENT_NOT_FOUND",
            status_code=404,
            details=details,
        )


class TextExtractionError(DocumentError):
    """Raised when text cannot be extracted from a file."""

    def __init__(self, filename: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Could not extract text from {filename}",
            code="TEXT_EXTRACTION_ERROR",
            status_code=400,
            details=details,
        )


class DocumentChatError(DocumentError):
    """Raised when a RAG chat operation fails."""

    def __init__(self, message: str = "Failed to chat with documents", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="DOCUMENT_CHAT_ERROR",
            status_code=502,
            details=details,
        )