# app/services/chat_stream_service.py
import json
import uuid
import logging
from typing import AsyncGenerator, Optional
from fastapi import HTTPException, status
from app.db.session import AsyncSessionLocal
from app.models.chat import ChatSessionModel
from app.providers.factory import get_llm_provider
from app.services.chat_service import ChatService
from app.services.chat_cache_service import ChatCacheService
from app.services.memory_manager import MemoryManager

logger = logging.getLogger(__name__)


class ChatStreamService:
    """
    High-concurrency streaming coordinator.
    Decouples database transactions from long-running LLM inference to protect
    the async database connection pool against starvation under high traffic.
    Leverages Redis conversation context caching to minimize PostgreSQL query load.
    """

    def __init__(
        self,
        session_factory=AsyncSessionLocal,
        memory_manager: Optional[MemoryManager] = None,
        cache_service: Optional[ChatCacheService] = None,
    ):
        self.session_factory = session_factory
        self.memory_manager = memory_manager or MemoryManager()
        self.cache_service = cache_service or ChatCacheService()

    async def stream_chat(
        self,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
        user_content: str,
        provider_name: Optional[str] = None,
        custom_system_prompt: Optional[str] = None,
    ) -> AsyncGenerator[dict, None]:
        # ==============================================================================
        # 1. PRE-INFERENCE PHASE: Check Redis cache, validate session, save turn (~5ms DB time)
        # ==============================================================================
        # Check active session context from Redis first (0ms DB load)
        cached_history = await self.cache_service.get_messages(session_id)

        async with self.session_factory() as db:
            chat_service = ChatService(db, cache_service=self.cache_service)
            session = await chat_service.get_session(session_id, user_id)
            if not session:
                yield {
                    "event": "error",
                    "data": json.dumps({"error": "Chat session not found."}),
                }
                return

            if cached_history is not None:
                # Cache hit: Avoid PostgreSQL message SELECT query
                prior_history = cached_history
            else:
                # Cache miss: Fetch from PostgreSQL and populate Redis cache
                db_messages = await chat_service.get_messages(session_id, user_id) or []
                prior_history = db_messages
                await self.cache_service.set_messages(session_id, db_messages)

            # Save the new user prompt to PostgreSQL
            saved_user_msg = await chat_service.add_message(
                session_id=session_id,
                user_id=user_id,
                role="user",
                content=user_content,
            )

            # Append user message to Redis cache
            await self.cache_service.append_message(session_id, saved_user_msg or {"role": "user", "content": user_content})

            # Build sliding-window context
            llm_messages = self.memory_manager.build_context(
                history=prior_history,
                new_user_message=user_content,
                custom_system_prompt=custom_system_prompt,
            )

        # Database connection is now released back to the pool.
        # ==============================================================================
        # 2. STREAMING INFERENCE PHASE: Zero DB connections held during token generation
        # ==============================================================================
        provider = get_llm_provider(provider_name)
        full_response_chunks = []

        try:
            async for token in provider.generate_stream(llm_messages):
                full_response_chunks.append(token)
                yield {
                    "event": "chunk",
                    "data": json.dumps({"content": token}),
                }
        except Exception as exc:
            logger.error(f"Error during LLM stream generation: {exc}", exc_info=True)
            yield {
                "event": "error",
                "data": json.dumps({"error": f"LLM generation error: {str(exc)}"}),
            }
            return

        # ==============================================================================
        # 3. POST-INFERENCE PHASE: Checkout fresh DB session to persist assistant response (~5ms)
        # ==============================================================================
        full_response_text = "".join(full_response_chunks)
        assistant_message_id = None

        if full_response_text:
            try:
                async with self.session_factory() as db:
                    chat_service = ChatService(db, cache_service=self.cache_service)
                    saved_msg = await chat_service.add_message(
                        session_id=session_id,
                        user_id=user_id,
                        role="assistant",
                        content=full_response_text,
                    )
                    if saved_msg:
                        assistant_message_id = str(saved_msg.id)
                        # Append assistant message to Redis cache
                        await self.cache_service.append_message(session_id, saved_msg)
            except Exception as exc:
                logger.error(f"Failed to persist assistant message: {exc}", exc_info=True)

        # Signal stream completion
        yield {
            "event": "done",
            "data": json.dumps({
                "message_id": assistant_message_id,
                "status": "completed",
            }),
        }
