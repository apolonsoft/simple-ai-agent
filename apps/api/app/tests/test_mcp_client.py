# app/tests/test_mcp_client.py
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.services.mcp_client_service import McpClientService


@pytest.mark.asyncio
async def test_mcp_client_unreachable_server():
    """Verify that McpClientService gracefully fails without raising an exception if server is down."""
    client = McpClientService(server_url="http://127.0.0.1:9999/sse")
    tools = await client.get_tool_definitions()
    assert tools == []


@pytest.mark.asyncio
async def test_mcp_client_call_tool_failure():
    """Verify that calling a tool on an unreachable server returns a clean error string."""
    client = McpClientService(server_url="http://127.0.0.1:9999/sse")
    result = await client.call_tool("search_web", {"query": "test"})
    assert "Error executing tool" in result


@pytest.mark.asyncio
async def test_mcp_client_schema_parsing():
    """Verify that MCP tool definitions are correctly converted to LLM function schemas."""
    client = McpClientService(server_url="http://127.0.0.1:8001/sse")

    mock_tool = MagicMock()
    mock_tool.name = "search_web"
    mock_tool.description = "Search the web"
    mock_tool.input_schema = {
        "type": "object",
        "properties": {"query": {"type": "string"}},
        "required": ["query"],
    }

    mock_session = AsyncMock()
    mock_session.initialize = AsyncMock()
    mock_session.list_tools = AsyncMock(
        return_value=MagicMock(tools=[mock_tool])
    )

    class MockContextManager:
        async def __aenter__(self):
            return mock_session

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    class MockSseContextManager:
        async def __aenter__(self):
            return (MagicMock(), MagicMock())

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    with patch(
        "app.services.mcp_client_service.sse_client",
        return_value=MockSseContextManager(),
    ), patch(
        "app.services.mcp_client_service.ClientSession",
        return_value=MockContextManager(),
    ):
        tools = await client.get_tool_definitions()
        assert len(tools) == 1
        fn = tools[0]["function"]
        assert fn["name"] == "search_web"
        assert fn["description"] == "Search the web"
        assert fn["parameters"]["required"] == ["query"]
