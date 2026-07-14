"""
Document Service.

Orchestrates document upload, text extraction, chunking, embedding storage,
retrieval, deletion, and RAG-based chat.  Preserves the same behaviour as
the legacy services/storage_service.py, services/document_service.py,
services/embedding_service.py, and services/rag_service.py, but wires them
through the new DI container and structured logging.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, AsyncGenerator

import httpx
import uuid
from fastapi import UploadFile

from app.core.logger import get_logger
from app.document.repositories import DocumentRepository
from app.document.models import DocumentRecord
from app.document.exceptions import (
    DocumentError,
    DocumentNotFoundError,
    TextExtractionError,
    DocumentChatError,
)

logger = get_logger("app.document.service")

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

UPLOAD_DIR = "uploads"
CHROMA_DIR = "chroma_db"
COLLECTION_NAME = "multimax_documents"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(CHROMA_DIR, exist_ok=True)

# --------------------------------------------------------------------------- #
# Lazy ChromaDB / Sentence-Transformer initialisation
# --------------------------------------------------------------------------- #

_chroma_client = None
_chroma_collection = None
_embedding_model = None


def _get_chroma_collection():
    """Return a lazy-initialised ChromaDB collection."""
    global _chroma_client, _chroma_collection, _embedding_model
    if _chroma_collection is None:
        import chromadb
        from chromadb.utils import embedding_functions
        from sentence_transformers import SentenceTransformer

        _chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
        sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        _chroma_collection = _chroma_client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=sentence_transformer_ef,
        )
        _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("ChromaDB collection initialised", extra={"collection": COLLECTION_NAME})
    return _chroma_collection


# ===================================================================
# Service
# ===================================================================


class DocumentService:
    """High-level document operations service.

    Every public method that produces externally-visible side-effects
    logs a structured event so operators can trace the document lifecycle.
    """

    def __init__(self, repository: Optional[DocumentRepository] = None) -> None:
        self._repository = repository or DocumentRepository()

    # ------------------------------------------------------------------ #
    # Upload & Process
    # ------------------------------------------------------------------ #

    async def upload_document(self, file: UploadFile) -> DocumentRecord:
        """Save an uploaded file, extract text, chunk, and embed.

        Args:
            file: The uploaded file from the HTTP request.

        Returns:
            A DocumentRecord describing the processed document.

        Raises:
            DocumentProcessingError: If text extraction or embedding fails.
        """
        logger.info("Upload started", extra={"filename": file.filename})

        # 1. Save file to disk ----------------------------------------- #
        file_id = str(uuid.uuid4())
        original_filename = file.filename or "unnamed"
        file_extension = os.path.splitext(original_filename)[1]
        saved_filename = f"{file_id}{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, saved_filename)

        try:
            content = await file.read()
            with open(file_path, "wb") as buffer:
                buffer.write(content)
        except OSError as exc:
            raise DocumentError(
                message=f"Failed to save file: {exc}",
                code="DOCUMENT_STORAGE_ERROR",
                status_code=500,
            ) from exc

        file_size = os.path.getsize(file_path)

        # 2. Extract text ---------------------------------------------- #
        text = self._extract_text(file_path, file_extension)
        if not text:
            # Clean up the saved file if extraction fails
            try:
                os.remove(file_path)
            except OSError:
                pass
            raise TextExtractionError(original_filename)

        # 3. Chunk text ------------------------------------------------- #
        chunks = self._split_text_into_chunks(text)

        # 4. Generate embeddings & store in ChromaDB ------------------- #
        self._embed_chunks(file_id, chunks)
        logger.info(
            "Embedding generation complete",
            extra={"document_id": file_id, "chunk_count": len(chunks)},
        )

        # 5. Persist metadata ------------------------------------------ #
        record = await self._repository.create(
            filename=original_filename,
            saved_filename=saved_filename,
            file_type=file_extension,
            file_size=file_size,
            chunk_count=len(chunks),
        )

        logger.info(
            "Upload completed",
            extra={
                "document_id": record.id,
                "filename": original_filename,
                "chunk_count": len(chunks),
            },
        )
        return record

    # ------------------------------------------------------------------ #
    # Retrieve
    # ------------------------------------------------------------------ #

    async def get_document(self, document_id: str) -> DocumentRecord:
        """Return a single document record.

        Raises:
            DocumentNotFoundError: If the ID does not exist.
        """
        record = await self._repository.get_by_id(document_id)
        if record is None:
            raise DocumentNotFoundError(document_id)
        return record

    async def list_documents(self) -> List[DocumentRecord]:
        """Return all document records."""
        return await self._repository.list_all()

    # ------------------------------------------------------------------ #
    # Delete
    # ------------------------------------------------------------------ #

    async def delete_document(self, document_id: str) -> None:
        """Delete a document and its associated file + ChromaDB entries.

        Raises:
            DocumentNotFoundError: If the ID does not exist.
        """
        record = await self._repository.get_by_id(document_id)
        if record is None:
            raise DocumentNotFoundError(document_id)

        # Delete from ChromaDB
        self._delete_chunks(document_id)

        # Delete physical file
        file_path = os.path.join(UPLOAD_DIR, record.saved_filename)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except OSError as exc:
            logger.warning(
                "Failed to remove file from disk",
                extra={"path": file_path, "error": str(exc)},
            )

        # Delete metadata
        await self._repository.delete(document_id)
        logger.info("Document deleted", extra={"document_id": document_id})

    # ------------------------------------------------------------------ #
    # RAG – Chat with Documents
    # ------------------------------------------------------------------ #

    async def chat_with_documents(
        self,
        query: str,
        document_ids: List[str],
        model: str = "phi3:latest",
    ) -> AsyncGenerator[bytes, None]:
        """Stream an LLM response grounded in the selected documents.

        Args:
            query: The user's question.
            document_ids: Which documents to restrict the search to.
            model: Ollama model name.

        Yields:
            Raw byte chunks from the Ollama streaming response.
        """
        logger.info(
            "RAG query",
            extra={
                "model": model,
                "document_ids": document_ids,
                "query_prefix": query[:80],
            },
        )

        search_results = self._search_chunks(query, document_ids)
        context = self._build_context(search_results)
        prompt = self._build_prompt(query, context)

        ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")

        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "POST",
                f"{ollama_url}/api/chat",
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": True,
                },
            ) as response:
                response.raise_for_status()
                async for chunk in response.aiter_bytes():
                    yield chunk

    # ================================================================== #
    # Internal helpers (extraction, chunking, embedding, search)
    # ================================================================== #

    @staticmethod
    def _extract_text(file_path: str, file_extension: str) -> Optional[str]:
        """Extract text from a file based on its extension.

        Supports PDF, DOCX, TXT, and MD.
        """
        ext = file_extension.lower()
        try:
            if ext == ".pdf":
                from pypdf import PdfReader

                reader = PdfReader(file_path)
                return "".join(page.extract_text() or "" for page in reader.pages)

            if ext == ".docx":
                from docx import Document as DocxDocument

                doc = DocxDocument(file_path)
                return "\n".join(p.text for p in doc.paragraphs)

            if ext in (".txt", ".md"):
                with open(file_path, "r", encoding="utf-8") as fh:
                    return fh.read()
        except Exception as exc:
            logger.error("Text extraction failed", extra={"path": file_path, "error": str(exc)})
            return None

        logger.warning("Unsupported file type", extra={"extension": file_extension})
        return None

    @staticmethod
    def _split_text_into_chunks(
        text: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> List[Dict[str, Any]]:
        """Split *text* into overlapping chunks using RecursiveCharacterTextSplitter."""
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""],
        )
        chunks = splitter.split_text(text)
        return [
            {"chunk_id": str(uuid.uuid4()), "text": chunk, "index": i}
            for i, chunk in enumerate(chunks)
        ]

    @staticmethod
    def _embed_chunks(document_id: str, chunks: List[Dict[str, Any]]) -> None:
        """Store chunks in ChromaDB with their embeddings."""
        collection = _get_chroma_collection()
        ids = [chunk["chunk_id"] for chunk in chunks]
        documents = [chunk["text"] for chunk in chunks]
        metadatas = [
            {"document_id": document_id, "chunk_index": chunk["index"]}
            for chunk in chunks
        ]
        collection.add(ids=ids, documents=documents, metadatas=metadatas)

    @staticmethod
    def _delete_chunks(document_id: str) -> None:
        """Remove all chunks belonging to *document_id* from ChromaDB."""
        collection = _get_chroma_collection()
        collection.delete(where={"document_id": document_id})

    @staticmethod
    def _search_chunks(
        query: str,
        document_ids: Optional[List[str]] = None,
        n_results: int = 5,
    ) -> dict:
        """Query ChromaDB for chunks relevant to *query*."""
        collection = _get_chroma_collection()
        where = None
        if document_ids:
            where = {"document_id": {"$in": document_ids}}
        return collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where,
        )

    @staticmethod
    def _build_context(search_results: dict) -> str:
        """Flatten ChromaDB search results into a single context string."""
        context_parts = []
        for i, doc in enumerate(search_results.get("documents", [[]])[0]):
            context_parts.append(f"Source {i + 1}:\n{doc}\n")
        return "\n".join(context_parts)

    @staticmethod
    def _build_prompt(query: str, context: str) -> str:
        """Build a RAG prompt with context."""
        return (
            "You are a helpful AI assistant. Use the following context to answer "
            "the user's question.\n"
            "If you don't know the answer, just say you don't know. "
            "Don't make up information.\n"
            "Always cite your sources when answering.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {query}\n\n"
            "Answer:"
        )