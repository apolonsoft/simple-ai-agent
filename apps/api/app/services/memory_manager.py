# app/services/memory_manager.py
from typing import List, Optional
from app.core.config import settings
from app.models.chat import ChatMessageModel
from app.schemas.llm import LLMMessage

DEFAULT_SYSTEM_PROMPT = (
    "You are an enterprise AI assistant. You provide accurate, concise, "
    "and helpful responses formatted in markdown."
)


class MemoryManager:
    """
    Manages conversational memory and context assembly.
    Implements a sliding window strategy to limit context length,
    ensuring low inference latency and preventing token context blowouts.
    """

    def __init__(
        self,
        window_size: Optional[int] = None,
        default_system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    ):
        self.window_size = window_size or settings.CHAT_MEMORY_WINDOW_SIZE
        self.default_system_prompt = default_system_prompt

    def build_context(
        self,
        history: List[ChatMessageModel],
        new_user_message: Optional[str] = None,
        custom_system_prompt: Optional[str] = None,
    ) -> List[LLMMessage]:
        """
        Assembles prompt context for LLM:
        1. Places system prompt at index 0.
        2. Slices historical messages to the last `window_size` items in chronological order.
        3. Appends the newest incoming user message.
        """
        system_instruction = custom_system_prompt or self.default_system_prompt
        context: List[LLMMessage] = [
            LLMMessage(role="system", content=system_instruction)
        ]

        # Apply sliding window: take only the last K messages
        windowed_history = history[-self.window_size:] if len(history) > self.window_size else history

        for msg in windowed_history:
            role = msg.get("role") if isinstance(msg, dict) else getattr(msg, "role", None)
            content = msg.get("content") if isinstance(msg, dict) else getattr(msg, "content", "")
            if role in ("user", "assistant", "system"):
                context.append(LLMMessage(role=role, content=content))

        # Append incoming message if provided
        if new_user_message:
            context.append(LLMMessage(role="user", content=new_user_message))

        return context
