# app/services/memory_manager.py
from collections.abc import Sequence
from typing import Literal, cast

from app.core.config import settings
from app.models.chat import ChatMessageModel
from app.schemas.llm import LLMMessage

DEFAULT_SYSTEM_PROMPT = (
    "You are an enterprise AI assistant. You provide accurate, concise, "
    "and helpful responses formatted in markdown."
)

TOOL_SYSTEM_INSTRUCTION = (
    "\nYou have access to the 'calculator' tool for arithmetic operations "
    "(add, subtract, multiply, divide). When a calculation is requested, "
    "use the calculator tool."
)


class MemoryManager:
    """
    Manages conversational memory and context assembly.
    Implements a sliding window strategy to limit context length,
    ensuring low inference latency and preventing token context blowouts.
    """

    def __init__(
        self,
        window_size: int | None = None,
        default_system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    ):
        self.window_size = window_size or settings.CHAT_MEMORY_WINDOW_SIZE
        self.default_system_prompt = default_system_prompt

    def build_context(
        self,
        history: Sequence[ChatMessageModel | dict],
        new_user_message: str | None = None,
        custom_system_prompt: str | None = None,
        include_tools: bool = False,
    ) -> list[LLMMessage]:
        """
        Assembles prompt context for LLM:
        1. Places system prompt at index 0.
        2. Slices historical messages to the last `window_size` items in chronological order.
        3. Appends the newest incoming user message.
        """
        system_instruction = custom_system_prompt or self.default_system_prompt
        if include_tools:
            system_instruction += TOOL_SYSTEM_INSTRUCTION

        context: list[LLMMessage] = [
            LLMMessage(role="system", content=system_instruction)
        ]

        # Apply sliding window: take only the last K messages
        windowed_history = (
            history[-self.window_size :] if len(history) > self.window_size else history
        )

        for msg in windowed_history:
            role = (
                msg.get("role") if isinstance(msg, dict) else getattr(msg, "role", None)
            )
            content = (
                msg.get("content")
                if isinstance(msg, dict)
                else getattr(msg, "content", "")
            ) or ""
            if not content.strip():
                tool_calls = (
                    msg.get("tool_calls")
                    if isinstance(msg, dict)
                    else getattr(msg, "tool_calls", None)
                )
                content = f"Tool call: {tool_calls}" if tool_calls else "..."
            if role in ("user", "assistant", "system"):
                context.append(
                    LLMMessage(
                        role=cast(Literal["system", "user", "assistant"], role),
                        content=str(content),
                    )
                )

        # Append incoming message if provided
        if new_user_message:
            context.append(LLMMessage(role="user", content=new_user_message))

        return context
