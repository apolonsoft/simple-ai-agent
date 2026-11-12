# app/tests/test_calculator_tools.py
from typing import Any, cast
from unittest.mock import patch

import httpx
import pytest
from fastapi import status

from app.providers.base import BaseLLMProvider
from app.tools.base import (
    AgentCompletionResponse,
    AgentMessageResponse,
    ToolCallResponse,
    function_to_input_schema,
    function_to_tool_definition,
    simple_agent_loop,
    tool_execution,
)
from app.tools.calculator import (
    calculator,
    calculator_tool_definition,
    execute_tool,
    search_web_tool_definition,
)
from app.tools.search import search_web


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
        calculator(cast(Any, "power"), 2.0, 3.0)


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
    assert properties["operator"]["enum"] == ["add", "subtract", "multiply", "divide"]
    assert "first_number" in properties
    assert "second_number" in properties
    assert params["required"] == ["operator", "first_number", "second_number"]


def test_search_web_tool_definition_and_execution():
    assert search_web_tool_definition["type"] == "function"
    fn = search_web_tool_definition["function"]
    assert fn["name"] == "search_web"
    assert fn["description"] == "Search the web for the given query."
    params = fn["parameters"]
    assert params["required"] == ["query"]
    assert params["properties"]["query"]["type"] == "string"
    assert params["properties"]["max_results"]["type"] == "integer"
    assert params["properties"]["max_results"]["default"] == 5

    with patch("app.tools.search.tavily_client.search") as mock_search:
        mock_search.return_value = {
            "results": [{"title": "FastAPI", "url": "https://fastapi.tiangolo.com"}]
        }
        res = search_web("FastAPI Python", max_results=3)
        assert res == [{"title": "FastAPI", "url": "https://fastapi.tiangolo.com"}]
        mock_search.assert_called_once_with(
            "FastAPI Python", max_results=3, topic="general", time_range=None
        )

    # Test error handling when search fails
    with patch(
        "app.tools.search.tavily_client.search",
        side_effect=Exception("API connection timeout"),
    ):
        error_res = search_web("Test query")
        assert "Error: Search failed - API connection timeout" in error_res

    # Test execution via execute_tool
    with patch("app.tools.search.tavily_client.search") as mock_search:
        mock_search.return_value = {"results": ["item1"]}
        result = execute_tool("search_web", {"query": "deep learning"})
        assert result == ["item1"]


def test_function_to_input_schema_and_tool_definition():
    def sample_func(
        city: str, days: int, verbose: bool = False, extra: dict | None = None
    ):
        """Search weather forecast for a city."""
        return f"{city}-{days}-{verbose}"

    schema = function_to_input_schema(sample_func)
    assert schema["type"] == "object"
    assert "city" in schema["properties"]
    assert schema["properties"]["city"]["type"] == "string"
    assert schema["properties"]["days"]["type"] == "integer"
    assert schema["properties"]["verbose"]["type"] == "boolean"
    assert schema["required"] == ["city", "days"]  # verbose has default

    tool_def = function_to_tool_definition(sample_func)
    assert tool_def["type"] == "function"
    assert tool_def["function"]["name"] == "sample_func"
    assert tool_def["function"]["description"] == "Search weather forecast for a city."
    assert tool_def["function"]["parameters"] == schema


def test_tool_execution_with_object_and_dict():
    tool_box = {"calculator": calculator}

    # 1. Object format (e.g. LiteLLM / OpenAI response)
    class FakeFunc:
        name = "calculator"
        arguments = '{"operator": "add", "first_number": 15, "second_number": 25}'

    class FakeToolCall:
        function = FakeFunc()

    result1 = tool_execution(tool_box, FakeToolCall())
    assert result1 == 40

    # 2. Dict format
    result2 = tool_execution(
        tool_box,
        {
            "name": "calculator",
            "arguments": {
                "operator": "multiply",
                "first_number": 4,
                "second_number": 5,
            },
        },
    )
    assert result2 == 20

    with pytest.raises(ValueError, match="is not registered in tool_box"):
        tool_execution(tool_box, {"name": "non_existent", "arguments": {}})


def test_simple_agent_loop_with_completion_fn():
    call_count = 0

    def mock_completion(api_base, model, messages, tools):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # Model requests tool call
            return AgentCompletionResponse(
                AgentMessageResponse(
                    content="",
                    tool_calls=[
                        ToolCallResponse(
                            id="call_mock_1",
                            name="calculator",
                            arguments={
                                "operator": "multiply",
                                "first_number": 9,
                                "second_number": 9,
                            },
                        )
                    ],
                )
            )
        else:
            # Second turn: Model returns final prose after seeing role="tool"
            return AgentCompletionResponse(AgentMessageResponse(content="9 * 9 = 81"))

    result = simple_agent_loop(
        system_prompt="You are a math helper.",
        question="What is 9 * 9?",
        tools=[calculator],
        completion_fn=mock_completion,
    )

    assert result == "9 * 9 = 81"
    assert call_count == 2


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


@pytest.mark.asyncio
async def test_search_web_tool_calling_flow_with_user_approval(
    client: httpx.AsyncClient,
):
    token = await get_auth_token(client, "search_approval@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    sess_res = await client.post(
        "/api/v1/chats", json={"title": "Web Search Session"}, headers=headers
    )
    session_id = sess_res.json()["id"]

    mock_search_call = {
        "type": "tool_call",
        "name": "search_web",
        "arguments": {"query": "FastAPI latest release notes"},
    }
    mock_provider = MockToolCallingProvider(
        tool_call_dict=mock_search_call,
        text_after_tool="Based on web search, FastAPI latest release includes multiple improvements.",
    )

    with patch(
        "app.services.chat_stream_service.get_llm_provider", return_value=mock_provider
    ):
        stream_res = await client.post(
            f"/api/v1/chats/{session_id}/stream",
            json={"content": "Can you search the web for the latest FastAPI release?"},
            headers=headers,
        )
        assert stream_res.status_code == status.HTTP_200_OK
        text_body = stream_res.text
        assert "event: tool_call" in text_body
        assert "search_web" in text_body
        assert "calculator" not in text_body
        assert "awaiting_approval" in text_body

    # Verify only 1 tool call was generated and stored in pending state
    msgs_res = await client.get(f"/api/v1/chats/{session_id}/messages", headers=headers)
    assert msgs_res.status_code == status.HTTP_200_OK
    messages = msgs_res.json()
    assert len(messages) == 2
    assistant_msg = messages[1]
    assert assistant_msg["tool_calls"] is not None
    assert len(assistant_msg["tool_calls"]) == 1
    tool_call = assistant_msg["tool_calls"][0]
    assert tool_call["tool"] == "search_web"
    assert tool_call["status"] == "pending"

    # User approves search_web execution
    fake_search_res = {
        "results": [{"title": "FastAPI Release", "url": "https://fastapi.tiangolo.com"}]
    }
    with (
        patch(
            "app.services.chat_stream_service.get_llm_provider",
            return_value=mock_provider,
        ),
        patch("app.tools.search.tavily_client.search", return_value=fake_search_res),
    ):
        approval_res = await client.post(
            f"/api/v1/chats/{session_id}/tool-calls/approval",
            json={
                "tool_call_id": tool_call["id"],
                "approved": True,
                "message_id": assistant_msg["id"],
            },
            headers=headers,
        )
        assert approval_res.status_code == status.HTTP_200_OK
        approval_text = approval_res.text
        assert "event: tool_result" in approval_text
        assert "executed" in approval_text
        assert "FastAPI Release" in approval_text
        assert "FastAPI latest release includes multiple improvements" in approval_text
