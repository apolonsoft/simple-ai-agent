# app/routes/chat_routes.py
import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.core.rate_limiter import RateLimiter
from app.models.user import UserModel
from app.services.chat_service import ChatService
from app.controllers.chat_controller import ChatController
from app.schemas.chat import (
    ChatSessionCreate,
    ChatSessionResponse,
    ChatSessionDetailResponse,
    ChatMessageResponse,
)

router = APIRouter(prefix="/chats", tags=["Chat"])


def get_chat_controller(db: AsyncSession = Depends(get_db)) -> ChatController:
    return ChatController(ChatService(db))


@router.post(
    "",
    response_model=ChatSessionResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RateLimiter(max_requests=30, window_seconds=60, scope="chat:create"))],
)
async def create_chat_session(
    session_in: ChatSessionCreate,
    current_user: UserModel = Depends(get_current_user),
    controller: ChatController = Depends(get_chat_controller),
):
    """Creates a new conversation thread for the authenticated user."""
    return await controller.create_session(current_user.id, session_in)


@router.get(
    "",
    response_model=List[ChatSessionResponse],
    dependencies=[Depends(RateLimiter(max_requests=60, window_seconds=60, scope="chat:list"))],
)
async def list_chat_sessions(
    current_user: UserModel = Depends(get_current_user),
    controller: ChatController = Depends(get_chat_controller),
):
    """Returns all chat threads belonging to the authenticated user."""
    return await controller.list_sessions(current_user.id)


@router.get(
    "/{session_id}",
    response_model=ChatSessionDetailResponse,
)
async def get_chat_session(
    session_id: uuid.UUID,
    current_user: UserModel = Depends(get_current_user),
    controller: ChatController = Depends(get_chat_controller),
):
    """Retrieves session metadata and messages if owned by the user."""
    return await controller.get_session(session_id, current_user.id)


@router.delete(
    "/{session_id}",
    status_code=status.HTTP_200_OK,
)
async def delete_chat_session(
    session_id: uuid.UUID,
    current_user: UserModel = Depends(get_current_user),
    controller: ChatController = Depends(get_chat_controller),
):
    """Deletes a chat session and all cascading messages."""
    return await controller.delete_session(session_id, current_user.id)


@router.get(
    "/{session_id}/messages",
    response_model=List[ChatMessageResponse],
)
async def get_chat_messages(
    session_id: uuid.UUID,
    current_user: UserModel = Depends(get_current_user),
    controller: ChatController = Depends(get_chat_controller),
):
    """Returns message history for a specific session."""
    return await controller.get_messages(session_id, current_user.id)
