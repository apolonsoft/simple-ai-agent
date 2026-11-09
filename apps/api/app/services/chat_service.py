# app/services/chat_service.py
import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import ChatMessageModel, ChatSessionModel

if TYPE_CHECKING:
    from app.services.chat_cache_service import ChatCacheService


class ChatService:
    def __init__(
        self, db: AsyncSession, cache_service: Optional["ChatCacheService"] = None
    ):
        self.db = db
        self.cache_service = cache_service

    async def create_session(
        self,
        user_id: uuid.UUID,
        title: str | None = "New Chat",
    ) -> ChatSessionModel:
        session = ChatSessionModel(
            id=uuid.uuid4(),
            user_id=user_id,
            title=title or "New Chat",
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def list_user_sessions(
        self,
        user_id: uuid.UUID,
    ) -> list[ChatSessionModel]:
        stmt = (
            select(ChatSessionModel)
            .where(ChatSessionModel.user_id == user_id)
            .order_by(ChatSessionModel.created_at.desc())
        )
        result = await self.db.scalars(stmt)
        return list(result.all())

    async def get_session(
        self,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> ChatSessionModel | None:
        """Fetches a session strictly verifying user ownership."""
        stmt = select(ChatSessionModel).where(
            ChatSessionModel.id == session_id,
            ChatSessionModel.user_id == user_id,
        )
        result = await self.db.scalars(stmt)
        return result.first()

    async def delete_session(
        self,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> bool:
        session = await self.get_session(session_id, user_id)
        if not session:
            return False
        await self.db.delete(session)
        await self.db.commit()

        if self.cache_service is not None:
            await self.cache_service.invalidate(session_id)

        return True

    async def add_message(
        self,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
        role: str,
        content: str,
        tokens: int | None = None,
    ) -> ChatMessageModel | None:
        """Adds a message to a session after confirming user ownership."""
        session = await self.get_session(session_id, user_id)
        if not session:
            return None

        message = ChatMessageModel(
            id=uuid.uuid4(),
            session_id=session_id,
            role=role,
            content=content,
            tokens=tokens,
        )
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        return message

    async def get_messages(
        self,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> list[ChatMessageModel] | None:
        session = await self.get_session(session_id, user_id)
        if not session:
            return None

        stmt = (
            select(ChatMessageModel)
            .where(ChatMessageModel.session_id == session_id)
            .order_by(ChatMessageModel.created_at.asc())
        )
        result = await self.db.scalars(stmt)
        return list(result.all())
