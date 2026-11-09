# app/controllers/chat_controller.py
import uuid

from fastapi import HTTPException, status

from app.schemas.chat import (
    ChatMessageResponse,
    ChatSessionCreate,
    ChatSessionDetailResponse,
    ChatSessionResponse,
)
from app.services.chat_service import ChatService


class ChatController:
    def __init__(self, service: ChatService):
        self.service = service

    async def create_session(
        self,
        user_id: uuid.UUID,
        session_in: ChatSessionCreate,
    ) -> ChatSessionResponse:
        session = await self.service.create_session(
            user_id=user_id,
            title=session_in.title,
        )
        return ChatSessionResponse.model_validate(session)

    async def list_sessions(
        self,
        user_id: uuid.UUID,
    ) -> list[ChatSessionResponse]:
        sessions = await self.service.list_user_sessions(user_id)
        return [ChatSessionResponse.model_validate(s) for s in sessions]

    async def get_session(
        self,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> ChatSessionDetailResponse:
        session = await self.service.get_session(session_id, user_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found.",
            )
        return ChatSessionDetailResponse.model_validate(session)

    async def delete_session(
        self,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> dict:
        deleted = await self.service.delete_session(session_id, user_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found.",
            )
        return {"status": "success", "message": "Chat session deleted successfully."}

    async def get_messages(
        self,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> list[ChatMessageResponse]:
        messages = await self.service.get_messages(session_id, user_id)
        if messages is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found.",
            )
        return [ChatMessageResponse.model_validate(m) for m in messages]
