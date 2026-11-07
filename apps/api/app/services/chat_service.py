# app/services/chat_service.py
import uuid
from typing import List, Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.chat import ChatSessionModel, ChatMessageModel


class ChatService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(
        self,
        user_id: uuid.UUID,
        title: Optional[str] = "New Chat",
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
    ) -> List[ChatSessionModel]:
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
    ) -> Optional[ChatSessionModel]:
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
        return True

    async def add_message(
        self,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
        role: str,
        content: str,
        tokens: Optional[int] = None,
    ) -> Optional[ChatMessageModel]:
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
    ) -> Optional[List[ChatMessageModel]]:
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
