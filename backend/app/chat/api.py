"""
 Chat REST API.

FastAPI router for chat operations.
Follows the same conventions as workspace/api.py.
Uses dependency injection for the service layer.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query, status

from app.chat.schemas import (
    ChatSessionListResponse,
    ChatSessionResponse,
    CreateChatSessionRequest,
    CreateChatSessionResponse,
    CreateMessageRequest,
    MessageListResponse,
    MessageResponse,
    RenameChatSessionRequest,
)
from app.chat.service import ChatService
from app.core.container import get_chat_service
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/chat", tags=["Chat"])


# ------------------------------------------------------------------ #
# Session Endpoints
# ------------------------------------------------------------------ #


@router.post(
    "/sessions",
    response_model=CreateChatSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new chat session",
)
async def create_session(
    request: CreateChatSessionRequest,
    chat_service: ChatService = Depends(get_chat_service),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> CreateChatSessionResponse:
    """Create a new chat session in a workspace.

    The authenticated user must be a member of the workspace.
    """
    return await chat_service.create_session(
        workspace_id=request.workspace_id,
        title=request.title,
        created_by=request.created_by or current_user.get("id", ""),
        metadata=request.metadata or {},
    )


@router.get(
    "/sessions/{session_id}",
    response_model=ChatSessionResponse,
    summary="Get a chat session by ID",
)
async def get_session(
    session_id: str,
    chat_service: ChatService = Depends(get_chat_service),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> ChatSessionResponse:
    """Get details of a specific chat session."""
    return await chat_service.get_session(session_id=session_id)


@router.get(
    "/workspaces/{workspace_id}/sessions",
    response_model=ChatSessionListResponse,
    summary="List chat sessions in a workspace",
)
async def list_sessions(
    workspace_id: str,
    include_deleted: bool = Query(False, description="Include soft-deleted sessions"),
    limit: int = Query(50, ge=1, le=200, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    chat_service: ChatService = Depends(get_chat_service),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> ChatSessionListResponse:
    """List all chat sessions in a workspace."""
    sessions, total = await chat_service.list_sessions(
        workspace_id=workspace_id,
        include_deleted=include_deleted,
        limit=limit,
        offset=offset,
    )
    return ChatSessionListResponse(sessions=sessions, total=total)


@router.patch(
    "/sessions/{session_id}",
    response_model=ChatSessionResponse,
    summary="Rename a chat session",
)
async def rename_session(
    session_id: str,
    request: RenameChatSessionRequest,
    chat_service: ChatService = Depends(get_chat_service),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> ChatSessionResponse:
    """Rename an existing chat session."""
    return await chat_service.rename_session(
        session_id=session_id,
        new_title=request.title,
    )


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete a chat session",
)
async def delete_session(
    session_id: str,
    chat_service: ChatService = Depends(get_chat_service),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> None:
    """Soft-delete a chat session and all its messages."""
    await chat_service.delete_session(session_id=session_id)


# ------------------------------------------------------------------ #
# Message Endpoints
# ------------------------------------------------------------------ #


@router.post(
    "/sessions/{session_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a message in a session",
)
async def create_message(
    session_id: str,
    request: CreateMessageRequest,
    chat_service: ChatService = Depends(get_chat_service),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> MessageResponse:
    """Add a new message to an existing chat session."""
    return await chat_service.create_message(
        session_id=session_id,
        role=request.role,
        content=request.content,
        model=request.model,
        tokens=request.tokens,
    )


@router.get(
    "/sessions/{session_id}/messages",
    response_model=MessageListResponse,
    summary="List messages in a session",
)
async def list_messages(
    session_id: str,
    limit: int = Query(100, ge=1, le=500, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    chat_service: ChatService = Depends(get_chat_service),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> MessageListResponse:
    """Get all messages in a chat session, ordered by creation time."""
    messages, total = await chat_service.get_messages(
        session_id=session_id,
        limit=limit,
        offset=offset,
    )
    return MessageListResponse(messages=messages, total=total)