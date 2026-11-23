### Task 15: Accept JWTs Only from the Authorization Header

- [x] Completed

**Lesson:** [07 — Session revocation and fail-open vs fail-closed](../lessons/lesson-07-session-revocation-and-failure-modes.md)

#### Full Description
**MEDIUM.** `get_current_user` (`app/core/dependencies.py:20,29`) accepts a JWT from `?token=` on every protected endpoint. The frontend never uses it (it sends `Authorization: Bearer`; the only `?token=` is the unrelated reset-token endpoint). Tokens in URLs leak into access logs, proxy logs, browser history and `Referer` headers.

#### Technical Instructions
1. **Failing test first** in `app/tests/test_auth_api.py`: `GET /api/v1/auth/me?token=<valid>` with no header → `401`.
2. Remove the `query_token` parameter; `token = header_token`.
3. Check `app/tests/test_pdf_download_api.py` and any test using `?token=` and switch them to headers.
4. Confirm `GET /auth/verify-reset-token?token=` still works (it's a separate `Query` on that route, not this dependency).

#### Files Touched
- `apps/api/app/core/dependencies.py` (Modified)
- `apps/api/app/tests/test_auth_api.py` (Modified)
- `apps/api/app/tests/test_pdf_download_api.py` (Modified — only if it uses `?token=`)

#### Verification Strategy
- Command: `make test-api && make lint-api && make typecheck-api && make test-web`

#### Prepared Git Commit
```text
fix(auth): accept access tokens only from the Authorization header

- Remove the ?token= query parameter from get_current_user so JWTs are
  never carried in URLs
- Add regression test rejecting query-string tokens
- Verification: make test-api, make lint-api, make typecheck-api,
  make test-web passed

BREAKING CHANGE: protected endpoints no longer accept ?token=.
```
