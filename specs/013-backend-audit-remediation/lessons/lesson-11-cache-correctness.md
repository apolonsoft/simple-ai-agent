# Lesson 11: Cache Correctness

**Pattern:** A cache is a second copy of your data that can be wrong, and is guaranteed to be eventually. Before adding one, know (1) what work it removes, (2) how it gets invalidated, (3) how concurrent writers interact with it, and (4) how big it can grow. A cache that's wrong is worse than no cache, because it fails silently.

**Applies to:** Task 14 (chat history), Task 19 (MCP tool definitions)

---

## 1. The bugs in this repo

```python
# apps/api/app/services/chat_cache_service.py — append_message
raw_data = await client.get(key)                     # read
if raw_data is not None:
    current_list = json.loads(raw_data)
    current_list.append(self._serialize_message(message))   # modify in Python
    await client.set(key, json.dumps(current_list), ex=self.ttl)   # write
```

Three problems:
1. **Lost updates**: two tabs streaming in the same session both `GET` N messages and both `SET` N+1. One message disappears from the cached context, and the sliding TTL keeps the wrong version alive as long as the chat is active.
2. **Unbounded size**: the whole history is cached, while `MemoryManager` uses only the last `CHAT_MEMORY_WINDOW_SIZE` (10) messages.
3. **O(n) writes**: each append re-reads and re-serializes the entire history.

And one problem that dwarfs the others: **the cache saved nothing**, because the ownership check (`get_session`) eagerly loaded every message through `lazy="selectin"` before the cache was consulted (Lesson 03).

## 2. Mental model: four questions for every cache

| Question | Chat history cache (before) | After Task 14 |
|---|---|---|
| What work does it remove? | Nothing: the DB read happened anyway | The windowed DB read, once Tasks 04 and 16 land |
| How is it invalidated? | Delete on session delete and tool-call update ✔ | Same, plus clearing the legacy key |
| How do concurrent writers interact? | Lost updates ✘ | Atomic append (Lua) ✔ |
| How big can it get? | Unbounded ✘ | `LTRIM` to the window ✔ |

### Use the data structure the store gives you
Redis has lists. `RPUSH` + `LTRIM` + `EXPIRE` express "append and keep the last N" natively. The only subtlety is "append **only if the key exists**", so a partial cache isn't created after an invalidation. That needs a conditional, which pipelines can't express, so it needs a small Lua script:

```lua
if redis.call('EXISTS', KEYS[1]) == 1 then
  redis.call('RPUSH', KEYS[1], ARGV[1])
  redis.call('LTRIM', KEYS[1], -tonumber(ARGV[2]), -1)
  redis.call('EXPIRE', KEYS[1], ARGV[3])
  return 1
end
return 0
```
Lua scripts run atomically in Redis. No other command interleaves.

### Version your keys when the format changes
Switching a key from a string to a list means old string keys would cause `WRONGTYPE` errors. A new key name (`chat:history:v2:{id}`) avoids a migration; old keys expire on their own TTL.

## 3. Stampedes: when they matter and when they don't
A **stampede** happens when a popular key expires and N concurrent requests all miss and all recompute.
- **Chat history**: one key per session, read by one user. N is 1 or 2, so there's no stampede. Don't add locking you don't need.
- **MCP tool definitions** (Task 19): one global value read by *every* chat message. At expiry, every in-flight message would open SSE sessions to every MCP server. Here it matters, so the fix uses **single-flight**: an `asyncio.Lock` plus a re-check after acquiring it, so only one coroutine per process refreshes.

  ```python
  if self._fresh(): return self._cache
  async with self._lock:
      if self._fresh(): return self._cache     # someone else refreshed while we waited
      self._cache = await self._fetch_all()
  ```
  Per process is fine here: K workers means at most K refreshes per TTL, which is harmless.

Other stampede tools, for bigger systems: probabilistic early refresh, stale-while-revalidate, and a distributed lock with `SET NX PX`.

### Negative caching
If an MCP server is down, cache the failure too, with a shorter TTL. Otherwise every message pays the connection timeout to rediscover that it's still down.

## 4. Invalidation rules that hold up
- Invalidate on **every** write path that changes the cached data. The repo does this for delete and tool-call updates, which is good.
- Prefer **delete** over **update** on writes. The next reader repopulates from the source of truth, so the race shrinks to the delete-then-stale-set case.
- Never let the cache become the source of truth for anything security-relevant (Lesson 07).

---

## Exercises
1. Two tabs, same session, cache populated with 4 messages. Write the interleaving of Redis commands that loses a message on the current code.
2. After Task 14, `invalidate` runs while another request is between "read DB on cache miss" and `set_messages`. What can go wrong, and how bad is it?
3. Why is a Redis pipeline (`MULTI/EXEC`) insufficient for "append only if the key exists", but sufficient for `set_messages`?
4. How would you *prove* the chat cache is worth keeping after Tasks 04 and 16? What would you measure?
5. The MCP cache lock is per process. When would you need a distributed lock instead?

---

## Mentor Notes
1. ```text
   Tab A: GET key → [m1..m4]
   Tab B: GET key → [m1..m4]
   Tab A: SET key [m1..m4, a5]
   Tab B: SET key [m1..m4, b5]      ← a5 is gone from the cache (still in Postgres)
   ```
   The next turn in either tab builds LLM context without a5, until the cache is invalidated or expires, and the TTL is refreshed on every append.
2. Request X misses and reads 10 messages from the DB. Request Y updates a tool call and calls `invalidate`. X then calls `set_messages` with its pre-update snapshot, and the cache now holds stale tool status until the next invalidation or TTL. Impact: the LLM sees one outdated tool result in its context. Low. A version counter (`INCR session:ver` on invalidate, `set_messages` only if the version is unchanged, checked in Lua) closes it, but that's not worth it here. Know the race exists, judge it, write it down.
3. `set_messages` is unconditional (`DEL`, `RPUSH`, `EXPIRE`); the pipeline just makes the three steps atomic. "Append only if it exists" needs the *result* of `EXISTS` to decide whether to run `RPUSH`, and a pipeline sends all commands before seeing any results. Lua runs server-side with branching.
4. Measure hit ratio (hits ÷ lookups), DB query count and latency for context loading with the cache on vs off, and Redis memory per session. If the windowed query (`LIMIT 10` on an index) takes ~1 ms and the hit ratio is modest, the cache may cost more in complexity than it saves. **Deleting a cache is a valid outcome.**
5. When the refresh itself is expensive or rate-limited *in aggregate*, for example calling a paid API or a fragile upstream, so K workers × R replicas refreshing at once is a problem. Then use `SET lock NX PX 5000` in Redis, with the other processes serving stale data while one refreshes.

## Review Checklist
- [ ] Can I state what work this cache removes, and have I measured it?
- [ ] Is every write path that changes the data paired with an invalidation?
- [ ] Are read-modify-write operations atomic in the cache store?
- [ ] Is the cached value bounded in size?
- [ ] For hot shared keys: is there single-flight or stale-while-revalidate?
- [ ] Are key formats versioned?
