"""
Storage Module — REST API Endpoints.

Provides file upload, download, listing, and deletion endpoints.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from fastapi.responses import FileResponse

from app.storage.dependencies import get_current_user_id, get_storage_service
from app.storage.schemas import StoredFileListResponse, StoredFileResponse, StorageInfoResponse
from app.storage.service import StorageService

router = APIRouter(prefix="/api/v1/storage", tags=["storage"])


@router.post("/upload", response_model=StoredFileResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    workspace_id: Optional[int] = Form(None),
    is_public: bool = Form(False),
    user_id: int = Depends(get_current_user_id),
    storage: StorageService = Depends(get_storage_service),
) -> StoredFileResponse:
    """Upload a file for the authenticated user."""
    content = await file.read()
    file_size = len(content)

    file.file.seek(0)

    record = await storage.upload_file(
        file_obj=file.file,
        original_filename=file.filename or "unnamed",
        content_type=file.content_type,
        file_size=file_size,
        user_id=user_id,
        workspace_id=workspace_id,
        is_public=is_public,
    )

    return StoredFileResponse.model_validate(record)


@router.get("/files", response_model=StoredFileListResponse)
async def list_files(
    page: int = 1,
    page_size: int = 20,
    workspace_id: Optional[int] = None,
    user_id: int = Depends(get_current_user_id),
    storage: StorageService = Depends(get_storage_service),
) -> StoredFileListResponse:
    """List the authenticated user's stored files."""
    items, total = await storage.list_files(
        user_id,
        workspace_id=workspace_id,
        page=page,
        page_size=page_size,
    )

    return StoredFileListResponse(
        items=[StoredFileResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/files/{file_id}", response_model=StoredFileResponse)
async def get_file(
    file_id: str,
    storage: StorageService = Depends(get_storage_service),
) -> StoredFileResponse:
    """Get metadata for a specific file."""
    record = await storage.get_file(file_id)
    return StoredFileResponse.model_validate(record)


@router.get("/files/{file_id}/download")
async def download_file(
    file_id: str,
    storage: StorageService = Depends(get_storage_service),
) -> FileResponse:
    """Download a file by its ID."""
    file_path = await storage.get_file_path(file_id)
    record = await storage.get_file(file_id)
    return FileResponse(
        path=file_path,
        filename=record.original_filename,
        media_type=record.content_type or "application/octet-stream",
    )


@router.delete("/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: str,
    storage: StorageService = Depends(get_storage_service),
) -> None:
    """Delete a file and its record."""
    await storage.delete_file(file_id)


@router.get("/info", response_model=StorageInfoResponse)
async def storage_info(
    user_id: int = Depends(get_current_user_id),
    storage: StorageService = Depends(get_storage_service),
) -> StorageInfoResponse:
    """Get storage usage summary for the authenticated user."""
    info = await storage.get_storage_info(user_id)
    return StorageInfoResponse(**info)


__all__ = [
    "router",
]