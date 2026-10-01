"""
Storage Module — FastAPI Dependencies.

Provides dependency injection for StorageService.
"""

from __future__ import annotations

from typing import Any, AsyncGenerator, Dict, Optional

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, get_optional_user
from app.core.database import get_db_session as get_session
from app.storage.service import StorageService


async def get_storage_service(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> AsyncGenerator[StorageService, None]:
    """Dependency that yields a StorageService instance."""
    yield StorageService(session=session)


async def get_current_user_id(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> str:
    """Return the ID resolved by the shared bearer-token auth dependency."""
    return current_user["id"]


async def get_optional_user_id(
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_user),
) -> Optional[str]:
    """Return the authenticated user ID when present, otherwise None."""
    return current_user["id"] if current_user else None


__all__ = [
    "get_storage_service",
    "get_current_user_id",
]
