# app/tests/test_calculator_tools.py
from unittest.mock import patch

import httpx
import pytest
from fastapi import status

from app.providers.base import BaseLLMProvider
from app.tools.calculator import (
    calculator,
    calculator_tool_definition,
    execute_tool,
)


def test_calculator_operations():
    # add
    assert calculator("add", 10.0, 5.0) == 15.0
    assert calculator("add", -2.0, 5.0) == 3.0

    # subtract
    assert calculator("subtract", 10.0, 4.0) == 6.0
    assert calculator("subtract", 4.0, 10.0) == -6.0

    # multiply
    assert calculator("multiply", 7.0, 6.0) == 42.0
    assert calculator("multiply", 0.0, 100.0) == 0.0

    # divide
    assert calculator("divide", 20.0, 4.0) == 5.0
    assert calculator("divide", 10.0, 4.0) == 2.5

    # divide by zero
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        calculator("divide", 10.0, 0.0)

    # unsupported operator
    with pytest.raises(ValueError, match="Unsupported operator: power"):
        calculator("power", 2.0, 3.0)


def test_execute_tool_calculator():
    assert (
        execute_tool(
            "calculator", {"operator": "add", "first_number": 10, "second_number": 20}
        )
        == 30
    )
    assert (
        execute_tool(
            "calculator", {"operator": "divide", "first_number": 10, "second_number": 4}
        )
        == 2.5
    )

    with pytest.raises(ValueError, match="Tool 'unknown' is not registered."):
        execute_tool("unknown", {})


def test_calculator_tool_definition_structure():
    assert calculator_tool_definition["type"] == "function"
    fn = calculator_tool_definition["function"]
    assert isinstance(fn, dict)
    assert fn["name"] == "calculator"
    params = fn["parameters"]
    assert isinstance(params, dict)
    properties = params["properties"]
    assert isinstance(properties, dict)
    assert "operator" in properties
    assert "first_number" in properties
    assert "second_number" in properties
    assert params["required"] == ["operator", "first_number", "second_number"]


class MockToolCallingProvider(BaseLLMProvider):
    """Yields a tool call followed by completion."""

    def __init__(self, tool_call_dict=None, text_after_tool=None):
        self.tool_call_dict = tool_call_dict or {
            "type": "tool_call",
            "name": "calculator",
            "arguments": {
                "operator": "multiply",
                "first_number": 12,
                "second_number": 10,
            },
        }
        self.text_after_tool = text_after_tool or "12 multiplied by 10 is 120."

    @property
    def provider_name(self) -> str:
        return "mock"

    async def generate_stream(
        self,
        messages,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ):
        # If this is the follow-up stream after approval
        if any("[SYSTEM NOTIFICATION]" in msg.content for msg in messages):
            yield self.text_after_tool
        else:
            yield self.tool_call_dict

    async def health_check(self) -> bool:
        return True


async def get_auth_token(
    client: httpx.AsyncClient, email: str = "tool_tester@example.com"
) -> str:
    await client.post(
        "/api/v1/auth/register", json={"email": email, "password": "password123"}
    )
    login_res = await client.post(
        "/api/v1/auth/login", data={"username": email, "password": "password123"}
    )
    return login_res.json()["access_token"]


@pytest.mark.asyncio
async def test_tool_calling_flow_with_user_approval(client: httpx.AsyncClient):
    token = await get_auth_token(client, "tool_approval@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create a session
    sess_res = await client.post(
        "/api/v1/chats", json={"title": "Calculator Session"}, headers=headers
    )
    session_id = sess_res.json()["id"]

    mock_provider = MockToolCallingProvider()

    # 2. User asks calculation -> model emits tool call, awaiting user approval
    with patch(
        "app.services.chat_stream_service.get_llm_provider", return_value=mock_provider
    ):
        stream_res = await client.post(
            f"/api/v1/chats/{session_id}/stream",
            json={"content": "What is 12 * 10?"},
            headers=headers,
        )
        assert stream_res.status_code == status.HTTP_200_OK
        text_body = stream_res.text
        assert "event: tool_call" in text_body
        assert "calculator" in text_body
        assert "multiply" in text_body
        assert "awaiting_approval" in text_body

    # 3. Check message in DB has pending tool_call
    msgs_res = await client.get(f"/api/v1/chats/{session_id}/messages", headers=headers)
    assert msgs_res.status_code == status.HTTP_200_OK
    messages = msgs_res.json()
    assert len(messages) == 2
    assistant_msg = messages[1]
    assert assistant_msg["role"] == "assistant"
    assert assistant_msg["tool_calls"] is not None
    assert len(assistant_msg["tool_calls"]) == 1
    tool_call = assistant_msg["tool_calls"][0]
    tool_call_id = tool_call["id"]
    assert tool_call["status"] == "pending"
    assert tool_call["arguments"]["operator"] == "multiply"

    # 4. User approves the tool call via frontend approval endpoint
    with patch(
        "app.services.chat_stream_service.get_llm_provider", return_value=mock_provider
    ):
        approval_res = await client.post(
            f"/api/v1/chats/{session_id}/tool-calls/approval",
            json={
                "tool_call_id": tool_call_id,
                "approved": True,
                "message_id": assistant_msg["id"],
            },
            headers=headers,
        )
        assert approval_res.status_code == status.HTTP_200_OK
        approval_text = approval_res.text
        assert "event: tool_result" in approval_text
        assert "executed" in approval_text
        assert "120" in approval_text
        assert "12 multiplied by 10 is 120." in approval_text

    # 5. Verify message updated in DB to executed with result
    msgs_res2 = await client.get(
        f"/api/v1/chats/{session_id}/messages", headers=headers
    )
    updated_assistant_msg = msgs_res2.json()[1]
    assert updated_assistant_msg["tool_calls"][0]["status"] == "executed"
    assert updated_assistant_msg["tool_calls"][0]["result"] == 120


@pytest.mark.asyncio
async def test_tool_calling_flow_with_user_rejection(client: httpx.AsyncClient):
    token = await get_auth_token(client, "tool_rejection@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    sess_res = await client.post(
        "/api/v1/chats", json={"title": "Rejection Session"}, headers=headers
    )
    session_id = sess_res.json()["id"]

    mock_provider = MockToolCallingProvider()

    with patch(
        "app.services.chat_stream_service.get_llm_provider", return_value=mock_provider
    ):
        stream_res = await client.post(
            f"/api/v1/chats/{session_id}/stream",
            json={"content": "Can you multiply 12 and 10?"},
            headers=headers,
        )
        assert stream_res.status_code == status.HTTP_200_OK

    msgs_res = await client.get(f"/api/v1/chats/{session_id}/messages", headers=headers)
    assistant_msg = msgs_res.json()[1]
    tool_call_id = assistant_msg["tool_calls"][0]["id"]

    # User REJECTS the tool call
    rejection_res = await client.post(
        f"/api/v1/chats/{session_id}/tool-calls/approval",
        json={
            "tool_call_id": tool_call_id,
            "approved": False,
        },
        headers=headers,
    )
    assert rejection_res.status_code == status.HTTP_200_OK
    rejection_text = rejection_res.text
    assert "event: tool_result" in rejection_text
    assert "rejected" in rejection_text

    # Verify message in DB marked as rejected
    msgs_res2 = await client.get(
        f"/api/v1/chats/{session_id}/messages", headers=headers
    )
    updated_assistant_msg = msgs_res2.json()[1]
    assert updated_assistant_msg["tool_calls"][0]["status"] == "rejected"
