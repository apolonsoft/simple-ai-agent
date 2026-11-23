### Task 13: Harden the Redis Connection Pool

- [x] Completed

**Lesson:** [07 — Session revocation and fail-open vs fail-closed](../lessons/lesson-07-session-revocation-and-failure-modes.md)

#### Full Description
**MEDIUM.** `get_redis_pool` (`app/core/redis.py:14-23`) creates a non-blocking `ConnectionPool` with `max_connections=50` and no timeouts:
- At 51 concurrent operations redis-py raises immediately instead of waiting, so rate limiting and caching silently fail open under load.
- If Redis hangs (network partition, `DEBUG SLEEP`, swap storm) rather than refusing connections, every awaiting request hangs indefinitely — fail-open never triggers.

After Task 11, Redis only serves rate limiting and caching, both fail-open by design (`AGENT.md` invariant 4). Fail-open only works if failures are detected quickly.

#### Technical Instructions
1. Add settings in `app/core/config.py`: `REDIS_MAX_CONNECTIONS: int = 50`, `REDIS_SOCKET_TIMEOUT: float = 0.5`, `REDIS_POOL_TIMEOUT: float = 0.2`.
2. `app/core/redis.py`:
   ```python
   _redis_pool = aioredis.BlockingConnectionPool.from_url(
       settings.REDIS_URL,
       max_connections=settings.REDIS_MAX_CONNECTIONS,
       timeout=settings.REDIS_POOL_TIMEOUT,
       socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
       socket_connect_timeout=settings.REDIS_SOCKET_TIMEOUT,
       health_check_interval=30,
       decode_responses=True,
   )
   ```
3. Remove the unused `get_redis` dependency (no callers outside tests — confirm with `rg "get_redis\b" apps/api`).
4. Add `app/tests/test_redis_pool.py`: pool type is `BlockingConnectionPool`; `socket_timeout` is set; a call against an unroutable host (`redis://10.255.255.1:6379`) fails within 1.5s and the rate limiter lets the request through.

#### Files Touched
- `apps/api/app/core/config.py` (Modified)
- `apps/api/app/core/redis.py` (Modified)
- `apps/api/app/tests/test_redis_pool.py` (Created)
- `.env.example` (Modified — document new settings)

#### Verification Strategy
- Command: `cd apps/api && .venv/bin/pytest app/tests/test_redis_pool.py app/tests/test_rate_limiter.py app/tests/test_chat_cache.py -v && cd ../.. && make lint-api && make typecheck-api`

#### Prepared Git Commit
```text
fix(redis): use a blocking pool with timeouts so fail-open is fast

- Switch to BlockingConnectionPool with pool wait, socket and connect
  timeouts and periodic health checks
- Make pool limits and timeouts configurable via settings
- Remove the unused get_redis dependency
- Add pool configuration and hung-Redis fail-open tests
- Verification: pytest test_redis_pool.py test_rate_limiter.py
  test_chat_cache.py, make lint-api, make typecheck-api passed
```
