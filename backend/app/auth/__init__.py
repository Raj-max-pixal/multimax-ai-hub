"""
Auth Module.

Handles user authentication, registration, session management,
JWT tokens, and authorization. Follows the domain module pattern
for automatic discovery and registration by the ModuleLoader.
"""

from __future__ import annotations

from typing import Any

from app.core.module_loader import ModuleInfo
from app.auth.models import User, UserRole, RefreshToken
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
from app.auth.api import router

module_info = ModuleInfo(
    name="auth",
    package="app.auth",
    description="User authentication and authorization",
    version="0.1.0",
    dependencies=["core"],
    enabled=True,
)


def register(app: Any, container: Any) -> None:
    """Register the auth module with the FastAPI application.

    Called by the ModuleLoader during application startup.
    """
    from app.auth.api import router as auth_router
    from app.auth.service import AuthService as AuthServiceImpl

    # Include the auth API router
    app.include_router(auth_router)

    # Register auth service as a singleton in the DI container
    container.register_singleton(AuthServiceImpl, AuthServiceImpl())


__all__ = [
    "User",
    "UserRole",
    "RefreshToken",
    "AuthService",
    "router",
    "module_info",
    "register",
    # Schemas
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "TokenResponse",
    "RefreshRequest",
    "UserUpdate",
    "PasswordChange",
]