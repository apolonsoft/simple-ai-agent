# Lesson 02: Resource Lifetimes — Connections, Transactions and Yield Dependencies

**Pattern:** A scarce resource (a database connection, a lock, a file handle) is held from the moment it's acquired until something explicitly releases it. Not until the last time you *use* it. If you don't know exactly when release happens, you don't control your system's capacity.

**Applies to:** Task 03 (stream pinning), Task 22 (cancellation)

---

## 1. The bug in this repo

```python
# apps/api/app/routes/chat_routes.py — stream_chat_response
async def stream_chat_response(
    session_id: uuid.UUID,
    message_in: ChatMessageCreate,
    current_user: UserModel = Depends(get_current_user),   # uses db
    db: AsyncSession = Depends(get_db),                     # same db (cached per request)
    stream_service: ChatStreamService = Depends(get_chat_stream_service),
):
    chat_service = ChatService(db)
    session = await chat_service.get_session(session_id, current_user.id)  # opens a transaction
    ...
    return EventSourceResponse(generator)   # handler returns; db is still open
```

`ChatStreamService` was carefully designed to release connections during inference (see its docstring and `AGENT.md` invariant 1). The route undid that design with one `Depends`.

## 2. Mental model

### 2.1 Autobegin
SQLAlchemy 2.0 sessions **autobegin**: the first `execute()` checks out a connection and starts a transaction. The connection goes back to the pool only on `commit()`, `rollback()` or `close()`. A read-only `SELECT` followed by nothing leaves Postgres showing the connection as `idle in transaction`.

### 2.2 When does a `yield` dependency finish?
```python
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session          # handler runs here
    # cleanup runs ... when?
```
The answer changed across FastAPI versions:
- **< 0.106**: after the response was fully sent.
- **0.106 – 0.117**: before the response was sent, which broke streaming responses that needed the session.
- **≥ 0.118 (you have 0.162)**: after the response is sent again. Newer versions also offer `Depends(..., scope="function")` to close right after the handler returns.

For a normal JSON response, "after the response is sent" means milliseconds. For SSE it means **after the whole LLM generation**, 5–30 seconds.

Read the source yourself; it's short. In `fastapi/routing.py`:
```python
async with AsyncExitStack() as request_stack:
    ...
    response = await f(request)
    await response(scope, receive, send)   # streaming happens here
# request-scoped dependencies close here
```

### 2.3 Little's Law: why seconds matter
Throughput ≤ pool size ÷ hold time.

| Hold time per request | Pool = 30 | Max requests/second |
|---|---|---|
| 5 ms (short transaction) | 30 | 6,000 |
| 20 s (pinned for a stream) | 30 | 1.5 |

Pinning a connection for a stream doesn't make the app a bit slower. It cuts capacity by more than three orders of magnitude, and it does so for **every** endpoint, because login needs a connection too. The failure mode is a cliff: everything works at 29 concurrent chats, and at 31 every request waits `pool_timeout=30s`, then fails.

## 3. The fix pattern
Acquire late, release early, and **never hold a resource across I/O you don't control** (LLM calls, tool calls, HTTP, user think-time).

```python
session = await chat_service.get_session(session_id, current_user.id)
if not session:
    raise HTTPException(404, ...)
user_id = current_user.id      # copy plain values out first
await db.close()               # transaction ends, connection returns to the pool
return EventSourceResponse(stream_service.stream_chat(session_id=session_id, user_id=user_id, ...))
```

The same rule applies inside `stream_tool_approval`: load (session A, closed) → run the tool (no session) → persist (session B, closed).

## 4. Cancellation is part of the lifetime too
When an SSE client disconnects, the generator gets `GeneratorExit` / `CancelledError` at its current `await`. Code after the loop never runs, so the assistant reply is lost (Task 22). Tools:
- `try/finally` for cleanup that must run.
- `asyncio.shield(...)` for a short write that must not be interrupted.
- Never `yield` inside `finally` after cancellation.

## 5. How to detect this class of bug
- Postgres: `SELECT state, now() - xact_start FROM pg_stat_activity WHERE state = 'idle in transaction';`
- SQLAlchemy: `engine.pool.checkedout()` and `engine.pool.status()`.
- Tests: assert `session.in_transaction()` is `False` at the point where you claim no resource is held.
- Load test: run `make benchmark` with more concurrent streams than `pool_size + max_overflow`.

---

## Exercises
1. Without running anything, how many concurrent chat streams can one worker sustain before `/auth/login` starts failing? Show the numbers.
2. `get_current_user` and the route both declare `Depends(get_db)`. Are they the same session or two? Why does it matter here?
3. After `await db.close()`, the route still uses `current_user.id`. Why is that safe? What would *not* be safe to access?
4. `ChatStreamService.stream_tool_approval` opens its own session with `async with self.session_factory()`. Which lines hold it, and what slow work happens inside?
5. Name a non-database resource in this codebase with the same lifetime risk.

---

## Mentor Notes
1. `pool_size=20 + max_overflow=10 = 30`. Each active stream holds one, so the 31st concurrent request of *any* kind waits up to 30 seconds (`DB_POOL_TIMEOUT`) and then fails. With 4 workers that's about 120 chats cluster-wide, but per-worker load is uneven, so the cliff arrives earlier.
2. The same session: FastAPI caches dependency results per request by default (`use_cache=True`). That's why closing `db` in the route also releases the connection `get_current_user` used. If they were separate, you'd need to close both.
3. `close()` expunges objects, but attributes that were already loaded stay readable on the detached instance. `id` was loaded. Lazy relationships are *not* safe; with `lazy="raise"` (Task 04) accessing one raises, and with plain lazy loading on async it fails with `MissingGreenlet`. Copy primitives out before closing.
4. Lines 241–358: the session is held across `mcp_client.get_tool_definitions()` (an SSE handshake per server), `mcp_client.call_tool(...)` or `execute_tool(...)` (web search, PDF generation), and history loading. That's seconds of external I/O with a pooled connection idle in a transaction.
5. Redis connections in the rate limiter (`async with redis.client() as conn` holds one connection for the whole sequence of round-trips). Also each `httpx.AsyncClient` created per LLM call holds sockets for the stream, and every MCP call opens a new SSE session.

## Review Checklist
- [ ] For every acquired resource, can I point to the exact line that releases it?
- [ ] Is any connection or lock held across a network call I don't control?
- [ ] For streaming responses, have I accounted for when dependencies actually close?
- [ ] Does cleanup still run, and is critical persistence protected, if the client disconnects?
