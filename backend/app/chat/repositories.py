"""
Chat Repositories.

Provides CRUD operations for ChatSession, Message, and Attachment models.
Follows the repository pattern used elsewhere in the project.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy import select, delete, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.chat.models import ChatSession, Message, Attachment, MessageRole
from app.core.database import get_database
from app.core.logger import get_logger

logger = get_logger("app.chat.repositories")


class ChatSessionRepository:
    """Repository for ChatSession CRUD operations."""

    def __init__(self) -> None:
        self._db = get_database()

    async def create(
        self,
        workspace_id: str,
        title: str = "New Chat",
        created_by: Optional[str] = None,
        metadata_json: Optional[Dict[str, Any]] = None,
    ) -> ChatSession:
        """Create a new chat session.

        Args:
            workspace_id: The workspace this session belongs to.
            title: Display title for the session.
            created_by: User ID of the creator.
            metadata_json: Optional metadata dictionary.

        Returns:
            The newly created ChatSession instance.
        """
        async with self._db.session() as session:
            chat_session = ChatSession(
                id=str(uuid4()),
                workspace_id=workspace_id,
                title=title,
                created_by=created_by or "",
                metadata_json=metadata_json or {},
            )
            session.add(chat_session)
            await session.flush()
            await session.refresh(chat_session)
            logger.info(f"Chat session created: {chat_session.id}")
            return chat_session

    async def get_by_id(self, session_id: str) -> Optional[ChatSession]:
        """Get a chat session by ID (excluding soft-deleted).

        Args:
            session_id: The session UUID.

        Returns:
            ChatSession if found and not deleted, else None.
        """
        async with self._db.session() as session:
            result = await session.execute(
                select(ChatSession).where(
                    ChatSession.id == session_id,
                    ChatSession.deleted_at.is_(None),
                )
            )
            return result.scalar_one_or_none()

    async def list_by_workspace(
        self,
        workspace_id: str,
        include_deleted: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> List[ChatSession]:
        """List chat sessions in a workspace.

        Args:
            workspace_id: The workspace to list sessions for.
            include_deleted: Whether to include soft-deleted sessions.
            limit: Maximum number of results.
            offset: Pagination offset.

        Returns:
            List of ChatSession instances.
        """
        async with self._db.session() as session:
            query = select(ChatSession).where(
                ChatSession.workspace_id == workspace_id,
            )

            if not include_deleted:
                query = query.where(ChatSession.deleted_at.is_(None))

            query = query.order_by(ChatSession.updated_at.desc()).limit(limit).offset(offset)

            result = await session.execute(query)
            return list(result.scalars().all())

    async def update_title(self, session_id: str, title: str) -> Optional[ChatSession]:
        """Update the title of a chat session.

        Args:
            session_id: The session UUID.
            title: New title string.

        Returns:
            Updated ChatSession, or None if not found.
        """
        async with self._db.session() as session:
            result = await session.execute(
                select(ChatSession).where(
                    ChatSession.id == session_id,
                    ChatSession.deleted_at.is_(None),
                )
            )
            chat_session = result.scalar_one_or_none()
            if not chat_session:
                return None

            chat_session.title = title
            session.add(chat_session)
            await session.flush()
            await session.refresh(chat_session)
            logger.info(f"Chat session title updated: {session_id}")
            return chat_session

    async def soft_delete(self, session_id: str) -> bool:
        """Soft-delete a chat session by setting deleted_at.

        Args:
            session_id: The session UUID.

        Returns:
            True if deleted, False if not found.
        """
        async with self._db.session() as session:
            result = await session.execute(
                select(ChatSession).where(
                    ChatSession.id == session_id,
                    ChatSession.deleted_at.is_(None),
                )
            )
            chat_session = result.scalar_one_or_none()
            if not chat_session:
                return False

            chat_session.deleted_at = datetime.now(timezone.utc)
            session.add(chat_session)
            logger.info(f"Chat session soft-deleted: {session_id}")
            return True


class MessageRepository:
    """Repository for Message CRUD operations."""

    def __init__(self) -> None:
        self._db = get_database()

    async def create(
        self,
        session_id: str,
        role: MessageRole,
        content: str,
        model: Optional[str] = None,
        tokens: Optional[int] = None,
    ) -> Message:
        """Create a new message in a chat session.

        Args:
            session_id: The parent chat session UUID.
            role: Message role (user, assistant, system).
            content: Message content text.
            model: Model identifier used for generation.
            tokens: Token count if available.

        Returns:
            The newly created Message instance.
        """
        async with self._db.session() as session:
            message = Message(
                id=str(uuid4()),
                session_id=session_id,
                role=role,
                content=content,
                model=model or "",
                tokens=tokens,
            )
            session.add(message)
            await session.flush()
            await session.refresh(message)

            # Update parent session's updated_at timestamp
            await session.execute(
                update(ChatSession)
                .where(ChatSession.id == session_id)
                .values(updated_at=datetime.now(timezone.utc))
            )

            logger.debug(f"Message created: {message.id} in session {session_id}")
            return message

    async def list_by_session(
        self,
        session_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Message]:
        """List messages in a chat session ordered by creation time.

        Args:
            session_id: The session UUID.
            limit: Maximum number of results.
            offset: Pagination offset.

        Returns:
            List of Message instances in chronological order.
        """
        async with self._db.session() as session:
            query = (
                select(Message)
                .where(Message.session_id == session_id)
                .order_by(Message.created_at.asc())
                .limit(limit)
                .offset(offset)
            )
            result = await session.execute(query)
            return list(result.scalars().all())

    async def delete_by_session(self, session_id: str) -> int:
        """Permanently delete all messages in a session.

        Args:
            session_id: The session UUID.

        Returns:
            Number of deleted messages.
        """
        async with self._db.session() as session:
            result = await session.execute(
                delete(Message).where(Message.session_id == session_id)
            )
            deleted_count = result.rowcount
            if deleted_count:
                logger.info(f"Deleted {deleted_count} messages from session {session_id}")
            return deleted_count


class AttachmentRepository:
    """Repository for Attachment CRUD operations."""

    def __init__(self) -> None:
        self._db = get_database()

    async def create(
        self,
        message_id: str,
        filename: str,
        path: str,
        file_type: str = "application/octet-stream",
        file_size: int = 0,
    ) -> Attachment:
        """Create a new attachment for a message.

        Args:
            message_id: The parent message UUID.
            filename: Original filename.
            path: Storage path for the file.
            file_type: MIME type of the file.
            file_size: Size in bytes.

        Returns:
            The newly created Attachment instance.
        """
        async with self._db.session() as session:
            attachment = Attachment(
                id=str(uuid4()),
                message_id=message_id,
                filename=filename,
                file_type=file_type,
                file_size=file_size,
                path=path,
            )
            session.add(attachment)
            await session.flush()
            await session.refresh(attachment)
            logger.debug(f"Attachment created: {attachment.id} for message {message_id}")
            return attachment

    async def list_by_message(self, message_id: str) -> List[Attachment]:
        """List all attachments for a message.

        Args:
            message_id: The message UUID.

        Returns:
            List of Attachment instances.
        """
        async with self._db.session() as session:
            query = select(Attachment).where(
                Attachment.message_id == message_id
            ).order_by(Attachment.created_at.asc())
            result = await session.execute(query)
            return list(result.scalars().all())