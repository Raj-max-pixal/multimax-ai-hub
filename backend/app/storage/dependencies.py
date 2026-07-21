"""
Storage Module — FastAPI Dependencies.

Provides dependency injection for StorageService.
"""

from __future__ import annotations

from typing import AsyncGenerator

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session as get_session
from app.storage.service import StorageService


async def get_storage_service(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> AsyncGenerator[StorageService, None]:
    """Dependency that yields a StorageService instance."""
    yield StorageService(session=session)


async def get_current_user_id(request: Request) -> int:
    """Extract the authenticated user ID from the request state.

    Relies on auth middleware having set request.state.user_id.
    """
    user_id = getattr(request.state, "user_id", None)
    if user_id is None:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return user_id


__all__ = [
    "get_storage_service",
    "get_current_user_id",
]