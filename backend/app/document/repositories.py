"""
Document data access layer.

Migrated from legacy services/storage_service.py and services/document_service.py.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Sequence
from uuid import UUID

from sqlalchemy import Text, and_, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.document.exceptions import ChunkNotFoundError, DocumentNotFoundError
from app.document.models import DocumentChunk, Document as DocumentRecord, DocumentShare

logger = get_logger("document.repositories")


class DocumentRepository:
    """Data access for DocumentRecord."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, document: DocumentRecord) -> DocumentRecord:
        """Persist a new document record."""
        self.session.add(document)
        await self.session.flush()
        logger.debug(f"Created document record {document.id}")
        return document

    async def get_by_id(self, document_id: UUID) -> Optional[DocumentRecord]:
        """Fetch a document by its UUID."""
        result = await self.session.get(DocumentRecord, document_id)
        return result

    async def get_by_id_or_raise(self, document_id: UUID) -> DocumentRecord:
        """Fetch a document or raise DocumentNotFoundError."""
        doc = await self.get_by_id(document_id)
        if doc is None:
            raise DocumentNotFoundError(str(document_id))
        return doc

    async def get_by_user(
        self,
        user_id: int,
        *,
        workspace_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[DocumentRecord], int]:
        """Fetch documents belonging to a user, with optional workspace filter."""
        query = select(DocumentRecord).where(DocumentRecord.user_id == user_id)
        count_query = select(func.count(DocumentRecord.id)).where(DocumentRecord.user_id == user_id)

        if workspace_id is not None:
            query = query.where(DocumentRecord.workspace_id == workspace_id)
            count_query = count_query.where(DocumentRecord.workspace_id == workspace_id)

        query = (
            query.order_by(DocumentRecord.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await self.session.execute(query)
        items = list(result.scalars().all())

        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        return items, total

    async def update_status(
        self,
        document_id: UUID,
        status: str,
        *,
        error_message: Optional[str] = None,
        chunk_count: Optional[int] = None,
    ) -> DocumentRecord:
        """Update document processing status."""
        doc = await self.get_by_id_or_raise(document_id)
        doc.status = status
        if error_message is not None:
            doc.error_message = error_message
        if chunk_count is not None:
            doc.chunk_count = chunk_count
        await self.session.flush()
        return doc

    async def delete(self, document_id: UUID) -> None:
        """Delete a document and its associated chunks."""
        doc = await self.get_by_id_or_raise(document_id)
        await self.session.delete(doc)
        await self.session.flush()
        logger.info(f"Deleted document {document_id}")


class DocumentChunkRepository:
    """Data access for DocumentChunk."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def bulk_create(self, chunks: list[DocumentChunk]) -> list[DocumentChunk]:
        """Persist multiple document chunks."""
        self.session.add_all(chunks)
        await self.session.flush()
        logger.debug(f"Created {len(chunks)} chunks")
        return chunks

    async def get_by_document(self, document_id: UUID) -> Sequence[DocumentChunk]:
        """Fetch all chunks for a document, ordered by index."""
        query = (
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index)
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_id(self, chunk_id: UUID) -> Optional[DocumentChunk]:
        """Fetch a single chunk by ID."""
        result = await self.session.get(DocumentChunk, chunk_id)
        return result

    async def search_by_embedding(
        self,
        query_embedding: list[float],
        *,
        top_k: int = 5,
        workspace_id: Optional[int] = None,
    ) -> list[tuple[DocumentChunk, float]]:
        """Perform cosine similarity search using embeddings.

        NOTE: This is a placeholder implementation using Python-side
        comparison. For production, use pgvector or a dedicated vector DB.
        """
        # Get all chunks with embeddings
        query = select(DocumentChunk).where(
            DocumentChunk.embedding.isnot(None),
            DocumentChunk.embedding != "",
        )
        result = await self.session.execute(query)
        chunks: Sequence[DocumentChunk] = result.scalars().all()

        scored: list[tuple[DocumentChunk, float]] = []
        query_vec = query_embedding

        for chunk in chunks:
            if not chunk.embedding:
                continue
            try:
                chunk_emb: list[float] = json.loads(chunk.embedding)
            except (json.JSONDecodeError, TypeError):
                continue

            score = self._cosine_similarity(query_vec, chunk_emb)
            if score > 0.0:
                scored.append((chunk, score))

        # Sort by score descending, return top_k
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if len(a) != len(b) or not a:
            return 0.0
        dot = sum(av * bv for av, bv in zip(a, b))
        norm_a = sum(av * av for av in a) ** 0.5
        norm_b = sum(bv * bv for bv in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    async def delete_by_document(self, document_id: UUID) -> None:
        """Delete all chunks for a document."""
        query = select(DocumentChunk).where(DocumentChunk.document_id == document_id)
        result = await self.session.execute(query)
        chunks = result.scalars().all()
        for chunk in chunks:
            await self.session.delete(chunk)
        await self.session.flush()


class DocumentShareRepository:
    """Data access for DocumentShare."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, share: DocumentShare) -> DocumentShare:
        """Persist a new document share record."""
        self.session.add(share)
        await self.session.flush()
        return share

    async def get_shares_for_document(self, document_id: UUID) -> Sequence[DocumentShare]:
        """Get all shares for a document."""
        query = select(DocumentShare).where(DocumentShare.document_id == document_id)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def delete(self, share_id: int) -> None:
        """Delete a share record."""
        share = await self.session.get(DocumentShare, share_id)
        if share:
            await self.session.delete(share)
            await self.session.flush()


__all__ = [
    "DocumentRepository",
    "DocumentChunkRepository",
    "DocumentShareRepository",
]