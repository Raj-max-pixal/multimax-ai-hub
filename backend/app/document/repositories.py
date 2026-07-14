"""
Document Repositories.

Provides CRUD operations for DocumentRecord metadata following the
repository pattern used elsewhere in the project.  Preserves the legacy
in-memory storage approach (documents_db) to avoid introducing SQL tables
for what is currently a simple document registry.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.core.logger import get_logger
from app.document.models import DocumentRecord

logger = get_logger("app.document.repositories")


class DocumentRepository:
    """Repository for DocumentRecord CRUD operations (in-memory)."""

    def __init__(self) -> None:
        self._store: List[DocumentRecord] = []

    # ------------------------------------------------------------------ #
    # Create
    # ------------------------------------------------------------------ #

    async def create(
        self,
        filename: str,
        saved_filename: str,
        file_type: str,
        file_size: int,
        chunk_count: int,
        status: str = "processed",
    ) -> DocumentRecord:
        """Create a new document record.

        Args:
            filename: Original uploaded filename.
            saved_filename: Name of the file on disk.
            file_type: File extension / MIME type.
            file_size: Size in bytes.
            chunk_count: Number of text chunks generated.
            status: Processing status (default ``"processed"``).

        Returns:
            The newly created DocumentRecord instance.
        """
        record = DocumentRecord(
            id=str(uuid4()),
            filename=filename,
            saved_filename=saved_filename,
            file_type=file_type,
            file_size=file_size,
            chunk_count=chunk_count,
            status=status,
        )
        self._store.append(record)
        logger.info(f"Document record created: {record.id} ({filename})")
        return record

    # ------------------------------------------------------------------ #
    # Read
    # ------------------------------------------------------------------ #

    async def get_by_id(self, document_id: str) -> Optional[DocumentRecord]:
        """Retrieve a document record by its ID.

        Args:
            document_id: The document UUID.

        Returns:
            DocumentRecord if found, else None.
        """
        return next((d for d in self._store if d.id == document_id), None)

    async def list_all(self) -> List[DocumentRecord]:
        """Return all document records.

        Returns:
            A list of all DocumentRecord instances.
        """
        return list(self._store)

    # ------------------------------------------------------------------ #
    # Delete
    # ------------------------------------------------------------------ #

    async def delete(self, document_id: str) -> Optional[DocumentRecord]:
        """Delete a document record by its ID.

        Args:
            document_id: The document UUID.

        Returns:
            The removed DocumentRecord if found, else None.
        """
        record = await self.get_by_id(document_id)
        if record is None:
            return None
        self._store = [d for d in self._store if d.id != document_id]
        logger.info(f"Document record deleted: {document_id} ({record.filename})")
        return record