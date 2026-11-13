# app/services/chat_stream_service.py
import json
import logging
import re
import uuid
from collections.abc import AsyncGenerator
from typing import Any

from app.db.session import AsyncSessionLocal
from app.models.chat import ChatMessageModel
from app.providers.factory import get_llm_provider
from app.services.chat_cache_service import ChatCacheService
from app.services.chat_service import ChatService
from app.services.mcp_client_service import mcp_client
from app.services.memory_manager import MemoryManager
from app.tools.calculator import TOOL_DEFINITIONS, execute_tool

logger = logging.getLogger(__name__)


def _extract_tool_calls_from_text(text: str) -> tuple[str, list[dict[str, Any]]]:
    """
    Fallback parser for models that output tool calls in markdown fences or JSON strings.
    Example:
    ```tool_call
    {"name": "calculator", "arguments": {"operator": "add", "first_number": 1, "second_number": 2}}
    ```
    """
    tool_calls = []
    pattern = r"```(?:tool_call|json)?\s*(\{(?:[^{}]|(?:\{[^{}]*\}))*\})\s*```"
    matches = list(re.finditer(pattern, text, re.DOTALL))

    cleaned_text = text
    for match in matches:
        raw_json = match.group(1).strip()
        try:
            parsed = json.loads(raw_json)
            tool_name = parsed.get("name") or parsed.get("tool")
            args = parsed.get("arguments") or parsed.get("parameters") or {}
            if tool_name and isinstance(args, dict):
                tool_calls.append(
                    {
                        "id": f"call_{uuid.uuid4().hex[:12]}",
                        "tool": tool_name,
                        "arguments": args,
                        "status": "pending",
                    }
                )
                cleaned_text = cleaned_text.replace(match.group(0), "").strip()
        except Exception:
            continue

    return cleaned_text, tool_calls


class ChatStreamService:
    """
    High-concurrency streaming coordinator with human-in-the-loop tool calling.
    Decouples database transactions from long-running LLM inference to protect
    the async database connection pool against starvation under high traffic.
    Leverages Redis conversation context caching to minimize PostgreSQL query load.
    """

    def __init__(
        self,
        session_factory=AsyncSessionLocal,
        memory_manager: MemoryManager | None = None,
        cache_service: ChatCacheService | None = None,
    ):
        self.session_factory = session_factory
        self.memory_manager = memory_manager or MemoryManager()
        self.cache_service = cache_service or ChatCacheService()

    async def stream_chat(
        self,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
        user_content: str,
        provider_name: str | None = None,
        custom_system_prompt: str | None = None,
    ) -> AsyncGenerator[dict, None]:
        # ==============================================================================
        # 1. PRE-INFERENCE PHASE: Check Redis cache, validate session, save turn (~5ms DB time)
        # ==============================================================================
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
                prior_history = cached_history
            else:
                db_messages = await chat_service.get_messages(session_id, user_id) or []
                prior_history = db_messages
                await self.cache_service.set_messages(session_id, db_messages)

            saved_user_msg = await chat_service.add_message(
                session_id=session_id,
                user_id=user_id,
                role="user",
                content=user_content,
            )

            await self.cache_service.append_message(
                session_id, saved_user_msg or {"role": "user", "content": user_content}
            )

            llm_messages = self.memory_manager.build_context(
                history=prior_history,
                new_user_message=user_content,
                custom_system_prompt=custom_system_prompt,
                include_tools=True,
            )

        # Database connection is now released back to the pool.
        # ==============================================================================
        # 2. STREAMING INFERENCE PHASE: Zero DB connections held during token generation
        # ==============================================================================
        provider = get_llm_provider(provider_name)
        full_response_chunks: list[str] = []
        detected_tool_calls: list[dict[str, Any]] = []

        # Discover dynamic tools from MCP server
        mcp_tools = await mcp_client.get_tool_definitions()
        local_tool_names = {t.get("function", {}).get("name") for t in TOOL_DEFINITIONS}
        active_tools = list(TOOL_DEFINITIONS)
        for mt in mcp_tools:
            if mt.get("function", {}).get("name") not in local_tool_names:
                active_tools.append(mt)

        try:
            async for token in provider.generate_stream(
                llm_messages, tools=active_tools
            ):
                if isinstance(token, dict):
                    # Provider emitted a tool call chunk
                    tool_name = token.get("name") or token.get("tool")
                    if not tool_name:
                        continue
                    call_id = token.get("id") or f"call_{uuid.uuid4().hex[:12]}"
                    tc_obj = {
                        "id": call_id,
                        "tool": tool_name,
                        "arguments": token.get("arguments", {}),
                        "status": "pending",
                    }
                    detected_tool_calls.append(tc_obj)
                    yield {
                        "event": "tool_call",
                        "data": json.dumps(tc_obj),
                    }
                elif isinstance(token, str):
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

        # Check for fallback tool calls in text
        full_response_text = "".join(full_response_chunks)
        if not detected_tool_calls and full_response_text:
            cleaned_text, fallback_calls = _extract_tool_calls_from_text(
                full_response_text
            )
            if fallback_calls:
                detected_tool_calls.extend(fallback_calls)
                full_response_text = cleaned_text
                for tc in fallback_calls:
                    yield {
                        "event": "tool_call",
                        "data": json.dumps(tc),
                    }

        # ==============================================================================
        # 3. POST-INFERENCE PHASE: Checkout fresh DB session to persist assistant response (~5ms)
        # ==============================================================================
        assistant_message_id = None

        if full_response_text or detected_tool_calls:
            try:
                async with self.session_factory() as db:
                    chat_service = ChatService(db, cache_service=self.cache_service)
                    saved_msg = await chat_service.add_message(
                        session_id=session_id,
                        user_id=user_id,
                        role="assistant",
                        content=full_response_text,
                        tool_calls=detected_tool_calls if detected_tool_calls else None,
                    )
                    if saved_msg:
                        assistant_message_id = str(saved_msg.id)
                        await self.cache_service.append_message(session_id, saved_msg)
            except Exception as exc:
                logger.error(
                    f"Failed to persist assistant message: {exc}", exc_info=True
                )

        # Signal completion with status
        done_payload: dict[str, Any] = {
            "message_id": assistant_message_id,
            "status": "awaiting_approval" if detected_tool_calls else "completed",
        }
        if detected_tool_calls:
            done_payload["tool_calls"] = detected_tool_calls

        yield {
            "event": "done",
            "data": json.dumps(done_payload),
        }

    async def stream_tool_approval(
        self,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
        tool_call_id: str,
        approved: bool,
        message_id: uuid.UUID | None = None,
        provider_name: str | None = None,
    ) -> AsyncGenerator[dict, None]:
        """
        Processes human-in-the-loop tool approval or rejection:
        - If rejected: marks tool call as rejected, returns cancellation notice.
        - If approved: executes the tool (e.g. calculator), yields tool result,
          then streams follow-up LLM response incorporating the tool output.
        """
        async with self.session_factory() as db:
            chat_service = ChatService(db, cache_service=self.cache_service)
            session = await chat_service.get_session(session_id, user_id)
            if not session:
                yield {
                    "event": "error",
                    "data": json.dumps({"error": "Chat session not found."}),
                }
                return

            target_msg = None
            if message_id:
                target_msg = await db.get(ChatMessageModel, message_id)
            if not target_msg:
                target_msg = await chat_service.get_message_by_tool_call_id(
                    session_id, tool_call_id
                )

            if not target_msg:
                yield {
                    "event": "error",
                    "data": json.dumps(
                        {"error": f"Tool call '{tool_call_id}' not found."}
                    ),
                }
                return

            calls = []
            if target_msg.tool_calls:
                try:
                    calls = json.loads(target_msg.tool_calls)
                except Exception:
                    calls = []

            tc = next((c for c in calls if c.get("id") == tool_call_id), None)
            if not tc:
                yield {
                    "event": "error",
                    "data": json.dumps(
                        {"error": f"Tool call '{tool_call_id}' not found in message."}
                    ),
                }
                return

            # Identify tool name
            tool_name = tc.get("tool") or "unknown_tool"

            if not approved:
                # User rejected tool execution
                await chat_service.update_message_tool_call(
                    message=target_msg,
                    tool_call_id=tool_call_id,
                    status="rejected",
                    result="Tool execution was rejected by user.",
                    append_content="\n\n*Tool execution was rejected by user.*",
                )

                yield {
                    "event": "tool_result",
                    "data": json.dumps(
                        {
                            "tool_call_id": tool_call_id,
                            "status": "rejected",
                            "result": "Tool execution was rejected by user.",
                        }
                    ),
                }
                yield {
                    "event": "chunk",
                    "data": json.dumps(
                        {
                            "content": f"\n\n*Tool execution was rejected by user. The '{tool_name}' tool was not executed.*"
                        }
                    ),
                }
                yield {
                    "event": "done",
                    "data": json.dumps(
                        {
                            "message_id": str(target_msg.id),
                            "status": "completed",
                        }
                    ),
                }
                return

            # User approved tool execution -> execute tool!
            tool_args = tc.get("arguments", {})
            try:
                # Check if tool is provided by MCP server
                mcp_tools = await mcp_client.get_tool_definitions()
                mcp_names = {t.get("function", {}).get("name") for t in mcp_tools}
                if tool_name in mcp_names:
                    tool_result = await mcp_client.call_tool(tool_name, tool_args)
                else:
                    tool_result = execute_tool(tool_name, tool_args)
                tool_error = None
            except Exception as exc:
                tool_result = None
                tool_error = str(exc)

            final_val = tool_result if tool_error is None else f"Error: {tool_error}"

            await chat_service.update_message_tool_call(
                message=target_msg,
                tool_call_id=tool_call_id,
                status="executed",
                result=final_val,
            )

            prior_history = await chat_service.get_messages(session_id, user_id) or []
            llm_messages = self.memory_manager.build_context(
                history=prior_history,
                new_user_message=(
                    f"[SYSTEM NOTIFICATION]: The tool '{tool_name}' was approved and executed with arguments {tool_args}. "
                    f"Result: {final_val}. Provide a friendly, concise answer to the user based on this result."
                ),
            )

        # Notify frontend of tool execution result
        yield {
            "event": "tool_result",
            "data": json.dumps(
                {
                    "tool_call_id": tool_call_id,
                    "status": "executed",
                    "result": final_val,
                }
            ),
        }

        # Stream follow-up completion from LLM
        provider = get_llm_provider(provider_name)
        followup_chunks: list[str] = []

        try:
            async for token in provider.generate_stream(llm_messages):
                if isinstance(token, str):
                    followup_chunks.append(token)
                    yield {
                        "event": "chunk",
                        "data": json.dumps({"content": token}),
                    }
        except Exception as exc:
            logger.error(
                f"Error during LLM stream after tool approval: {exc}", exc_info=True
            )
            fallback_text = f"\n\nTool '{tool_name}' result: {final_val}"
            followup_chunks.append(fallback_text)
            yield {
                "event": "chunk",
                "data": json.dumps({"content": fallback_text}),
            }

        followup_text = "".join(followup_chunks)
        if followup_text:
            try:
                async with self.session_factory() as db:
                    chat_service = ChatService(db, cache_service=self.cache_service)
                    msg_to_update = await db.get(ChatMessageModel, target_msg.id)
                    if msg_to_update:
                        await chat_service.update_message_tool_call(
                            message=msg_to_update,
                            tool_call_id=tool_call_id,
                            status="executed",
                            append_content=f"\n\n{followup_text}",
                        )
            except Exception as exc:
                logger.error(
                    f"Failed to persist followup LLM content: {exc}", exc_info=True
                )

        yield {
            "event": "done",
            "data": json.dumps(
                {
                    "message_id": str(target_msg.id),
                    "status": "completed",
                }
            ),
        }
