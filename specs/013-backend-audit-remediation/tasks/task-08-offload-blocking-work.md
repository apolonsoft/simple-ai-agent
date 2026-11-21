### Task 08: Move Blocking Work off the Event Loop

- [ ] Pending

**Lesson:** [06 — What actually blocks the event loop](../lessons/lesson-06-event-loop-blocking.md)

#### Full Description
**HIGH + MEDIUM.** Three sources of synchronous work run directly on the event loop, freezing every concurrent SSE stream on the worker:
1. Argon2 hash/verify (`app/core/security.py:13-18`), called from `register_user`, `authenticate`, `reset_password`, `change_password` in `app/services/auth_service.py`.
2. In-process tool execution `execute_tool(...)` (`app/services/chat_stream_service.py:336`) — sync Tavily HTTP (`app/tools/search.py`) and CPU-bound fpdf/pypdf.
3. `boto3.client(...)` constructed per request (`app/services/storage_service.py:19`) via `get_user_controller` (`app/routes/user_routes.py:15-16`), even on `GET /users/me`.

#### Technical Instructions
1. `app/core/security.py`: add
   ```python
   async def hash_password_async(password: str) -> str:
       return await asyncio.to_thread(password_hash.hash, password)

   async def verify_password_async(plain: str, hashed: str) -> bool:
       return await asyncio.to_thread(password_hash.verify, plain, hashed)
   ```
   Keep the sync versions for `scripts/manage_admin.py`.
2. Replace every call in `auth_service.py` with the async versions.
3. `chat_stream_service.py`: `tool_result = await asyncio.to_thread(execute_tool, tool_name, tool_args)`.
4. `storage_service.py`:
   - Module-level `_s3_client: Any | None = None` and `def _get_s3_client()` that creates it once (boto3 clients are thread-safe after creation; creation itself is not, so guard with `threading.Lock`).
   - `StorageService.__init__` stores the injected client or `None`; resolve lazily inside `_sync_upload` (already in a thread).
   - `_bucket_verified` becomes module-level so it isn't re-checked per request.
5. Tests:
   - `test_auth_service.py`: patch `asyncio.to_thread` in `app.core.security` with a spy and assert it is used by `authenticate`.
   - `test_user_profile_api.py`: assert `boto3.client` is called at most once across two `GET /users/me` calls.

#### Files Touched
- `apps/api/app/core/security.py` (Modified)
- `apps/api/app/services/auth_service.py` (Modified)
- `apps/api/app/services/chat_stream_service.py` (Modified)
- `apps/api/app/services/storage_service.py` (Modified)
- `apps/api/app/tests/test_auth_service.py` (Modified)
- `apps/api/app/tests/test_user_profile_api.py` (Modified)

#### Verification Strategy
- Command: `make test-api && make lint-api && make typecheck-api`
- Optional: `make benchmark` — p99 chunk latency during a login burst should no longer spike.

#### Prepared Git Commit
```text
perf(api): move password hashing, tool execution and S3 setup off the event loop

- Add hash_password_async / verify_password_async using asyncio.to_thread
  and use them throughout AuthService
- Run in-process tool execution in a worker thread
- Create the boto3 S3 client once per process instead of per request
- Add tests for thread offloading and single client construction
- Verification: make test-api, make lint-api, make typecheck-api passed
```
