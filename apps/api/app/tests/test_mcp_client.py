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


@pytest.mark.asyncio
async def test_mcp_client_multi_server_aggregation():
    """Verify that McpClientService aggregates tools across multiple configured servers."""
    client = McpClientService(
        server_urls=["http://127.0.0.1:8001/sse", "http://127.0.0.1:8002/sse"]
    )
    assert len(client.server_urls) == 2

    tool_tavily = MagicMock()
    tool_tavily.name = "search_web"
    tool_tavily.description = "Search web"
    tool_tavily.input_schema = {"type": "object", "properties": {}}

    tool_pdf = MagicMock()
    tool_pdf.name = "create_pdf"
    tool_pdf.description = "Create PDF"
    tool_pdf.input_schema = {"type": "object", "properties": {}}

    mock_session1 = AsyncMock()
    mock_session1.initialize = AsyncMock()
    mock_session1.list_tools = AsyncMock(
        return_value=MagicMock(tools=[tool_tavily])
    )

    mock_session2 = AsyncMock()
    mock_session2.initialize = AsyncMock()
    mock_session2.list_tools = AsyncMock(
        return_value=MagicMock(tools=[tool_pdf])
    )

    sessions = [mock_session1, mock_session2]

    class MockContextManager:
        async def __aenter__(self):
            return sessions.pop(0)

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
        side_effect=lambda r, w: MockContextManager(),
    ):
        tools = await client.get_tool_definitions()
        tool_names = [t["function"]["name"] for t in tools]
        assert "search_web" in tool_names
        assert "create_pdf" in tool_names
        assert client.tool_to_server["search_web"] == "http://127.0.0.1:8001/sse"
        assert client.tool_to_server["create_pdf"] == "http://127.0.0.1:8002/sse"
