### Task 16: Bound Chat Queries with Pagination and Windowed Context

- [ ] Pending

**Lesson:** [03 — What your ORM does behind your back](../lessons/lesson-03-orm-loading-strategies.md)

#### Full Description
**MEDIUM.** Unbounded reads that grow with usage:
- `list_user_sessions` (`app/services/chat_service.py:37-47`) and `get_messages` (`:106-121`) return everything.
- `stream_chat` loads the full history on cache miss (`app/services/chat_stream_service.py:100`) and `stream_tool_approval` always does (`:351`), though only the last `CHAT_MEMORY_WINDOW_SIZE` messages are used.
- `get_message_by_tool_call_id` (`chat_service.py:123-147`) loads and JSON-parses every tool message in the session.

The response shape (a JSON array) must not change, so the Angular client keeps working without edits.

#### Technical Instructions
1. **Failing tests first** in `app/tests/test_chat_api.py`: 150 sessions → default `GET /chats` returns 100; `?limit=10&before=<created_at of 10th>` returns the next 10; `limit=500` → 422.
2. Routes (`app/routes/chat_routes.py`): add to `GET /chats` and `GET /chats/{id}/messages`:
   ```python
   limit: int = Query(default=100, ge=1, le=200),
   before: datetime | None = Query(default=None),
   ```
   Pass through controller → service.
3. `list_user_sessions`: `.where(created_at < before)` when given, `.order_by(created_at.desc()).limit(limit)`.
4. `get_messages`: newest-first with limit, then reverse in Python so the API still returns ascending order.
5. Add `get_recent_messages(session_id, limit)` using the existing `ix_chat_messages_session_created` index (`ORDER BY created_at DESC LIMIT :n`, reversed). Use it in both stream paths with `limit=settings.CHAT_MEMORY_WINDOW_SIZE`.
6. `get_message_by_tool_call_id`: filter in SQL first with `ChatMessageModel.tool_calls.contains(f'"id": "{tool_call_id}"', autoescape=True)` and `.limit(5)`, then confirm with `json.loads`. (After Task 05, `message_id` is normally provided, so this is the fallback path.)

#### Files Touched
- `apps/api/app/routes/chat_routes.py` (Modified)
- `apps/api/app/controllers/chat_controller.py` (Modified)
- `apps/api/app/services/chat_service.py` (Modified)
- `apps/api/app/services/chat_stream_service.py` (Modified)
- `apps/api/app/tests/test_chat_api.py` (Modified)

#### Verification Strategy
- Command: `cd apps/api && .venv/bin/pytest app/tests/test_chat_api.py app/tests/test_chat_stream.py app/tests/test_calculator_tools.py -v && cd ../.. && make lint-api && make typecheck-api && make test-web`

#### Prepared Git Commit
```text
perf(chat): paginate session/message lists and window LLM context reads

- Add limit (default 100, max 200) and before cursor to session and
  message list endpoints without changing the response shape
- Fetch only the last CHAT_MEMORY_WINDOW_SIZE messages for LLM context
- Pre-filter tool-call lookup in SQL before JSON parsing
- Add pagination tests
- Verification: pytest test_chat_api.py test_chat_stream.py
  test_calculator_tools.py, make lint-api, make typecheck-api,
  make test-web passed
```
