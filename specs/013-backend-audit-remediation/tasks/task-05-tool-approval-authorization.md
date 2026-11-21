### Task 05: Authorize and Lock Tool-Call Approvals

- [ ] Pending

**Lessons:** [04 — Object-level authorization](../lessons/lesson-04-object-level-authorization.md), [05 — Check-then-act races](../lessons/lesson-05-check-then-act-races.md)

#### Full Description
**HIGH + MEDIUM.** Three defects in `ChatStreamService.stream_tool_approval` (`app/services/chat_stream_service.py`):
1. **IDOR**: `db.get(ChatMessageModel, message_id)` (`:252-253`) loads any message by id; ownership was checked for a *different* object (the path `session_id`).
2. **Replay**: the tool call's `status` is never checked (`:275-286`), so an executed or rejected call can be approved again and re-run.
3. **Lost update / double execution**: `update_message_tool_call` (`app/services/chat_service.py:149-196`) reads, modifies and writes JSON text without a lock; two concurrent approvals both execute.

Depends on Task 03 (phased sessions).

#### Technical Instructions
1. **Failing tests first** in `app/tests/test_calculator_tools.py`:
   - User B approves using user A's `message_id` + `tool_call_id` against B's own session → SSE `error` event, A's message unchanged.
   - Approve the same call twice → second stream yields `error` with "already processed".
   - Launch two approvals with `asyncio.gather` → tool function called once (Postgres-only, skip on SQLite since it ignores `FOR UPDATE`).
2. `app/services/chat_service.py`: add
   ```python
   async def get_message_for_update(self, session_id, message_id) -> ChatMessageModel | None:
       stmt = (
           select(ChatMessageModel)
           .where(ChatMessageModel.id == message_id, ChatMessageModel.session_id == session_id)
           .with_for_update()
       )
   ```
3. In phase 1 of `stream_tool_approval` (one short transaction):
   - Resolve the message with `get_message_for_update(session_id, message_id)`; if `message_id` is absent, use `get_message_by_tool_call_id` and then re-select it with the lock.
   - If `tc["status"] != "pending"` → yield `error` `{"error": "Tool call already processed."}` and return.
   - Set status to `"executing"` (approve) or `"rejected"` (reject) and **commit** — this releases the lock and marks the claim.
4. Phase 2 sets `"executed"` with the result. On tool exception set `"failed"` with a generic message.
5. Add `"executing"` and `"failed"` to the status comment on `ToolCallSchema` (`app/schemas/chat.py:14`) and to `shared/types/api.ts` `ToolCall.status`.

#### Files Touched
- `apps/api/app/services/chat_stream_service.py` (Modified)
- `apps/api/app/services/chat_service.py` (Modified)
- `apps/api/app/schemas/chat.py` (Modified)
- `shared/types/api.ts` (Modified)
- `apps/web/src/app/core/models/chat.model.ts` (Modified — status union, if typed)
- `apps/api/app/tests/test_calculator_tools.py` (Modified)

#### Verification Strategy
- Command: `cd apps/api && .venv/bin/pytest app/tests/test_calculator_tools.py app/tests/test_chat_stream.py -v && cd ../.. && make lint-api && make typecheck-api && make test-web`

#### Prepared Git Commit
```text
fix(chat): bind tool approvals to session and execute at most once

- Look up approval messages by (id, session_id) with SELECT ... FOR UPDATE
- Reject approvals for tool calls that are no longer pending
- Claim the call as "executing" in a short committed transaction before
  running the tool; record "executed" or "failed" afterwards
- Add executing/failed to the tool call status contract
- Add tests for cross-session message ids, replay and concurrent approval
- Verification: pytest test_calculator_tools.py test_chat_stream.py,
  make lint-api, make typecheck-api, make test-web passed
```
