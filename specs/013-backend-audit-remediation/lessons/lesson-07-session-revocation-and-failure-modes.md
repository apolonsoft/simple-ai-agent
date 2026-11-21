# Lesson 07: Session Revocation and Fail-Open vs Fail-Closed

**Pattern:** Stateless tokens can't be "logged out" without some server-side state. *Where* you keep that state decides how revocation behaves under failure. Every dependency needs an explicit decision: when it fails, do we allow (fail open) or deny (fail closed)? And that decision only works if failures are *detected quickly*.

**Applies to:** Task 01 (refactor), Task 11 (DB revocation), Task 13 (Redis timeouts), Task 15 (tokens in URLs)

---

## 1. The bugs in this repo

```python
# apps/api/app/core/dependencies.py
try:
    revoked_at = await redis.get(f"revoked_user:{user_id}")
    ...
except Exception:
    pass          # Redis error → revocation check silently skipped
```

Four ways the current design lets a revoked token through:
1. **Redis down** → check skipped (fail-open).
2. **Redis saturated** → the non-blocking pool raises at 51 concurrent operations → check skipped. Revocation turns off *under load*, which is exactly when an attacker would be active.
3. **Redis hung** → no socket timeout → requests hang forever. Fail-open never even triggers.
4. **Logic gaps**: password reset never writes revocation; unban *deletes* it, which revives tokens issued before a ban **or** a password change.

## 2. Mental model: revocation strategies for JWTs

| Strategy | State | Check cost | Trade-off |
|---|---|---|---|
| Short expiry (5–15 min) + refresh token | Refresh tokens server-side | None for access tokens | Revocation delay = access-token lifetime; more client logic |
| Denylist by `jti` | One entry per revoked token | One lookup per request | Must store every revoked token until it expires |
| **Per-user "valid after" timestamp** | One field per user | Free if you already load the user | Revokes *all* of a user's sessions at once |
| Session table (opaque tokens) | One row per session | One lookup per request | Most control; it's just sessions again |

This app already loads the user row on every request (`get_current_user`). A `tokens_valid_after` column gives the third strategy **for free**, with Postgres-grade durability and no extra dependency. That's Task 11.

```python
if user.tokens_valid_after and int(payload["iat"]) < int(user.tokens_valid_after.timestamp()):
    raise HTTPException(401, "Session revoked. Please log in again.")
```

## 3. Mental model: fail-open vs fail-closed
Ask: *what is this dependency protecting, and what happens if I skip it?*

| Control | If skipped | Decision |
|---|---|---|
| Chat history cache | Extra DB read | **Fail open**: it's an optimization |
| Rate limiter | Abuse is briefly possible | **Fail open**, usually, plus alerting. Security-sensitive limits (login) might fail closed |
| Token revocation | A stolen token works | **Fail closed**, or don't depend on the flaky component at all |
| Authorization | Anyone can do anything | **Always fail closed** |

`AGENT.md` invariant 4 says "Redis must fail open". That's right for caching and rate limiting, but it was applied to a security control by accident. The fix isn't to flip revocation to fail-closed on Redis, which would make Redis outages lock everyone out. It's to **move revocation to the store you already depend on**.

## 4. Fail-open only works with fast failure
A dependency that *hangs* is worse than one that's down: your `except` never runs. Every network client needs:
- a **connect timeout**,
- a **read/socket timeout**,
- a **pool wait timeout**, using a blocking pool so bursts queue briefly instead of erroring instantly.

For Redis on a LAN, sub-second values (0.2–0.5 s) are appropriate (Task 13). A cache lookup that takes 2 seconds has already failed at its job.

## 5. Tokens in URLs
`get_current_user` also accepts `?token=`. Query strings end up in uvicorn and proxy access logs, browser history, `Referer` headers, and analytics. A JWT there is a credential written to disk in plaintext. Credentials belong in headers (Task 15). The reset-token link in email is a deliberate exception: it's single-use, short-lived, and has no other delivery channel.

## 6. Why refactor first (Task 01)
Revocation logic lived in three files with three TTLs (24 h, 30 days, delete). Changing the storage model in three places at once is how you introduce the *next* bug. Consolidating first with zero behavior change, verified by unchanged tests, makes Task 11 a one-module change. That's the "preparatory refactoring" rule in `.agent/rules/single-file-tasks.md`.

---

## Exercises
1. Walk through the unban token-resurrection bug step by step, starting from "attacker steals a token".
2. `iat` has one-second resolution. A user changes their password at `12:00:00.300` and immediately logs in at `12:00:00.900`. Is their new token valid? Is an attacker's token minted at `12:00:00.100` valid? Is that acceptable?
3. Why does `ban_user` already work even when Redis is down? What does that tell you about where the ban really lives?
4. Make the case *for* failing the rate limiter closed on `/auth/login` only. What's the risk?
5. After Task 11, should `revoked_user:*` keys be migrated or deleted? What's the safe rollout?

---

## Mentor Notes
1. The attacker steals token T, issued at t0. The victim notices and changes their password at t1, which writes `revoked_user = t1`, so T is rejected. Later an admin bans the victim for unrelated reasons, overwriting the key with t2, and then unbans them, which **deletes the key**. Now there's no revocation record, T's `iat` t0 isn't compared against anything, and T works again until its 24 h `exp`.
2. Revocation stores `int(now)` = `12:00:00`, so `revoked_at = 43200` (seconds of day, for illustration). The new token's `iat` is also `43200`; `43200 < 43200` is false, so it's **valid**, which is good. The attacker's token minted in the same second also has `iat = 43200` and is **also valid**. The window is under one second and requires the attacker to mint a token *within the same second* as the change. That's acceptable. Using milliseconds in both `iat` and the column would close it, at the cost of a non-standard `iat`.
3. `get_current_user` checks `user.is_banned` from the **database row**. The Redis key was redundant for bans. The real source of truth was already Postgres, a hint that revocation belonged there too.
4. For: credential-stuffing is the main threat to login, and a Redis outage is exactly when an attacker could brute-force without limits. Risk: a Redis outage then blocks *all logins*, turning a cache outage into a full auth outage. A middle ground is fail-open with an in-process fallback limiter: imperfect across workers, but bounded.
5. No migration needed. The old keys are simply no longer read and expire within 30 days. Rollout: deploy the migration (adds a nullable column, safe online), then the code. Tokens revoked *only* in Redis before deploy become valid again for at most their remaining lifetime (≤ 24 h). If that's unacceptable, backfill `tokens_valid_after` from existing keys with a one-off script using `SCAN`, never `KEYS`.

## Review Checklist
- [ ] For each external dependency: is the failure decision (open/closed) explicit and justified?
- [ ] Are security controls independent of best-effort components?
- [ ] Does every network client have connect, read and pool timeouts?
- [ ] Are credentials ever placed in URLs?
- [ ] Does every "revoke" have no "un-revoke" side effect?
