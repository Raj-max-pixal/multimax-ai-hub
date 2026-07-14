"""
Document Domain Module.

Manages document upload, text extraction, embedding, and RAG-based chat.
Migrated from legacy services/storage_service.py, services/document_service.py,
services/embedding_service.py, and services/rag_service.py.
"""

from __future__ import annotations

from typing import Any

from app.core.module_loader import ModuleInfo
from app.document.api import router

module_info = ModuleInfo(
    name="document",
    package="app.document",
    description="Document upload, text extraction, embedding, and RAG chat",
    version="0.1.0",
    dependencies=["core"],
    enabled=True,
)


def register(app: Any, container: Any) -> None:
    """Register the document module with the FastAPI application.

    Called by the ModuleLoader during application startup.
    """
    app.include_router(router)

    from app.document.service import DocumentService
    container.register_singleton(DocumentService, DocumentService())


__all__ = [
    "DocumentService",
    "router",
    "module_info",
    "register",
]