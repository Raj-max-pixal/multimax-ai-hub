"""
Settings Domain Models.

System-wide key-value settings and per-user settings.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, DateTime, Index, ForeignKey, Boolean

from app.core.database import Base


class SystemSetting(Base):
    """System-wide configuration setting (key-value store)."""

    __tablename__ = "system_settings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    key = Column(String(255), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=False, default="")
    description = Column(Text, nullable=True)
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("idx_system_setting_key", "key"),
    )


class UserSetting(Base):
    """Per-user configuration setting."""

    __tablename__ = "user_settings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    key = Column(String(255), nullable=False)
    value = Column(Text, nullable=False, default="")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("idx_user_setting_user_key", "user_id", "key", unique=True),
    )