# app/routes/chat_routes.py
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.controllers.chat_controller import ChatController
from app.core.dependencies import get_current_user
from app.core.rate_limiter import RateLimiter
from app.db.session import get_db, get_session_factory
from app.models.user import UserModel
from app.schemas.chat import (
    ChatMessageCreate,
    ChatMessageResponse,
    ChatSessionCreate,
    ChatSessionDetailResponse,
    ChatSessionResponse,
    ToolApprovalRequest,
)
from app.services.chat_cache_service import ChatCacheService
from app.services.chat_service import ChatService
from app.services.chat_stream_service import ChatStreamService

router = APIRouter(prefix="/chats", tags=["Chat"])


def get_chat_cache_service() -> ChatCacheService:
    return ChatCacheService()


def get_chat_controller(
    db: AsyncSession = Depends(get_db),
    cache_service: ChatCacheService = Depends(get_chat_cache_service),
) -> ChatController:
    return ChatController(ChatService(db, cache_service=cache_service))


@router.post(
    "",
    response_model=ChatSessionResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(RateLimiter(max_requests=30, window_seconds=60, scope="chat:create"))
    ],
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
    response_model=list[ChatSessionResponse],
    dependencies=[
        Depends(RateLimiter(max_requests=60, window_seconds=60, scope="chat:list"))
    ],
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
    response_model=list[ChatMessageResponse],
)
async def get_chat_messages(
    session_id: uuid.UUID,
    current_user: UserModel = Depends(get_current_user),
    controller: ChatController = Depends(get_chat_controller),
):
    """Returns message history for a specific session."""
    return await controller.get_messages(session_id, current_user.id)


def get_chat_stream_service(
    session_factory=Depends(get_session_factory),
    cache_service: ChatCacheService = Depends(get_chat_cache_service),
) -> ChatStreamService:
    return ChatStreamService(
        session_factory=session_factory, cache_service=cache_service
    )


@router.post(
    "/{session_id}/stream",
    dependencies=[
        Depends(RateLimiter(max_requests=20, window_seconds=60, scope="chat:stream"))
    ],
)
async def stream_chat_response(
    session_id: uuid.UUID,
    message_in: ChatMessageCreate,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    stream_service: ChatStreamService = Depends(get_chat_stream_service),
):
    """
    Real-time Server-Sent Events (SSE) token streaming endpoint.
    Streams model response chunks and persists messages to PostgreSQL.
    """
    # Verify session ownership prior to establishing the stream
    chat_service = ChatService(db)
    session = await chat_service.get_session(session_id, current_user.id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found.",
        )

    generator = stream_service.stream_chat(
        session_id=session_id,
        user_id=current_user.id,
        user_content=message_in.content,
    )
    return EventSourceResponse(generator)


@router.post(
    "/{session_id}/tool-calls/approval",
    dependencies=[
        Depends(
            RateLimiter(max_requests=30, window_seconds=60, scope="chat:tool-approval")
        )
    ],
)
async def handle_tool_approval(
    session_id: uuid.UUID,
    approval_in: ToolApprovalRequest,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    stream_service: ChatStreamService = Depends(get_chat_stream_service),
):
    """
    Submits human approval or rejection for a pending agent tool call.
    Streams tool execution result and LLM followup response chunks.
    """
    chat_service = ChatService(db)
    session = await chat_service.get_session(session_id, current_user.id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found.",
        )

    generator = stream_service.stream_tool_approval(
        session_id=session_id,
        user_id=current_user.id,
        tool_call_id=approval_in.tool_call_id,
        approved=approval_in.approved,
        message_id=approval_in.message_id,
    )
    return EventSourceResponse(generator)
