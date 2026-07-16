"""
Settings Module.

System-wide and user-specific settings management with CRUD API.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, FastAPI, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select

from app.auth.dependencies import get_current_user
from app.core.container import Container
from app.core.database import get_database

logger = logging.getLogger("app.settings")

module_info = type("ModuleInfo", (), {"name": "settings"})

PACKAGE_NAME = __name__
API_PREFIX = "/api/v1/settings"


def register(app: FastAPI, container: Container) -> None:
    """Register settings module routes."""
    router = APIRouter(prefix=API_PREFIX, tags=["settings"])

    # ------------------------------------------------------------------ #
    # System Settings
    # ------------------------------------------------------------------ #

    @router.get("/system", summary="Get all system settings")
    async def get_system_settings():
        """Retrieve all system settings as key-value pairs."""
        from app.settings.models import SystemSetting
        db = get_database()
        async with db.session() as session:
            result = await session.execute(select(SystemSetting))
            settings_raw = result.scalars().all()
            return {"success": True, "settings": {s.key: s.value for s in settings_raw}}

    @router.get("/system/{key}", summary="Get a single system setting by key")
    async def get_system_setting(key: str):
        """Retrieve a single system setting by its key."""
        from app.settings.models import SystemSetting
        db = get_database()
        async with db.session() as session:
            result = await session.execute(
                select(SystemSetting).where(SystemSetting.key == key)
            )
            setting = result.scalar_one_or_none()
            if not setting:
                raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")
            return {
                "success": True,
                "setting": {
                    "key": setting.key,
                    "value": setting.value,
                    "description": setting.description,
                    "is_public": setting.is_public,
                },
            }

    @router.put("/system/{key}", summary="Create or update a system setting")
    async def upsert_system_setting(key: str, data: Dict[str, Any]):
        """Create or update a system setting (upsert)."""
        from app.settings.models import SystemSetting
        db = get_database()
        async with db.session() as session:
            result = await session.execute(
                select(SystemSetting).where(SystemSetting.key == key)
            )
            setting = result.scalar_one_or_none()
            if setting:
                setting.value = str(data.get("value", setting.value))
                if "description" in data:
                    setting.description = data["description"]
                if "is_public" in data:
                    setting.is_public = bool(data["is_public"])
            else:
                setting = SystemSetting(
                    key=key,
                    value=str(data.get("value", "")),
                    description=data.get("description"),
                    is_public=bool(data.get("is_public", False)),
                )
            session.add(setting)
        return {"success": True, "message": f"Setting '{key}' saved"}

    @router.delete("/system/{key}", summary="Delete a system setting")
    async def delete_system_setting(key: str):
        """Delete a system setting by its key."""
        from app.settings.models import SystemSetting
        db = get_database()
        async with db.session() as session:
            result = await session.execute(
                select(SystemSetting).where(SystemSetting.key == key)
            )
            setting = result.scalar_one_or_none()
            if not setting:
                raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")
            await session.delete(setting)
        return {"success": True, "message": f"Setting '{key}' deleted"}

    # ------------------------------------------------------------------ #
    # User Settings
    # ------------------------------------------------------------------ #

    @router.get("/user/me", summary="Get current user settings")
    async def get_user_settings(current_user: Dict[str, Any] = Depends(get_current_user)):
        """Retrieve all settings for the authenticated user."""
        from app.settings.models import UserSetting
        db = get_database()
        async with db.session() as session:
            result = await session.execute(
                select(UserSetting).where(UserSetting.user_id == current_user["id"])
            )
            user_settings_raw = result.scalars().all()
            return {
                "success": True,
                "settings": {s.key: s.value for s in user_settings_raw},
            }

    @router.put("/user/me/{key}", summary="Set a user setting")
    async def set_user_setting(
        key: str,
        data: Dict[str, Any],
        current_user: Dict[str, Any] = Depends(get_current_user),
    ):
        """Create or update a user setting."""
        from app.settings.models import UserSetting
        db = get_database()
        async with db.session() as session:
            result = await session.execute(
                select(UserSetting).where(
                    UserSetting.user_id == current_user["id"],
                    UserSetting.key == key,
                )
            )
            setting = result.scalar_one_or_none()
            if setting:
                setting.value = str(data.get("value", setting.value))
            else:
                setting = UserSetting(
                    user_id=current_user["id"],
                    key=key,
                    value=str(data.get("value", "")),
                )
            session.add(setting)
        return {"success": True, "message": f"Setting '{key}' saved"}

    @router.delete("/user/me/{key}", summary="Delete a user setting")
    async def delete_user_setting(
        key: str,
        current_user: Dict[str, Any] = Depends(get_current_user),
    ):
        """Delete a user setting by key."""
        from app.settings.models import UserSetting
        db = get_database()
        async with db.session() as session:
            result = await session.execute(
                select(UserSetting).where(
                    UserSetting.user_id == current_user["id"],
                    UserSetting.key == key,
                )
            )
            setting = result.scalar_one_or_none()
            if not setting:
                raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")
            await session.delete(setting)
        return {"success": True, "message": f"Setting '{key}' deleted"}

    app.include_router(router)