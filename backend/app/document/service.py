"""
Document business logic service.

Migrated from legacy services/document_service.py, services/embedding_service.py,
services/rag_service.py, and services/storage_service.py.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logger import get_logger
from app.document.exceptions import (
    DocumentNotFoundError,
    DocumentProcessingError,
    DocumentUploadError,
    EmbeddingError,
)
from app.document.models import DocumentChunk, DocumentRecord
from app.document.repositories import DocumentChunkRepository, DocumentRepository
from app.document.schemas import (
    ChunkData,
    DocumentChatRequest,
    DocumentChatResponse,
    DocumentChunkResponse,
    DocumentIndexData,
    DocumentResponse,
)

logger = get_logger("document.service")


class DocumentService:
    """High-level document operations: upload, processing, indexing, and RAG chat."""

    def __init__(self, session: AsyncSession | None = None) -> None:
        self._session = session
        self._doc_repo: DocumentRepository | None = None
        self._chunk_repo: DocumentChunkRepository | None = None

    @property
    def doc_repo(self) -> DocumentRepository:
        if self._doc_repo is None:
            if self._session is None:
                raise RuntimeError("DocumentService not initialized with a database session")
            self._doc_repo = DocumentRepository(self._session)
        return self._doc_repo

    @property
    def chunk_repo(self) -> DocumentChunkRepository:
        if self._chunk_repo is None:
            if self._session is None:
                raise RuntimeError("DocumentService not initialized with a database session")
            self._chunk_repo = DocumentChunkRepository(self._session)
        return self._chunk_repo

    # ------------------------------------------------------------------ #
    # Upload
    # ------------------------------------------------------------------ #

    async def upload_document(
        self,
        *,
        file_path: str,
        filename: str,
        original_filename: str,
        file_size: int,
        mime_type: str | None,
        user_id: int,
        workspace_id: int | None = None,
    ) -> DocumentRecord:
        """Register an uploaded document in the database.

        Args:
            file_path: Path on disk where the file is stored.
            filename: Server-side filename.
            original_filename: Original user-provided filename.
            file_size: File size in bytes.
            mime_type: MIME type of the file.
            user_id: Owner user ID.
            workspace_id: Optional workspace association.

        Returns:
            The created DocumentRecord.
        """
        record = DocumentRecord(
            id=uuid.uuid4(),
            filename=filename,
            original_filename=original_filename,
            file_path=file_path,
            file_size=file_size,
            mime_type=mime_type,
            status="uploaded",
            user_id=user_id,
            workspace_id=workspace_id,
        )
        return await self.doc_repo.create(record)

    async def get_document(self, document_id: UUID) -> DocumentRecord:
        """Fetch a document by ID, raising if not found."""
        return await self.doc_repo.get_by_id_or_raise(document_id)

    async def list_user_documents(
        self,
        user_id: int,
        *,
        workspace_id: int | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[DocumentRecord], int]:
        """List documents for a user with pagination."""
        return await self.doc_repo.get_by_user(
            user_id,
            workspace_id=workspace_id,
            page=page,
            page_size=page_size,
        )

    async def delete_document(self, document_id: UUID) -> None:
        """Delete a document and its files."""
        doc = await self.doc_repo.get_by_id_or_raise(document_id)

        # Remove file from disk
        if os.path.exists(doc.file_path):
            os.remove(doc.file_path)
            logger.info(f"Deleted file: {doc.file_path}")

        # Remove from DB (cascades to chunks)
        await self.doc_repo.delete(document_id)

    # ------------------------------------------------------------------ #
    # Processing / Indexing
    # ------------------------------------------------------------------ #

    async def process_and_index_document(
        self,
        document_id: UUID,
        *,
        text_extractor: Any,  # Callable[[str], str] — extract text from file
        embedding_fn: Any,  # Callable[[str], list[float]] — generate embedding
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> int:
        """Extract text, chunk it, generate embeddings, and store chunks.

        Args:
            document_id: Document to process.
            text_extractor: Function that takes a file path and returns text.
            embedding_fn: Function that takes text and returns an embedding vector.
            chunk_size: Target characters per chunk.
            chunk_overlap: Overlap between consecutive chunks.

        Returns:
            Number of chunks created.
        """
        doc = await self.doc_repo.get_by_id_or_raise(document_id)
        await self.doc_repo.update_status(document_id, "processing")

        try:
            # Extract text from file
            text = text_extractor(doc.file_path)

            # Split into chunks
            chunks = self._chunk_text(text, chunk_size=chunk_size, overlap=chunk_overlap)

            # Generate embeddings and create chunk models
            chunk_models: list[DocumentChunk] = []
            for i, chunk_text in enumerate(chunks):
                embedding = embedding_fn(chunk_text)
                chunk = DocumentChunk(
                    id=uuid.uuid4(),
                    document_id=document_id,
                    chunk_index=i,
                    content=chunk_text,
                    embedding=json.dumps(embedding) if embedding else None,
                    metadata_json=json.dumps({
                        "chunk_size": len(chunk_text),
                        "doc_filename": doc.filename,
                    }),
                )
                chunk_models.append(chunk)

            # Persist all chunks
            created = await self.chunk_repo.bulk_create(chunk_models)

            # Update document status
            await self.doc_repo.update_status(
                document_id,
                "indexed",
                chunk_count=len(created),
            )

            logger.info(
                f"Indexed document {document_id}: {len(created)} chunks"
            )
            return len(created)

        except Exception as e:
            await self.doc_repo.update_status(
                document_id,
                "error",
                error_message=str(e),
            )
            raise DocumentProcessingError(
                document_id=str(document_id),
                reason=str(e),
            ) from e

    def _chunk_text(
        self,
        text: str,
        chunk_size: int = 1000,
        overlap: int = 200,
    ) -> list[str]:
        """Split text into overlapping chunks."""
        if not text:
            return []

        chunks: list[str] = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = start + chunk_size
            if end >= text_len:
                chunks.append(text[start:])
                break

            # Try to break at a sentence boundary or newline
            search_end = min(end + min(overlap, 200), text_len)
            break_point = self._find_break(text, end, search_end)

            if break_point == -1:
                break_point = end

            chunks.append(text[start:break_point])
            start = max(break_point - overlap, start + 1)

        return chunks

    @staticmethod
    def _find_break(text: str, start: int, end: int) -> int:
        """Find the best break point in the range [start, end]."""
        # Priority: double newline, single newline, sentence end, word boundary
        for i in range(end - 1, start - 1, -1):
            if text[i : i + 2] == "\n\n":
                return i + 2
        for i in range(end - 1, start - 1, -1):
            if text[i] == "\n":
                return i + 1
        for i in range(end - 1, start - 1, -1):
            if text[i] in ".!?" and i + 1 < len(text) and text[i + 1] == " ":
                return i + 1
        # Word boundary
        for i in range(end - 1, start - 1, -1):
            if text[i] == " ":
                return i + 1
        return -1

    # ------------------------------------------------------------------ #
    # RAG Chat
    # ------------------------------------------------------------------ #

    async def chat_with_document(
        self,
        request: DocumentChatRequest,
        *,
        embedding_fn: Any,  # Callable[[str], list[float]]
        llm_complete_fn: Any,  # Callable[[str, list[str]], str]
        session: AsyncSession | None = None,
    ) -> DocumentChatResponse:
        """Answer a query against a document using RAG.

        Args:
            request: Chat request with document_id, query, top_k.
            embedding_fn: Function to embed the query.
            llm_complete_fn: Function that takes (query, context_chunks) and returns answer.
            session: Optional DB session (falls back to service session).

        Returns:
            DocumentChatResponse with answer and source chunks.
        """
        try:
            query_embedding = embedding_fn(request.query)
        except Exception as e:
            raise EmbeddingError(f"Failed to embed query: {e}") from e

        repo = self.chunk_repo
        results = await repo.search_by_embedding(
            query_embedding,
            top_k=request.top_k,
        )

        # Build response
        sources: list[DocumentChunkResponse] = []
        context_parts: list[str] = []
        for chunk, score in results:
            sources.append(
                DocumentChunkResponse(
                    chunk_id=chunk.id,
                    document_id=chunk.document_id,
                    chunk_index=chunk.chunk_index,
                    content=chunk.content,
                    score=score,
                )
            )
            context_parts.append(
                f"[Chunk {chunk.chunk_index} (score: {score:.3f})]\n{chunk.content}"
            )

        context = "\n\n".join(context_parts)

        try:
            answer = llm_complete_fn(request.query, context)
        except Exception as e:
            raise DocumentProcessingError(
                document_id=str(request.document_id),
                reason=f"LLM completion failed: {e}",
            ) from e

        return DocumentChatResponse(
            answer=answer,
            sources=sources,
        )


__all__ = [
    "DocumentService",
]