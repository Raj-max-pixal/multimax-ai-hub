"""
Chat Service.

Business logic layer for chat operations.
Sits between the repository layer and future REST APIs.
Follows the same service pattern as workspace/service.py.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from app.chat.models import ChatSession, Message, MessageRole
from app.chat.repositories import (
    ChatSessionRepository,
    MessageRepository,
    AttachmentRepository,
)
from app.chat.schemas import (
    ChatSessionResponse,
    CreateChatSessionResponse,
    MessageResponse,
)
from app.core.exceptions import NotFoundError, ValidationError
from app.core.logger import get_logger

logger = get_logger("app.chat.service")


class ChatService:
    """Service for chat operations.

    Encapsulates business logic and validation.
    Does NOT know about HTTP or FastAPI.
    Injected via constructor for testability and DI compatibility.
    """

    def __init__(
        self,
        session_repo: ChatSessionRepository,
        message_repo: MessageRepository,
        attachment_repo: AttachmentRepository,
    ) -> None:
        self._session_repo = session_repo
        self._message_repo = message_repo
        self._attachment_repo = attachment_repo

    # ------------------------------------------------------------------ #
    # Session Operations
    # ------------------------------------------------------------------ #

    async def create_session(
        self,
        workspace_id: str,
        title: str = "New Chat",
        created_by: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CreateChatSessionResponse:
        """Create a new chat session.

        Args:
            workspace_id: The parent workspace ID.
            title: Display title (will be trimmed).
            created_by: User ID of the session creator.
            metadata: Optional metadata dictionary.

        Returns:
            CreateChatSessionResponse with session details.

        Raises:
            ValidationError: If workspace_id or created_by is missing.
        """
        if not workspace_id or not workspace_id.strip():
            raise ValidationError("workspace_id is required")

        # Validate session creation
        title_clean = title.strip() if title else "New Chat"
        if not title_clean:
            title_clean = "New Chat"

        created_by_clean = created_by.strip() if created_by else ""
        if not created_by_clean:
            raise ValidationError("created_by is required")

        session = await self._session_repo.create(
            workspace_id=workspace_id.strip(),
            title=title_clean,
            created_by=created_by_clean,
            metadata_json=metadata or {},
        )

        logger.info(
            "Session created",
            extra={
                "session_id": session.id,
                "workspace_id": workspace_id,
                "created_by": created_by_clean,
            },
        )

        return CreateChatSessionResponse.from_orm_model(session)

    async def get_session(self, session_id: str) -> ChatSessionResponse:
        """Get a chat session by ID.

        Args:
            session_id: The session UUID.

        Returns:
            ChatSessionResponse with session details.

        Raises:
            NotFoundError: If session does not exist or is deleted.
        """
        session = await self._session_repo.get_by_id(session_id)
        if not session:
            raise NotFoundError(
                f"Chat session {session_id} not found or has been deleted"
            )

        return ChatSessionResponse.from_orm_model(session)

    async def list_sessions(
        self,
        workspace_id: str,
        include_deleted: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[ChatSessionResponse], int]:
        """List chat sessions in a workspace.

        Args:
            workspace_id: The workspace to list sessions for.
            include_deleted: Whether to include soft-deleted sessions.
            limit: Maximum results.
            offset: Pagination offset.

        Returns:
            Tuple of (list of session responses, total count).

        Raises:
            ValidationError: If workspace_id is missing.
        """
        if not workspace_id or not workspace_id.strip():
            raise ValidationError("workspace_id is required")

        sessions = await self._session_repo.list_by_workspace(
            workspace_id=workspace_id.strip(),
            include_deleted=include_deleted,
            limit=limit,
            offset=offset,
        )

        responses = [ChatSessionResponse.from_orm_model(s) for s in sessions]
        total = len(sessions)  # For now, total is what we got

        return responses, total

    async def rename_session(
        self, session_id: str, new_title: str
    ) -> ChatSessionResponse:
        """Rename a chat session.

        Args:
            session_id: The session UUID.
            new_title: The new title (will be trimmed).

        Returns:
            ChatSessionResponse with updated session details.

        Raises:
            NotFoundError: If session does not exist or is deleted.
            ValidationError: If title is empty after trimming.
        """
        title_clean = new_title.strip() if new_title else ""
        if not title_clean:
            raise ValidationError("Session title must not be empty")

        session = await self._session_repo.update_title(session_id, title_clean)
        if not session:
            raise NotFoundError(
                f"Chat session {session_id} not found or has been deleted — "
                f"cannot rename"
            )

        logger.info(
            "Session renamed",
            extra={
                "session_id": session_id,
                "new_title": title_clean,
            },
        )

        return ChatSessionResponse.from_orm_model(session)

    async def delete_session(self, session_id: str) -> None:
        """Soft-delete a chat session.

        Args:
            session_id: The session UUID.

        Raises:
            NotFoundError: If session does not exist or is already deleted.
        """
        deleted = await self._session_repo.soft_delete(session_id)
        if not deleted:
            raise NotFoundError(
                f"Chat session {session_id} not found or is already deleted"
            )

        logger.info(
            "Session deleted (soft)",
            extra={"session_id": session_id},
        )

    # ------------------------------------------------------------------ #
    # Message Operations
    # ------------------------------------------------------------------ #

    async def create_message(
        self,
        session_id: str,
        role: str,
        content: str,
        model: Optional[str] = None,
        tokens: Optional[int] = None,
    ) -> MessageResponse:
        """Create a new message in a session.

        Validates that the session exists and is not deleted.
        Trims content whitespace.
        Rejects empty content after trimming.

        Args:
            session_id: The parent session UUID.
            role: Message role (user, assistant, system).
            content: Message content (will be trimmed).
            model: Optional model identifier.
            tokens: Optional token count.

        Returns:
            MessageResponse with the created message details.

        Raises:
            ValidationError: If content is empty after trimming.
            NotFoundError: If the parent session does not exist or is deleted.
        """
        # Validate content
        content_clean = content.strip() if content else ""
        if not content_clean:
            raise ValidationError("Message content must not be empty")

        # Validate role
        try:
            role_enum = MessageRole(role)
        except ValueError:
            raise ValidationError(
                f"Invalid role '{role}'. Must be one of: user, assistant, system"
            )

        # Verify session exists and is not deleted
        session = await self._session_repo.get_by_id(session_id)
        if not session:
            raise NotFoundError(
                f"Cannot create message — session {session_id} not found "
                f"or has been deleted"
            )

        # Create the message (repository also updates session.updated_at)
        message = await self._message_repo.create(
            session_id=session_id,
            role=role_enum,
            content=content_clean,
            model=model.strip() if model else None,
            tokens=tokens,
        )

        logger.info(
            "Message created",
            extra={
                "message_id": message.id,
                "session_id": session_id,
                "role": role,
            },
        )

        return MessageResponse.from_orm_model(message)

    async def get_messages(
        self,
        session_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[MessageResponse], int]:
        """Get messages in a session.

        Args:
            session_id: The session UUID.
            limit: Maximum results.
            offset: Pagination offset.

        Returns:
            Tuple of (list of message responses, total count).

        Raises:
            NotFoundError: If session does not exist or is deleted.
        """
        # Verify session exists and is not deleted
        session = await self._session_repo.get_by_id(session_id)
        if not session:
            raise NotFoundError(
                f"Chat session {session_id} not found or has been deleted"
            )

        messages = await self._message_repo.list_by_session(
            session_id=session_id,
            limit=limit,
            offset=offset,
        )

        responses = [MessageResponse.from_orm_model(m) for m in messages]
        total = len(messages)

        return responses, total