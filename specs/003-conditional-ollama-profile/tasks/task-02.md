### Task 02: Update Infrastructure Verification Script and Documentation

- [x] Completed

#### Full Description
Update `scripts/verify_infra.py` to inspect `COMPOSE_PROFILES` from environment or `.env` and conditionally verify Ollama port `11434` only when active. Update `README.md` to explain how to enable local Ollama.

#### Technical Instructions
1. In `scripts/verify_infra.py`, add logic to determine whether Ollama is enabled by checking `os.getenv("COMPOSE_PROFILES")` and reading `.env` if needed.
2. In `check_services()` of `scripts/verify_infra.py`:
   - If `ollama` is in active profiles, run `check_port("localhost", 11434, "Ollama")`.
   - Otherwise, display an informational note: `  ℹ️  Ollama service is inactive (COMPOSE_PROFILES does not include 'ollama')`.
3. In `README.md`, update Docker / Quickstart documentation explaining that Ollama is managed under the `ollama` profile and activated via `COMPOSE_PROFILES=ollama`.

#### Files Touched
- `scripts/verify_infra.py` (Modified)
- `README.md` (Modified)

#### Verification Strategy
```bash
python3 scripts/verify_infra.py
COMPOSE_PROFILES=ollama python3 scripts/verify_infra.py
```

#### Prepared Git Commit
```text
docs(infra): update verification script and readme for ollama profile

- Update scripts/verify_infra.py to conditionally check Ollama port 11434
- Document COMPOSE_PROFILES=ollama in README.md
- Verification command passed: python3 scripts/verify_infra.py in both profile modes
```
