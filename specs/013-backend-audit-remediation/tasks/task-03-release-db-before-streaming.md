### Task 03: Release DB Connections Before SSE Streaming

- [ ] Pending

**Lesson:** [02 — Resource lifetimes: connections, transactions and yield dependencies](../lessons/lesson-02-resource-lifetimes.md)

#### Full Description
**CRITICAL.** In FastAPI 0.162, request-scoped `yield` dependencies are finalized only after `await response(...)` completes (`fastapi/routing.py`, `request_stack`). For SSE, that means after the whole stream. The `db` session used by `get_current_user` and the ownership check in `stream_chat_response` (`app/routes/chat_routes.py:128-153`) and `handle_tool_approval` (`:164-190`) therefore keeps a pooled connection **idle in transaction** for the entire LLM generation. About 30 concurrent chats per worker exhaust the pool (20 + 10 overflow) and every other request waits 30s, then fails.

Separately, `ChatStreamService.stream_tool_approval` (`app/services/chat_stream_service.py:241-358`) runs the tool (MCP call, web search) inside its own `async with self.session_factory()` block.

Both violate `AGENT.md` invariant 1.

#### Technical Instructions
1. **Failing test first** in `app/tests/test_chat_stream.py`:
   - Use a fake provider whose `generate_stream` records whether the request's session is still in a transaction (`session.in_transaction()`) — capture the session via a wrapped `get_db` override — then yields one chunk.
   - Add a Postgres-only variant (skip when `DATABASE_URL` is SQLite) asserting `engine.pool.checkedout() == 0` inside the provider.
2. `app/routes/chat_routes.py`, both stream routes, after the ownership check:
   ```python
   user_id = current_user.id
   await db.close()
   ```
   Pass `user_id` (not `current_user`) into the generator. `close()` ends the transaction and returns the connection; `get_db`'s later `close()` is a no-op.
3. `app/services/chat_stream_service.py::stream_tool_approval`, restructure into three phases:
   - **Phase 1 (session A):** load session, message, tool call; copy out plain values (`target_msg_id`, `tool_name`, `tool_args`). Close session A.
   - **Tool execution:** no session open.
   - **Phase 2 (session B):** re-load message by id, `update_message_tool_call(...)`, load history for the follow-up prompt. Close session B.
   - Leave the existing post-follow-up persistence block (session C) as is.
4. Do not change SSE event names or payloads.

#### Files Touched
- `apps/api/app/routes/chat_routes.py` (Modified)
- `apps/api/app/services/chat_stream_service.py` (Modified)
- `apps/api/app/tests/test_chat_stream.py` (Modified)
- `apps/api/app/tests/test_calculator_tools.py` (Modified — only if approval flow fixtures need adjusting)

#### Verification Strategy
- Command: `cd apps/api && .venv/bin/pytest app/tests/test_chat_stream.py app/tests/test_calculator_tools.py -v && cd ../.. && make lint-api && make typecheck-api`
- Optional load check: `make benchmark` with > 40 concurrent streams completes without `TimeoutError: QueuePool limit`.

#### Prepared Git Commit
```text
fix(chat): release database connection before SSE streaming

- Close the request-scoped session in /stream and /tool-calls/approval
  after the ownership check so no connection is pinned for the stream
- Split stream_tool_approval into load / execute / persist phases so no
  session is open during tool execution
- Add regression test asserting no open transaction while the provider
  is generating
- Verification: pytest test_chat_stream.py test_calculator_tools.py,
  make lint-api, make typecheck-api passed
```
