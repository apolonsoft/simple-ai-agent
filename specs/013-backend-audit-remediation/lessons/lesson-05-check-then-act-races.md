# Lesson 05: Check-Then-Act Races

**Pattern:** "Read a value, decide, then write" is only correct if nothing can change the value between the read and the write. In a server handling concurrent requests, something always can. This is TOCTOU (time-of-check to time-of-use). The fix is never "check more carefully". It is to make the check and the act **one atomic operation**, or to let a constraint reject the loser.

**Applies to:** Task 05 (tool approval), Task 09 (rate limiter), Task 14 (cache, see Lesson 11), Task 20 (registration)

---

## 1. Four instances in this repo

| Where | Check | Act | What two concurrent requests do |
|---|---|---|---|
| `stream_tool_approval` | (none) status | run tool, write status | Both run the tool; one JSON update overwrites the other |
| `RateLimiter.__call__` | `ZCARD < max` (pipeline 1) | `ZADD` (pipeline 2) | 20 parallel requests all see 4 < 5 and all pass |
| `AuthController.register` | `get_by_email is None` | `INSERT` | Both pass; unique index rejects one, which surfaces as a **500** |
| `ChatCacheService.append_message` | `GET` list | `SET` list + 1 | Both read N, both write N+1; one message is lost |

Notice the asymmetry: registration is *safe* (the database has a unique constraint) but *ugly* (500 instead of 409). The other three are *unsafe*, because nothing below the application enforces the invariant.

## 2. Mental model: where can the invariant live?
Ordered from strongest to weakest:

1. **Database constraint**: `UNIQUE`, `CHECK`, `FOREIGN KEY`, exclusion constraints. Impossible to violate. Catch `IntegrityError` and map it to a clean error.
2. **Atomic conditional write (compare-and-set)**:
   ```sql
   UPDATE tool_calls SET status = 'executing'
   WHERE id = :id AND status = 'pending'
   RETURNING id;
   ```
   Zero rows returned means someone else won. No lock is held while you think.
3. **Row lock**: `SELECT ... FOR UPDATE` inside a short transaction, then check and write, then commit. Correct, but you must keep the transaction short (Lesson 02).
4. **Atomic primitives in Redis**: `INCR`, `SET NX`, `MULTI/EXEC` pipelines, Lua scripts. A Redis pipeline is atomic, but it **cannot branch** on a value it read. If the decision depends on the read, use Lua or `WATCH`.
5. **Application-level locks** (`asyncio.Lock`): only valid within *one process*. Useless across workers and replicas.

## 3. The tool-approval fix, explained
Tool calls are stored as JSON text inside `chat_messages.tool_calls`, so a clean `UPDATE ... WHERE status='pending'` on one call isn't available. A row lock is the pragmatic choice:

```python
# Phase 1: short transaction claims the work
msg = await chat_service.get_message_for_update(session_id, message_id)   # SELECT ... FOR UPDATE
tc = find_call(msg, tool_call_id)
if tc["status"] != "pending":
    yield error("Tool call already processed."); return
set_status(msg, tool_call_id, "executing")
await db.commit()                      # lock released, claim recorded

# Tool runs with NO lock and NO connection held
result = await run_tool(...)

# Phase 2: record the outcome
```
The trick is the **claim state** (`executing`). It lets the slow work happen outside the lock while still guaranteeing at-most-once execution. If the worker crashes mid-tool, the call stays `executing`; a production system would add a timeout sweeper. Note that as a non-goal or follow-up.

The better long-term design: give tool calls their own table, so a compare-and-set `UPDATE` works directly.

## 4. The rate-limiter fix, explained
Add first, then count, in **one** `MULTI/EXEC`:
```text
ZREMRANGEBYSCORE key 0 window_start
ZADD key now member
ZCARD key            → count includes this request
EXPIRE key window+5
```
If `count > max`, reject and `ZREM` your member. Every request is now serialized by Redis, so exactly `max` requests are admitted.

## 5. Testing races
- Use `asyncio.gather(*[call() for _ in range(20)])` to force interleaving.
- **SQLite won't reproduce row-lock races**: it ignores `FOR UPDATE` and serializes writers. Mark those tests Postgres-only (`pytest.mark.skipif("sqlite" in DATABASE_URL)`) and run them in CI against the docker-compose Postgres.
- Make the slow part *slow* in tests (`await asyncio.sleep(0.05)` inside a fake tool) to widen the race window.

---

## Exercises
1. For the registration race: is it a security bug, a correctness bug, or a UX bug? What guarantees that you can't get two accounts with the same email?
2. Rewrite the tool-approval claim as a single compare-and-set `UPDATE`, assuming a dedicated `tool_calls` table. What do you gain over `FOR UPDATE`?
3. Why can't the rate limiter fix be "just put everything in one pipeline" while keeping the current order (count first, then add)?
4. `asyncio.Lock` around `append_message` would fix the lost update in tests. Why is it wrong in production?
5. Find a check-then-act in `admin_service.ban_user`. Is it dangerous?

---

## Mentor Notes
1. Correctness/UX. The unique index `ix_users_email` (migration `a9a5a2298381`) guarantees uniqueness, which is integrity. The bug is the unhandled `IntegrityError` becoming a 500. Keep the pre-check for the common case (nice error, no failed insert), *and* catch the constraint violation for the race.
2. ```sql
   UPDATE tool_calls SET status='executing', claimed_at=now()
   WHERE id=:call_id AND message_id=:msg_id AND status='pending'
   RETURNING tool_name, arguments;
   ```
   You gain: no lock wait, a single round trip, no long transaction risk, and authorization (`message_id`) plus state check in one statement. Zero rows means "not found, not yours, or already processed".
3. A pipeline executes commands atomically but returns results only at the end. You can't make `ZADD` conditional on the `ZCARD` result inside the same pipeline. Adding unconditionally and then removing on reject sidesteps that, because the decision moves after the atomic step.
4. You run multiple uvicorn workers and possibly multiple replicas. Each has its own `asyncio.Lock`, so two tabs routed to different workers still race. Process-local locks only protect process-local state.
5. `target = db.get(...)` → check role → set `is_banned`. If a super_admin promotes the target to admin between the read and the commit, a regular admin's ban could still apply. The window is tiny, admin actions are rare, and the impact is an admin wrongly banned, which can be reversed. Low risk; `with_for_update()` on the target would close it cheaply. Judging when a race *matters* is part of the skill.

## Review Checklist
- [ ] Every "if not exists then insert" backed by a unique constraint and `IntegrityError` handling?
- [ ] Every state transition (`pending → done`) done with compare-and-set or a row lock?
- [ ] Redis read-modify-write done with Lua, `WATCH`, or a native atomic command?
- [ ] No process-local locks guarding shared state?
- [ ] Race tests run against Postgres, not just SQLite?
