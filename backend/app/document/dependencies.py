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

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.document.repositories import DocumentRepository
from app.document.service import DocumentService


# --------------------------------------------------------------------------- #
# Repository dependency
# --------------------------------------------------------------------------- #


async def get_document_repository(
    session: AsyncSession = Depends(get_db_session),
) -> AsyncGenerator[DocumentRepository, None]:
    """Provide a request-scoped SQLAlchemy document repository."""
    yield DocumentRepository(session)


# --------------------------------------------------------------------------- #
# Service dependency
# --------------------------------------------------------------------------- #


async def get_document_service(
    session: AsyncSession = Depends(get_db_session),
) -> AsyncGenerator[DocumentService, None]:
    """Provide a DocumentService wired to the repository."""
    yield DocumentService(session=session)
