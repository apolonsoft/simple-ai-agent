# app/services/chat_service.py
import json
import uuid
from typing import TYPE_CHECKING, Any, Optional

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
        tool_calls: list[dict[str, Any]] | None = None,
    ) -> ChatMessageModel | None:
        """Adds a message to a session after confirming user ownership."""
        session = await self.get_session(session_id, user_id)
        if not session:
            return None

        tool_calls_json = json.dumps(tool_calls) if tool_calls else None
        message = ChatMessageModel(
            id=uuid.uuid4(),
            session_id=session_id,
            role=role,
            content=content,
            tokens=tokens,
            tool_calls=tool_calls_json,
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

    async def get_message_by_tool_call_id(
        self,
        session_id: uuid.UUID,
        tool_call_id: str,
    ) -> ChatMessageModel | None:
        """Finds a message containing a specific tool_call_id."""
        stmt = (
            select(ChatMessageModel)
            .where(
                ChatMessageModel.session_id == session_id,
                ChatMessageModel.tool_calls.isnot(None),
            )
            .order_by(ChatMessageModel.created_at.desc())
        )
        result = await self.db.scalars(stmt)
        for msg in result.all():
            if not msg.tool_calls:
                continue
            try:
                calls = json.loads(msg.tool_calls)
                if any(c.get("id") == tool_call_id for c in calls):
                    return msg
            except Exception:
                continue
        return None

    async def update_message_tool_call(
        self,
        message: ChatMessageModel,
        tool_call_id: str,
        status: str,
        result: Any | None = None,
        append_content: str | None = None,
    ) -> ChatMessageModel:
        """Updates tool call status and optional result in a message."""
        calls = []
        if message.tool_calls:
            try:
                calls = json.loads(message.tool_calls)
            except Exception:
                calls = []

        found = False
        for c in calls:
            if c.get("id") == tool_call_id:
                c["status"] = status
                if result is not None:
                    c["result"] = result
                found = True
                break

        if not found:
            calls.append(
                {
                    "id": tool_call_id,
                    "status": status,
                    "result": result,
                }
            )

        message.tool_calls = json.dumps(calls)
        if append_content:
            if message.content:
                message.content += append_content
            else:
                message.content = append_content.lstrip()

        await self.db.commit()
        await self.db.refresh(message)

        if self.cache_service is not None:
            await self.cache_service.invalidate(message.session_id)

        return message
