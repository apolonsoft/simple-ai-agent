import asyncio
import logging
import time
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
        ttl_seconds: float = 60.0,
    ):
        target = server_urls or server_url
        if target is None:
            urls = []
            tavily = getattr(settings, "MCP_TAVILY_URL", "http://127.0.0.1:8001/sse")
            if tavily:
                urls.append(tavily)
            pdf = getattr(settings, "MCP_PDF_URL", "http://127.0.0.1:8002/sse")
            if pdf:
                urls.append(pdf)
            self.server_urls = urls or ["http://127.0.0.1:8001/sse"]
        elif isinstance(target, str):
            self.server_urls = [target]
        else:
            self.server_urls = list(target)
        self.tool_to_server: dict[str, str] = {}
        self.ttl_seconds = ttl_seconds
        self._cache: list[dict[str, Any]] | None = None
        self._cache_expires_at: float = 0.0
        self._lock = asyncio.Lock()

    @property
    def server_url(self) -> str:
        return self.server_urls[0] if self.server_urls else ""

    async def _fetch_from_server(self, url: str) -> list[dict[str, Any]]:
        async with (
            sse_client(url) as (read, write),
            ClientSession(read, write) as session,
        ):
            await session.initialize()
            response = await session.list_tools()

            definitions: list[dict[str, Any]] = []
            for tool in response.tools:
                input_schema = getattr(
                    tool, "input_schema", getattr(tool, "inputSchema", {})
                )
                definitions.append(
                    {
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description or "",
                            "parameters": input_schema or {},
                        },
                    }
                )
            return definitions

    async def _fetch(self, url: str) -> tuple[str, list[dict[str, Any]], bool]:
        try:
            definitions = await asyncio.wait_for(
                self._fetch_from_server(url), timeout=3.0
            )
            return url, definitions, True
        except Exception as exc:
            logger.warning(
                "Could not fetch tools from MCP server at %s: %s",
                url,
                exc,
            )
            return url, [], False

    async def get_tool_definitions(self) -> list[dict[str, Any]]:
        """Fetch tools from all configured MCP servers with in-process TTL caching."""
        if self._cache is not None and time.monotonic() < self._cache_expires_at:
            return self._cache

        async with self._lock:
            if self._cache is not None and time.monotonic() < self._cache_expires_at:
                return self._cache

            results = await asyncio.gather(
                *(self._fetch(url) for url in self.server_urls)
            )

            all_tool_definitions: list[dict[str, Any]] = []
            seen_tool_names: set[str] = set()
            any_failed = False

            for url, tools, ok in results:
                if not ok:
                    any_failed = True
                for tool_def in tools:
                    name = tool_def["function"]["name"]
                    self.tool_to_server[name] = url
                    if name in seen_tool_names:
                        continue
                    seen_tool_names.add(name)
                    all_tool_definitions.append(tool_def)

            ttl = min(self.ttl_seconds, 10.0) if any_failed else self.ttl_seconds
            self._cache = all_tool_definitions
            self._cache_expires_at = time.monotonic() + ttl
            return self._cache

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

                output_parts: list[str] = []
                for content in result.content:
                    if hasattr(content, "text"):
                        output_parts.append(str(content.text))
                    else:
                        output_parts.append(str(content))

                return (
                    "\n\n".join(output_parts) if output_parts else "No output returned."
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
