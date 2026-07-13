"""
Chat Module.

Provides chat session, message, and attachment data models and repositories.
This module implements only the database layer for chat functionality.
API and service layers will be added in later phases.
"""

from __future__ import annotations

from typing import Any

from app.core.module_loader import ModuleInfo
from app.chat.models import (
    ChatSession,
    Message,
    Attachment,
    MessageRole,
)
from app.chat.repositories import (
    ChatSessionRepository,
    MessageRepository,
    AttachmentRepository,
)

module_info = ModuleInfo(
    name="chat",
    package="app.chat",
    description="Chat session, message, and attachment management (database layer)",
    version="0.1.0",
    dependencies=["core", "workspace"],
    enabled=True,
)


def register(app: Any, container: Any) -> None:
    """Register the chat module with the FastAPI application.

    Called by the ModuleLoader during application startup.
    Phase 1 Step 1: Only registers repository classes in the DI container.
    """
    # Register chat repositories in the DI container
    container.register_singleton(ChatSessionRepository, ChatSessionRepository())
    container.register_singleton(MessageRepository, MessageRepository())
    container.register_singleton(AttachmentRepository, AttachmentRepository())

    # No API routers are registered in this step.
    # REST APIs will be added in Phase 1 Step 2.


__all__ = [
    "ChatSession",
    "Message",
    "Attachment",
    "MessageRole",
    "ChatSessionRepository",
    "MessageRepository",
    "AttachmentRepository",
    "module_info",
    "register",
]