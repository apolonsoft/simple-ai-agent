### Task 21: Gemini Key Header and Admin Search Escaping

- [x] Completed

**Lessons:** [09 — Trusting infrastructure: headers, proxies and config](../lessons/lesson-09-trusting-infrastructure.md), [01 — Never trust the request body](../lessons/lesson-01-trust-boundaries-and-mass-assignment.md)

#### Full Description
**LOW.**
1. `GeminiProvider` puts the API key in the URL query string (`app/providers/gemini_provider.py:96`, `:158`). httpx logs request URLs at INFO, and exceptions/tracebacks include the URL.
2. Admin search (`app/services/admin_service.py:42-49`) interpolates the term into `ilike('%term%')` without escaping `%` and `_`, so `_` matches any character and `%` matches everything.

#### Technical Instructions
1. **Failing tests first**:
   - `test_llm_providers.py`: capture the request passed to the mocked `httpx.AsyncClient.stream`; assert `"key=" not in url` and header `x-goog-api-key` equals the key.
   - `test_admin_api.py`: users `a_b@x.com` and `axb@x.com`; `search=a_b` returns only the first.
2. `gemini_provider.py`: build the URL without `key=`; pass `headers={"x-goog-api-key": self.api_key}` to `client.stream(...)` and to the health-check `client.get(...)`.
3. `admin_service.py`: use `UserModel.email.icontains(term, autoescape=True)` and the same for `full_name` (SQLAlchemy escapes `%`, `_` and the escape char).

#### Files Touched
- `apps/api/app/providers/gemini_provider.py` (Modified)
- `apps/api/app/services/admin_service.py` (Modified)
- `apps/api/app/tests/test_llm_providers.py` (Modified)
- `apps/api/app/tests/test_admin_api.py` (Modified)

#### Verification Strategy
- Command: `cd apps/api && .venv/bin/pytest app/tests/test_llm_providers.py app/tests/test_admin_api.py -v && cd ../.. && make lint-api && make typecheck-api`

#### Prepared Git Commit
```text
fix(api): send Gemini key in header and escape admin search wildcards

- Pass the Gemini API key via x-goog-api-key instead of the URL query
- Use icontains(autoescape=True) for admin email/name search
- Add tests for header usage and literal underscore search
- Verification: pytest test_llm_providers.py test_admin_api.py,
  make lint-api, make typecheck-api passed
```
