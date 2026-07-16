"""
Settings Pydantic Schemas.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class SystemSettingCreate(BaseModel):
    """System setting creation schema."""
    key: str = Field(..., min_length=1, max_length=255)
    value: str = Field(..., max_length=5000)
    description: Optional[str] = None
    is_public: bool = False


class SystemSettingUpdate(BaseModel):
    """System setting update schema."""
    value: str = Field(..., max_length=5000)
    description: Optional[str] = None
    is_public: Optional[bool] = None


class UserSettingCreate(BaseModel):
    """User setting creation schema."""
    key: str = Field(..., min_length=1, max_length=255)
    value: str = Field(..., max_length=5000)


class SettingsResponse(BaseModel):
    """Generic settings response."""
    success: bool = True
    settings: Dict[str, Any]