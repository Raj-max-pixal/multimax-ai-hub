"""
Auth API Routes.

REST endpoints for authentication and user management.
All routes are prefixed with /api/auth.
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status, Body

from app.auth.schemas import (
    UserCreate,
    UserLogin,
    UserResponse,
    TokenResponse,
    RefreshRequest,
    UserUpdate,
    PasswordChange,
)
from app.auth.service import AuthService
from app.auth.dependencies import get_current_user, get_current_admin_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _user_to_response(user_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a user dict to a standardized response format."""
    return {
        "id": user_dict.get("id", ""),
        "email": user_dict.get("email", ""),
        "username": user_dict.get("username", ""),
        "display_name": user_dict.get("display_name", ""),
        "role": user_dict.get("role", "user"),
        "is_active": user_dict.get("is_active", True),
        "is_verified": user_dict.get("is_verified", False),
        "avatar_url": user_dict.get("avatar_url", ""),
        "created_at": user_dict.get("created_at"),
        "updated_at": user_dict.get("updated_at"),
    }


# ------------------------------------------------------------------ #
# Public Endpoints (no auth required)
# ------------------------------------------------------------------ #


@router.post(
    "/register",
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account. Email and username must be unique.",
)
async def register(
    data: UserCreate,
    auth_service: AuthService = Depends(lambda: AuthService()),
):
    """Register a new user account."""
    try:
        user = await auth_service.register(
            email=data.email,
            username=data.username,
            password=data.password,
            display_name=data.display_name,
        )
        return {"success": True, "message": "Registration successful", "user": _user_to_response(user)}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@router.post(
    "/login",
    response_model=Dict[str, Any],
    summary="Login",
    description="Authenticate with username/email and password. Returns JWT tokens.",
)
async def login(
    data: UserLogin,
    auth_service: AuthService = Depends(lambda: AuthService()),
):
    """Authenticate and get JWT tokens."""
    try:
        result = await auth_service.login(
            username=data.username,
            password=data.password,
        )
        return {
            "success": True,
            "access_token": result["access_token"],
            "refresh_token": result["refresh_token"],
            "token_type": result["token_type"],
            "expires_in": result["expires_in"],
            "user": _user_to_response(result["user"]),
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.post(
    "/refresh",
    response_model=Dict[str, Any],
    summary="Refresh access token",
    description="Exchange a valid refresh token for a new access token (token rotation).",
)
async def refresh(
    data: RefreshRequest,
    auth_service: AuthService = Depends(lambda: AuthService()),
):
    """Refresh an access token using a refresh token."""
    try:
        result = await auth_service.refresh_token(data.refresh_token)
        return {
            "success": True,
            "access_token": result["access_token"],
            "refresh_token": result["refresh_token"],
            "token_type": result["token_type"],
            "expires_in": result["expires_in"],
            "user": _user_to_response(result["user"]),
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Logout",
    description="Revoke a refresh token.",
)
async def logout(
    data: RefreshRequest,
    auth_service: AuthService = Depends(lambda: AuthService()),
):
    """Logout by revoking the refresh token."""
    await auth_service.logout(data.refresh_token)
    return {"success": True, "message": "Logged out successfully"}


@router.get(
    "/me",
    response_model=Dict[str, Any],
    summary="Get current user profile",
    description="Returns the authenticated user's profile.",
)
async def get_me(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Get the current authenticated user's profile."""
    return {
        "success": True,
        "user": _user_to_response(current_user),
    }


@router.patch(
    "/me",
    response_model=Dict[str, Any],
    summary="Update current user profile",
    description="Update display name, avatar URL, or preferences.",
)
async def update_me(
    data: UserUpdate,
    auth_service: AuthService = Depends(lambda: AuthService()),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Update the current user's profile."""
    update_dict = {}
    if data.display_name is not None:
        update_dict["display_name"] = data.display_name
    if data.avatar_url is not None:
        update_dict["avatar_url"] = data.avatar_url
    if data.preferences is not None:
        update_dict["preferences"] = data.preferences

    if not update_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )

    updated = await auth_service.update_user(current_user["id"], update_dict)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return {
        "success": True,
        "message": "Profile updated",
        "user": _user_to_response(updated),
    }


@router.post(
    "/me/change-password",
    response_model=Dict[str, Any],
    summary="Change password",
    description="Change the current user's password. Invalidates all refresh tokens.",
)
async def change_password(
    data: PasswordChange,
    auth_service: AuthService = Depends(lambda: AuthService()),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Change the current user's password."""
    success = await auth_service.change_password(
        current_user["id"],
        data.current_password,
        data.new_password,
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    return {"success": True, "message": "Password changed successfully"}


# ------------------------------------------------------------------ #
# Admin Endpoints (requires admin role)
# ------------------------------------------------------------------ #


@router.get(
    "/admin/users",
    response_model=Dict[str, Any],
    summary="List all users (admin only)",
    description="Get a paginated list of all users. Requires admin role.",
)
async def list_users(
    auth_service: AuthService = Depends(lambda: AuthService()),
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
):
    """List all users (admin only)."""
    from sqlalchemy import select, func
    from app.core.database import get_database

    db = get_database()
    async with db.session() as session:
        from app.auth.models import User
        result = await session.execute(
            select(User).order_by(User.created_at.desc()).limit(100)
        )
        users = [u.to_dict() for u in result.scalars().all()]

        count_result = await session.execute(select(func.count()).select_from(User))
        total = count_result.scalar() or 0

    return {
        "success": True,
        "users": [_user_to_response(u) for u in users],
        "total": total,
    }