"""Repository-aware coding agent module."""

from __future__ import annotations

from typing import Any

from app.core.module_loader import ModuleInfo
from app.coding.api import router

module_info = ModuleInfo(
    name="coding-agent",
    package="app.coding",
    description="Authenticated project files and reviewed AI patches",
    version="0.1.0",
    dependencies=["auth", "workspace"],
    enabled=True,
)


def register(app: Any, container: Any) -> None:
    app.include_router(router)


__all__ = ["router", "module_info", "register"]
