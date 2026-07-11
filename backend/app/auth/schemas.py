"""
Auth Pydantic Schemas.

Request/response schemas for all auth endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    """Registration request schema."""
    email: str = Field(..., max_length=255)
    username: str = Field(..., min_length=3, max_length=100, pattern=r"^[a-zA-Z0-9_-]+$")
    password: str = Field(..., min_length=8, max_length=128)
    display_name: Optional[str] = Field(None, max_length=255)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Invalid email address")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserLogin(BaseModel):
    """Login request schema."""
    username: str = Field(..., min_length=1, description="Username or email")
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    """JWT token response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Dict[str, Any]


class RefreshRequest(BaseModel):
    """Refresh token request schema."""
    refresh_token: str = Field(..., min_length=1)


class UserResponse(BaseModel):
    """User response schema (public)."""
    id: str
    email: str
    username: str
    display_name: str
    role: str
    is_active: bool
    is_verified: bool
    avatar_url: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class UserUpdate(BaseModel):
    """User profile update schema."""
    display_name: Optional[str] = Field(None, max_length=255)
    avatar_url: Optional[str] = Field(None, max_length=512)
    preferences: Optional[Dict[str, Any]] = None


class PasswordChange(BaseModel):
    """Password change request schema."""
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v