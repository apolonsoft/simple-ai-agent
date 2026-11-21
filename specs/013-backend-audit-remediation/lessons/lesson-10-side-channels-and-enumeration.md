# Lesson 10: Side Channels — What Response Time Reveals

**Pattern:** A carefully generic message ("If an account exists, we sent a link") means nothing if the response *takes longer* when the account exists. Attackers measure everything you return: body, status, headers, size, **and time**. Make the observable behavior identical across the cases you want to hide, or accept the leak deliberately.

**Applies to:** Task 18

---

## 1. The bugs in this repo

```python
# apps/api/app/controllers/auth_controller.py
async def forgot_password(self, email: str) -> MessageResponse:
    raw_token = await self.service.create_password_reset(email)
    if raw_token:
        await self.email_service.send_password_reset_email(email, raw_token)   # +100s of ms, only if registered
    return MessageResponse(message="If an account with that email exists, ...")
```

```python
# apps/api/app/services/auth_service.py
async def authenticate(self, email, password):
    user = await self.get_by_email(email)
    if not user or not verify_password(password, user.hashed_password):   # Argon2 only if user exists
        return None
```

| Endpoint | Unknown email | Known email | Difference |
|---|---|---|---|
| `/auth/forgot-password` | ~5 ms | ~5 ms + SMTP round-trip | 50–1000 ms: trivially measurable |
| `/auth/login` | ~2 ms | ~2 ms + Argon2 (~50 ms) | ~50 ms: measurable over a few samples |

## 2. Mental model: equalize the expensive branch
Find the operation that only happens in one branch, then either:
1. **do it in both branches**: verify against a dummy hash when the user doesn't exist, or
2. **take it off the response path**: send the email after the response (`BackgroundTasks`, a queue).

```python
DUMMY_PASSWORD_HASH = password_hash.hash(secrets.token_urlsafe(16))   # once, at import

user = await self.get_by_email(email)
hashed = user.hashed_password if user else DUMMY_PASSWORD_HASH
valid = await verify_password_async(password, hashed)
return user if (user and valid) else None
```

The `and` in the last line matters: the dummy hash can never authenticate anyone, even if someone guesses its password.

### Background tasks in FastAPI
`background_tasks.add_task(fn, ...)` runs after the response is sent, in the same worker. It's fine for best-effort work like email. `send_password_reset_email` already catches its own exceptions, which matters, because an exception in a background task is only logged and the client never sees it. For guaranteed delivery you'd use a durable queue. That's out of scope here.

## 3. Be honest about what you can't hide
`POST /auth/register` returns `409 Email is already registered.` That's an enumeration oracle by design, and most products accept it because telling users "you already have an account" is good UX. Mitigations are rate limiting (Task 09), or a verification-email flow where registration always says "check your inbox".

Security work is about **consistent** decisions. There's little point hardening forgot-password timing if register openly confirms the same fact. Decide on a threat model, write it down, and apply it everywhere. In this spec, the login and forgot-password timing leaks are fixed because they're cheap; register's explicit 409 is accepted and rate-limited.

## 4. Other side channels to know about
- **Status codes**: `403` vs `404` for unowned objects (Lesson 04).
- **Error text**: "user not found" vs "wrong password".
- **Response size**: different templates for different cases.
- **Rate-limit behavior**: limiting only when an account exists.
- **String comparison**: compare secrets with `hmac.compare_digest`, never `==`. Here, reset tokens are compared via an indexed SHA-256 *hash* lookup, which is fine: the attacker can't control the hash prefix.

---

## Exercises
1. Estimate how many requests an attacker needs to reliably tell a 50 ms difference apart over the internet with ±30 ms jitter.
2. After Task 18, is there *any* remaining timing difference in forgot-password? Is it worth fixing?
3. Why compute `DUMMY_PASSWORD_HASH` once at import instead of hashing a fixed string on each request?
4. Given that register returns `409`, argue for or against fixing the login timing leak at all.
5. `change_password` checks `current_password == new_password` *after* verifying the current password. Is there a side channel?

---

## Mentor Notes
1. Averaging n samples shrinks the noise by √n. To separate 50 ms from 0 against ±30 ms jitter at high confidence, roughly 5–10 samples per email are enough. Within a 10/min rate limit, an attacker checks about 1–2 emails per minute per IP. With the X-Forwarded-For bypass (Task 09), the limit doesn't apply at all. Rate limits and timing fixes reinforce each other.
2. Yes: `create_password_reset` does an `INSERT` + `COMMIT` only for existing users, around 1–3 ms. That's below internet jitter and would need many samples. Accept it, document it (the Task 18 commit does), and move on. Perfect constant-time behavior at the HTTP level is rarely worth the complexity.
3. Hashing per request doubles the work on the unknown-user path, which creates the *opposite* timing signal, and wastes CPU. More subtly, the dummy hash should use the **same parameters** as real hashes so verification takes the same time. Hashing once at startup with the same `PasswordHash.recommended()` guarantees that.
4. For fixing: cost is near zero, and login is where credential stuffing happens. Attackers with a breached list want to filter for *registered* emails first, and register-probing creates accounts as a side effect that you can detect and block. Against: the information is already available via register. Reasonable conclusion: fix it because it's cheap, but don't pretend email existence is secret.
5. No meaningful channel. The caller is already authenticated as that user, so there's nothing to enumerate. Side channels matter when they cross a privilege boundary.

## Review Checklist
- [ ] Do "does X exist?" branches have equal cost on the response path?
- [ ] Is best-effort slow work (email, webhooks) moved off the response path?
- [ ] Are secret comparisons constant-time or hash-indexed?
- [ ] Is the enumeration stance consistent across register, login and forgot-password, and written down?
