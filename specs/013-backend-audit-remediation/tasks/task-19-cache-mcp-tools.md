### Task 19: Cache MCP Tool Definitions

- [ ] Pending

**Lesson:** [06 — What actually blocks the event loop](../lessons/lesson-06-event-loop-blocking.md)

#### Full Description
**MEDIUM.** `McpClientService.get_tool_definitions` (`app/services/mcp_client_service.py:38-76`) opens a fresh SSE session to every MCP server, sequentially, on every chat message (`chat_stream_service.py:124`) and every approval (`:331`). When a server is down, every message waits for the connection to fail before the LLM call even starts.

#### Technical Instructions
1. **Failing test first** in `app/tests/test_mcp_client.py`: two consecutive `get_tool_definitions()` calls → `sse_client` entered once per server; after advancing a patched `time.monotonic` by 61s → entered again.
2. Add to `McpClientService`:
   - `_cache: list[dict] | None`, `_cache_expires_at: float`, `_lock = asyncio.Lock()`, `ttl_seconds: float = 60.0` (constructor arg).
   - `get_tool_definitions()`: return the cache if fresh; otherwise take the lock, re-check, then fetch. The lock prevents N concurrent messages from all refreshing at once.
3. Fetch servers concurrently with `asyncio.gather(*(self._fetch(url) for url in self.server_urls))`, each wrapped in `asyncio.wait_for(..., timeout=3.0)`.
4. Cache an empty/partial result too (so a dead server costs one timeout per TTL, not per message), but use a shorter TTL (10s) when any server failed.
5. `call_tool` is unchanged (it needs a live session).

#### Files Touched
- `apps/api/app/services/mcp_client_service.py` (Modified)
- `apps/api/app/tests/test_mcp_client.py` (Modified)

#### Verification Strategy
- Command: `cd apps/api && .venv/bin/pytest app/tests/test_mcp_client.py app/tests/test_chat_stream.py -v && cd ../.. && make lint-api && make typecheck-api`

#### Prepared Git Commit
```text
perf(mcp): cache tool definitions and fetch servers concurrently

- Cache MCP tool definitions for 60s (10s after a partial failure)
  behind an asyncio.Lock to avoid refresh stampedes
- Query MCP servers concurrently with a 3s per-server timeout
- Add cache hit/expiry tests
- Verification: pytest test_mcp_client.py test_chat_stream.py,
  make lint-api, make typecheck-api passed
```
