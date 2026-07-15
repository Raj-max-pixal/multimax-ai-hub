"""
Document REST API.

FastAPI router for document upload, listing, retrieval, deletion,
and RAG-based chat with documents.  Follows the same conventions
as chat/api.py and uses dependency injection for the service layer.
"""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status

from app.document.dependencies import get_document_service
from app.document.exceptions import (
    DocumentNotFoundError,
    TextExtractionError,
)
from app.document.schemas import (
    DocumentChatRequest,
    DocumentListResponse,
    DocumentResponse,
    UploadResponse,
)
from app.document.service import DocumentService

router = APIRouter(prefix="/api/v1/documents", tags=["Documents"])


# ------------------------------------------------------------------ #
# Upload Endpoint
# ------------------------------------------------------------------ #


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload one or more document files",
)
async def upload_documents(
    files: List[UploadFile] = File(..., description="One or more files to upload and process"),
    doc_service: DocumentService = Depends(get_document_service),
) -> UploadResponse:
    """Upload and process one or more document files.

    For each file the server will:
    1. Save it to disk
    2. Extract text (PDF, DOCX, TXT, MD supported)
    3. Split text into overlapping chunks
    4. Generate embeddings and store them in ChromaDB
    5. Persist metadata

    Returns a list of ``DocumentResponse`` items describing the processed documents.
    """
    documents: List[DocumentResponse] = []

    for file in files:
        try:
            record = await doc_service.upload_document(file)
            documents.append(
                DocumentResponse(
                    id=record.id,
                    filename=record.filename,
                    saved_filename=record.saved_filename,
                    file_type=record.file_type,
                    file_size=record.file_size,
                    chunk_count=record.chunk_count,
                    status=record.status,
                )
            )
        except TextExtractionError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            )
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process file '{file.filename}': {exc}",
            )

    return UploadResponse(
        documents=documents,
        message=f"Successfully processed {len(documents)} document(s)",
    )


# ------------------------------------------------------------------ #
# List Endpoint
# ------------------------------------------------------------------ #


@router.get(
    "",
    response_model=DocumentListResponse,
    summary="List all documents",
)
async def list_documents(
    doc_service: DocumentService = Depends(get_document_service),
) -> DocumentListResponse:
    """Return metadata for all uploaded documents."""
    records = await doc_service.list_documents()
    return DocumentListResponse(
        documents=[
            DocumentResponse(
                id=r.id,
                filename=r.filename,
                saved_filename=r.saved_filename,
                file_type=r.file_type,
                file_size=r.file_size,
                chunk_count=r.chunk_count,
                status=r.status,
            )
            for r in records
        ]
    )


# ------------------------------------------------------------------ #
# Get Single Endpoint
# ------------------------------------------------------------------ #


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Get a single document by ID",
)
async def get_document(
    document_id: str,
    doc_service: DocumentService = Depends(get_document_service),
) -> DocumentResponse:
    """Return metadata for a specific document."""
    try:
        record = await doc_service.get_document(document_id)
        return DocumentResponse(
            id=record.id,
            filename=record.filename,
            saved_filename=record.saved_filename,
            file_type=record.file_type,
            file_size=record.file_size,
            chunk_count=record.chunk_count,
            status=record.status,
        )
    except DocumentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


# ------------------------------------------------------------------ #
# Delete Endpoint
# ------------------------------------------------------------------ #


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a document",
)
async def delete_document(
    document_id: str,
    doc_service: DocumentService = Depends(get_document_service),
) -> None:
    """Delete a document and its associated file + ChromaDB entries."""
    try:
        await doc_service.delete_document(document_id)
    except DocumentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


# ------------------------------------------------------------------ #
# RAG Chat Endpoint
# ------------------------------------------------------------------ #


@router.post(
    "/chat",
    summary="Chat with selected documents (RAG)",
)
async def chat_with_documents(
    request: DocumentChatRequest,
    doc_service: DocumentService = Depends(get_document_service),
):
    """Stream an LLM response grounded in the selected documents.

    Uses Ollama under the hood.  The response is streamed as
    Server-Sent Events (SSE).
    """
    from fastapi.responses import StreamingResponse

    streaming = doc_service.chat_with_documents(
        query=request.query,
        document_ids=request.document_ids,
        model=request.model or "phi3:latest",
    )
    return StreamingResponse(streaming, media_type="text/event-stream")