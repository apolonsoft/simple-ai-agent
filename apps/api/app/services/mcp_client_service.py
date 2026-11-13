import logging
from typing import Any

from mcp.client.session import ClientSession
from mcp.client.sse import sse_client

from app.core.config import settings

logger = logging.getLogger(__name__)


class McpClientService:
    def __init__(self, server_url: str | None = None):
        self.server_url = server_url or getattr(
            settings, "MCP_TAVILY_URL", "http://127.0.0.1:8001/sse"
        )

    async def get_tool_definitions(self) -> list[dict[str, Any]]:
        """Fetch tools from the MCP server and convert them to standard LLM format."""
        try:
            async with sse_client(self.server_url) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    response = await session.list_tools()

                    tool_definitions = []
                    for tool in response.tools:
                        input_schema = getattr(
                            tool, "input_schema", getattr(tool, "inputSchema", {})
                        )
                        tool_definitions.append(
                            {
                                "type": "function",
                                "function": {
                                    "name": tool.name,
                                    "description": tool.description or "",
                                    "parameters": input_schema or {},
                                },
                            }
                        )
                    return tool_definitions
        except Exception as exc:
            logger.warning(
                "Could not fetch tools from MCP server at %s: %s",
                self.server_url,
                exc,
            )
            return []

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> str:
        """Call a specific tool on the MCP server and return the string result."""
        try:
            async with sse_client(self.server_url) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool(tool_name, arguments)

                    output_parts = []
                    for content in result.content:
                        if hasattr(content, "text"):
                            output_parts.append(content.text)
                        else:
                            output_parts.append(str(content))

                    return (
                        "\n\n".join(output_parts)
                        if output_parts
                        else "No output returned."
                    )
        except Exception as exc:
            logger.error("Failed to execute MCP tool '%s': %s", tool_name, exc)
            return f"Error executing tool {tool_name}: {exc}"


mcp_client = McpClientService()
