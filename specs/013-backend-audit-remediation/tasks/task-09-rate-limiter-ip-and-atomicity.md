### Task 09: Trust Only Real Client IPs and Make Rate Limiting Atomic

- [ ] Pending

**Lessons:** [09 — Trusting infrastructure: headers, proxies and config](../lessons/lesson-09-trusting-infrastructure.md), [05 — Check-then-act races](../lessons/lesson-05-check-then-act-races.md)

#### Full Description
**HIGH + LOW.**
1. `RateLimiter.get_identifier` (`app/core/rate_limiter.py:46-48`) trusts `X-Forwarded-For` from any client. Rotating the header gives unlimited login brute force, registration spam and forgot-password email bombing.
2. The count check (`:66-73`) and the insert (`:100-105`) are two separate pipelines; N concurrent requests all see `count < max` and all pass.

Client-IP resolution belongs to the ASGI server: uvicorn rewrites `request.client` from `X-Forwarded-For` only when the immediate peer is in `--forwarded-allow-ips`.

#### Technical Instructions
1. **Failing tests first** in `app/tests/test_rate_limiter.py`:
   - 11 login attempts, each with a different `X-Forwarded-For` → the 11th returns `429`.
   - `asyncio.gather` of 20 requests against a limit of 5 → exactly 5 succeed. Use `fakeredis` only if already installed; otherwise use the existing `fake_redis` helper extended with `MULTI` semantics, or mark Redis-required.
2. `get_identifier`: remove all `X-Forwarded-For` parsing; use `request.client.host if request.client else "unknown"`.
3. `__call__`: one transactional pipeline that adds first, then counts:
   ```python
   pipe.zremrangebyscore(key, 0, window_start)
   pipe.zadd(key, {member_id: now})
   pipe.zcard(key)
   pipe.zrange(key, 0, 0, withscores=True)
   pipe.expire(key, self.window_seconds + 5)
   _, _, count, oldest, _ = await pipe.execute()
   if count > self.max_requests:
       await conn.zrem(key, member_id)
       raise HTTPException(429, ...)
   ```
   Removing the rejected member keeps rejected attempts from extending the window.
4. Ops:
   - `Makefile` `dev-api` and `dev.sh`: add `--proxy-headers --forwarded-allow-ips "$${FORWARDED_ALLOW_IPS:-127.0.0.1}"`.
   - `.env.example`: document `FORWARDED_ALLOW_IPS` (set to the reverse proxy's IP; never `*` on an internet-facing port).

#### Files Touched
- `apps/api/app/core/rate_limiter.py` (Modified)
- `apps/api/app/tests/test_rate_limiter.py` (Modified)
- `Makefile` (Modified)
- `dev.sh` (Modified)
- `.env.example` (Modified)

#### Verification Strategy
- Command: `cd apps/api && .venv/bin/pytest app/tests/test_rate_limiter.py app/tests/test_auth_api.py -v && cd ../.. && make lint-api && make typecheck-api`

#### Prepared Git Commit
```text
fix(security): stop trusting X-Forwarded-For and make rate limiting atomic

- Identify unauthenticated clients by request.client.host only; proxy
  headers are resolved by uvicorn --forwarded-allow-ips
- Add, count and expire in a single Redis transaction and remove the
  member when the request is rejected
- Configure proxy headers in Makefile/dev.sh and document
  FORWARDED_ALLOW_IPS in .env.example
- Add header-spoofing and concurrency regression tests
- Verification: pytest test_rate_limiter.py test_auth_api.py,
  make lint-api, make typecheck-api passed
```
