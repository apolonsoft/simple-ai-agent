### Task 01: Refactor McpClientService for Multi-Server Support (Preparatory Refactor)

- [x] Completed

#### Full Description
Refactor `McpClientService` in `apps/api/app/services/mcp_client_service.py` to support multiple MCP server endpoints (or a single URL for backward compatibility). When querying tools or executing calls, it aggregates tools across configured server URLs and routes calls to the server that provides the tool, with ZERO functional regressions or breaking changes to existing callers and tests.

#### Technical Instructions
1. In `apps/api/app/services/mcp_client_service.py`:
   - Update `__init__` signature to accept `server_urls: list[str] | str | None = None`. Normalize into a list of strings (`self.server_urls`).
   - Retain `self.server_url` property pointing to the first URL for backward compatibility.
   - Maintain an internal registry/cache mapping `tool_name -> server_url` discovered during `get_tool_definitions()`.
   - In `get_tool_definitions()`: iterate across all `self.server_urls`, fetch tool definitions, update the tool-to-server mapping, and return the aggregated list of LLM tool schemas.
   - In `call_tool(tool_name, arguments)`: look up the server URL responsible for `tool_name` (or fallback to the first server if unknown) and execute the SSE session.
2. Ensure existing tests in `app/tests/test_mcp_client.py` still pass completely without modification.

#### Files Touched
- `apps/api/app/services/mcp_client_service.py` (Modified)

#### Verification Strategy
```bash
cd apps/api && uv run pytest app/tests/test_mcp_client.py -v
```

#### Prepared Git Commit
```text
refactor(mcp): support multiple MCP server endpoints in McpClientService

- Accept list[str] | str in McpClientService constructor
- Aggregate tool definitions across multiple MCP servers
- Route tool execution based on discovered tool-to-server mapping
- Maintain 100% backward compatibility with single-server usage
- Verification command passed: pytest app/tests/test_mcp_client.py
```
