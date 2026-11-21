### Task 14: Make the Chat Cache an Atomic Bounded List

- [ ] Pending

**Lesson:** [11 — Cache correctness](../lessons/lesson-11-cache-correctness.md)

#### Full Description
**MEDIUM.** `ChatCacheService.append_message` (`app/services/chat_cache_service.py:111-137`) does `GET` → modify in Python → `SET`. Two concurrent streams on one session (two tabs) lose a message from the cached context, and the TTL refresh keeps the wrong history alive. The cache also stores the **entire** history while `MemoryManager` uses only the last `CHAT_MEMORY_WINDOW_SIZE` messages, and each append re-serializes everything (O(n) per message).

Public method signatures stay the same so callers in `chat_stream_service.py` and `chat_service.py` don't change.

#### Technical Instructions
1. **Failing tests first** in `app/tests/test_chat_cache.py` (real Redis or `fakeredis` if available; otherwise mark `@pytest.mark.redis`):
   - 20 concurrent `append_message` calls after `set_messages` → `get_messages` returns all 20 + seed.
   - `set_messages` with 50 messages → `get_messages` returns the last `window` messages.
2. Rewrite storage as a Redis list of JSON strings, key `chat:history:v2:{session_id}` (new key avoids type clashes with old string keys):
   - `set_messages`: pipeline(transaction=True) → `DELETE`, `RPUSH *items` (only the last `window`), `EXPIRE`.
   - `append_message`: "append only if the key exists" must be atomic, so run it as a Lua script (a pipeline cannot branch on `EXISTS`):
     ```lua
     if redis.call('EXISTS', KEYS[1]) == 1 then
       redis.call('RPUSH', KEYS[1], ARGV[1])
       redis.call('LTRIM', KEYS[1], -tonumber(ARGV[2]), -1)
       redis.call('EXPIRE', KEYS[1], ARGV[3])
       return 1
     end
     return 0
     ```
     Register once with `client.register_script(...)`.
   - `get_messages`: `LRANGE key 0 -1` → `[json.loads(x) for x in items]`; empty list on a missing key must still mean "miss" → check `EXISTS` in the same pipeline.
   - `invalidate`: `DELETE` both the v2 key and the legacy key.
3. Window size: `ChatCacheService(window: int | None = None)` defaulting to `settings.CHAT_MEMORY_WINDOW_SIZE`.
4. Keep fail-open: any exception → log warning, return `None`/`False`.
5. Stampede: not applicable (one user per key) — no locking needed; document this in the class docstring.

#### Files Touched
- `apps/api/app/services/chat_cache_service.py` (Modified)
- `apps/api/app/tests/test_chat_cache.py` (Modified)

#### Verification Strategy
- Command: `cd apps/api && .venv/bin/pytest app/tests/test_chat_cache.py app/tests/test_chat_stream.py -v && cd ../.. && make lint-api && make typecheck-api`

#### Prepared Git Commit
```text
fix(cache): store chat history as an atomic, bounded Redis list

- Replace GET/modify/SET with RPUSH + LTRIM + EXPIRE executed atomically
  via a Lua script that only appends to populated keys
- Bound cached history to CHAT_MEMORY_WINDOW_SIZE
- Version the cache key (chat:history:v2) and clear legacy keys on
  invalidate
- Add concurrent-append and window-trim tests
- Verification: pytest test_chat_cache.py test_chat_stream.py,
  make lint-api, make typecheck-api passed
```
