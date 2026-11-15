### Task 02: Add fpdf2 and pypdf Dependencies and MCP PDF Settings

- [ ] Pending

#### Full Description
Add `fpdf2` and `pypdf` dependencies to `apps/api/pyproject.toml` and configure `MCP_PDF_URL` and `MCP_PDF_DIR` in `apps/api/app/core/config.py`.

#### Technical Instructions
1. In `apps/api/pyproject.toml`:
   - Add `"fpdf2>=2.8.2"` and `"pypdf>=5.1.0"` to the `dependencies` list.
2. Run `uv lock` or `uv sync` in `apps/api` to resolve and install the new pure-Python packages.
3. In `apps/api/app/core/config.py`:
   - Add `MCP_PDF_URL: str = "http://127.0.0.1:8002/sse"` to `Settings`.
   - Add `MCP_PDF_DIR: str = "outputs/pdfs"` to `Settings`.
4. Verify imports and configuration loading via python one-liner.

#### Files Touched
- `apps/api/pyproject.toml` (Modified)
- `apps/api/uv.lock` (Modified)
- `apps/api/app/core/config.py` (Modified)

#### Verification Strategy
```bash
cd apps/api && uv run python -c "import fpdf; import pypdf; from app.core.config import settings; print('OK', settings.MCP_PDF_URL, settings.MCP_PDF_DIR)"
```

#### Prepared Git Commit
```text
feat(config): add fpdf2 and pypdf dependencies and MCP PDF configuration

- Add fpdf2 and pypdf to dependencies in pyproject.toml
- Define MCP_PDF_URL and MCP_PDF_DIR in app/core/config.py
- Verification command passed: python import and settings check
```
