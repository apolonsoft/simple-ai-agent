### Task 22: Persist Partial Replies on Client Disconnect

- [ ] Pending

**Lesson:** [02 — Resource lifetimes: connections, transactions and yield dependencies](../lessons/lesson-02-resource-lifetimes.md)

#### Full Description
**LOW.** When the browser disconnects mid-stream, sse-starlette cancels the generator. `stream_chat` (`app/services/chat_stream_service.py:139-211`) only persists the assistant message after the loop finishes, so the user's message is saved with no reply and the next turn's context is inconsistent.

#### Technical Instructions
1. **Failing test first** in `app/tests/test_chat_stream.py`: fake provider yields 3 chunks then sleeps; consume 2 events, call `await gen.aclose()`; assert an assistant message containing the first chunks exists in the DB.
2. Wrap the streaming loop in `try/finally`. In `finally`, if not yet persisted and there is text or tool calls, persist in a **shielded** task so cancellation can't interrupt the write:
   ```python
   finally:
       if not persisted and (full_response_chunks or detected_tool_calls):
           await asyncio.shield(self._persist_assistant(session_id, user_id, text, calls))
   ```
   Extract `_persist_assistant` from the current post-inference block and reuse it on the normal path.
3. Do **not** add a column to flag interrupted replies (non-goal); the partial text is stored as-is.
4. Ensure `yield` never happens inside `finally` (illegal after `GeneratorExit`).

#### Files Touched
- `apps/api/app/services/chat_stream_service.py` (Modified)
- `apps/api/app/tests/test_chat_stream.py` (Modified)

#### Verification Strategy
- Command: `cd apps/api && .venv/bin/pytest app/tests/test_chat_stream.py -v && cd ../.. && make lint-api && make typecheck-api`

#### Prepared Git Commit
```text
fix(chat): persist partial assistant replies when the client disconnects

- Extract _persist_assistant and call it from a finally block shielded
  from cancellation
- Add test that closes the stream mid-generation and asserts the partial
  reply is stored
- Verification: pytest test_chat_stream.py, make lint-api,
  make typecheck-api passed
```
