"""
Document Dependencies.

Provides FastAPI dependency injection helpers for the Document module,
following the same pattern as app/chat/dependencies.py and
app/auth/dependencies.py.

Usage:
    @router.post("/upload")
    async def upload(file: UploadFile, doc_service: DocumentService = Depends(get_document_service)):
        ...
"""

from __future__ import annotations

from typing import AsyncGenerator

from fastapi import Depends

from app.document.repositories import DocumentRepository
from app.document.service import DocumentService


# --------------------------------------------------------------------------- #
# Repository dependency
# --------------------------------------------------------------------------- #


async def get_document_repository() -> AsyncGenerator[DocumentRepository, None]:
    """Provide a fresh DocumentRepository per request.

    Because the repository is a simple in-memory store, we can yield the
    same singleton safely.  If SQL persistence were introduced later this
    would become a scoped session.
    """
    yield DocumentRepository()


# --------------------------------------------------------------------------- #
# Service dependency
# --------------------------------------------------------------------------- #


async def get_document_service(
    repository: DocumentRepository = Depends(get_document_repository),
) -> AsyncGenerator[DocumentService, None]:
    """Provide a DocumentService wired to the repository."""
    yield DocumentService(repository=repository)