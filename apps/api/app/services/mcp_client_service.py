import logging
from typing import Any

from mcp.client.session import ClientSession
from mcp.client.sse import sse_client

from app.core.config import settings

logger = logging.getLogger(__name__)


class McpClientService:
    def __init__(
        self,
        server_url: str | list[str] | None = None,
        server_urls: list[str] | str | None = None,
    ):
        target = server_urls or server_url
        if target is None:
            self.server_urls = [
                getattr(settings, "MCP_TAVILY_URL", "http://127.0.0.1:8001/sse")
            ]
        elif isinstance(target, str):
            self.server_urls = [target]
        else:
            self.server_urls = list(target)
        self.tool_to_server: dict[str, str] = {}

    @property
    def server_url(self) -> str:
        return self.server_urls[0] if self.server_urls else ""

    async def get_tool_definitions(self) -> list[dict[str, Any]]:
        """Fetch tools from all configured MCP servers and convert them to standard LLM format."""
        all_tool_definitions: list[dict[str, Any]] = []
        seen_tool_names: set[str] = set()

        for url in self.server_urls:
            try:
                async with (
                    sse_client(url) as (read, write),
                    ClientSession(read, write) as session,
                ):
                    await session.initialize()
                    response = await session.list_tools()

                    for tool in response.tools:
                        self.tool_to_server[tool.name] = url
                        if tool.name in seen_tool_names:
                            continue
                        seen_tool_names.add(tool.name)
                        input_schema = getattr(
                            tool, "input_schema", getattr(tool, "inputSchema", {})
                        )
                        all_tool_definitions.append(
                            {
                                "type": "function",
                                "function": {
                                    "name": tool.name,
                                    "description": tool.description or "",
                                    "parameters": input_schema or {},
                                },
                            }
                        )
            except Exception as exc:
                logger.warning(
                    "Could not fetch tools from MCP server at %s: %s",
                    url,
                    exc,
                )
        return all_tool_definitions

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> str:
        """Call a specific tool on the appropriate MCP server and return the string result."""
        target_url = self.tool_to_server.get(tool_name) or (
            self.server_urls[0] if self.server_urls else ""
        )
        if not target_url:
            return f"Error executing tool {tool_name}: No MCP server configured."

        try:
            async with (
                sse_client(target_url) as (read, write),
                ClientSession(read, write) as session,
            ):
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
            logger.error(
                "Failed to execute MCP tool '%s' on %s: %s",
                tool_name,
                target_url,
                exc,
            )
            return f"Error executing tool {tool_name}: {exc}"


mcp_client = McpClientService()
