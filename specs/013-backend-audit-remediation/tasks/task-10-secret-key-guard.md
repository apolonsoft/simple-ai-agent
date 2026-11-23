### Task 10: Refuse to Start with a Default Secret Key

- [x] Completed

**Lesson:** [09 — Trusting infrastructure: headers, proxies and config](../lessons/lesson-09-trusting-infrastructure.md)

#### Full Description
**HIGH.** `Settings.SECRET_KEY` (`app/core/config.py:35`) defaults to a public string. If the environment variable is missing in production, anyone can sign a valid JWT for any user id. Make the app fail fast instead.

#### Technical Instructions
1. **Failing test first**: create `app/tests/test_config.py`:
   - `Settings(ENVIRONMENT="production", SECRET_KEY=<default>)` raises `ValidationError`.
   - `Settings(ENVIRONMENT="production", SECRET_KEY="short")` raises.
   - `Settings(ENVIRONMENT="production", SECRET_KEY="x" * 32)` succeeds.
   - `Settings(ENVIRONMENT="development")` with the default succeeds.
   - Pass `_env_file=None` so a local `.env` doesn't affect the test.
2. `app/core/config.py`:
   ```python
   _DEFAULT_SECRET_KEY = "CHANGE_THIS_TO_A_SUPER_SECRET_RANDOM_KEY_IN_PRODUCTION"
   _DEV_ENVIRONMENTS = {"development", "development_debug", "test"}

   @model_validator(mode="after")
   def _require_strong_secret(self) -> "Settings":
       if self.ENVIRONMENT not in _DEV_ENVIRONMENTS and (
           self.SECRET_KEY == _DEFAULT_SECRET_KEY or len(self.SECRET_KEY) < 32
       ):
           raise ValueError("SECRET_KEY must be set to a random value of at least 32 characters")
       return self
   ```
3. `.env.example`: replace the placeholder comment with the generation command `python -c "import secrets; print(secrets.token_urlsafe(48))"`.

#### Files Touched
- `apps/api/app/core/config.py` (Modified)
- `apps/api/app/tests/test_config.py` (Created)
- `.env.example` (Modified)

#### Verification Strategy
- Command: `cd apps/api && .venv/bin/pytest app/tests/test_config.py -v && cd ../.. && make test-api && make lint-api && make typecheck-api`

#### Prepared Git Commit
```text
fix(config): refuse to start outside development with a weak SECRET_KEY

- Add Settings model validator rejecting the default or <32 char key
  when ENVIRONMENT is not a development/test environment
- Document secret generation in .env.example
- Add config validation tests
- Verification: pytest test_config.py, make test-api, make lint-api,
  make typecheck-api passed
```
