"""
Auth Dependencies.

FastAPI dependency injection for authentication and authorization.
Provides reusable dependencies for:
- get_current_user: Require valid access token
- get_current_admin_user: Require admin role
- get_optional_user: Optionally get user info (for public endpoints)
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.auth.service import _decode_token
from app.auth.service import AuthService
from app.core.container import get_container

# Bearer token scheme — extracts "Authorization: Bearer <token>" header
_bearer_scheme = HTTPBearer(
    auto_error=False,  # We handle errors manually for optional auth
)


def _get_auth_service() -> AuthService:
    """Resolve AuthService from the DI container instead of direct construction."""
    container = get_container()
    return container.resolve(AuthService)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    auth_service: AuthService = Depends(_get_auth_service),
) -> Dict[str, Any]:
    """Require a valid access token.

    Returns:
        User dict from the database.

    Raises:
        HTTPException 401: If token is missing, invalid, or expired.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = _decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    user = await auth_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.get("is_active", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    return user


async def get_current_admin_user(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """Require admin role.

    Raises:
        HTTPException 403: If user is not an admin.
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
    auth_service: AuthService = Depends(_get_auth_service),
) -> Optional[Dict[str, Any]]:
    """Optionally resolve the current user.

    Returns None if no valid token is provided, rather than raising an error.
    Useful for endpoints that change behavior based on auth status.
    """
    if not credentials:
        return None

    payload = _decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    user = await auth_service.get_user_by_id(user_id)
    if not user or not user.get("is_active", False):
        return None

    return user


async def get_current_user_id(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> str:
    """Shorthand dependency that just returns the user ID string.

    Useful for endpoints that only need the user ID.
    Compatible with existing workspace stubs.
    """
    return current_user["id"]