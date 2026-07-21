"""
Chat module exceptions.

Defines domain-specific exceptions for the chat module.
"""

from app.core.exceptions import MultimaxError, NotFoundError


class ChatNotFoundError(NotFoundError):
    """Raised when a chat session is not found."""

    def __init__(self, session_id: str) -> None:
        super().__init__(f"Chat session not found: {session_id}", detail={"session_id": session_id})


class MessageNotFoundError(NotFoundError):
    """Raised when a message is not found."""

    def __init__(self, message_id: str) -> None:
        super().__init__(f"Message not found: {message_id}", detail={"message_id": message_id})


__all__ = [
    "ChatNotFoundError",
    "MessageNotFoundError",
]