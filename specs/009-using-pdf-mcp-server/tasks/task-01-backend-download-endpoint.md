### Task 01: Backend Secure PDF Download Endpoint & Tool Payload Enhancement

- [x] Completed

#### Full Description
Implement an authenticated file delivery endpoint `GET /api/v1/chats/files/pdf/{filename}` in FastAPI. The endpoint supports both `Authorization: Bearer <token>` and `?token=<token>` query parameter authentication for direct browser address bar navigations and iframe embedding, protects against directory traversal attacks, verifies the requested file exists in `settings.MCP_PDF_DIR`, and returns a `FileResponse` with MIME type `application/pdf`. Additionally, update `pdf_server.py` so `create_pdf` and `merge_pdfs` output include `download_url: f"/api/v1/chats/files/pdf/{safe_filename}"`.

#### Technical Instructions
1. In `apps/api/app/routes/chat_routes.py`:
   - Import `FileResponse` from `starlette.responses`.
   - Add endpoint `@router.get("/files/pdf/{filename}")`.
   - Protect with `current_user: UserModel = Depends(get_current_user)`.
   - Strip directory elements using `os.path.basename(filename)`.
   - Resolve `target_path = os.path.join(pdf_dir, safe_filename)` and verify canonical path is contained in `pdf_dir`.
   - Raise `HTTPException(404, "PDF file not found.")` if file does not exist or canonical path mismatch.
   - Return `FileResponse(path=target_path, media_type="application/pdf", filename=safe_filename)`.
2. In `apps/api/app/mcp_servers/pdf_server.py`:
   - In `create_pdf` and `merge_pdfs`, add `"download_url": f"/api/v1/chats/files/pdf/{safe_filename}"` to the returned dictionary.
3. In `apps/api/app/tests/test_pdf_download_api.py`:
   - Write pytest async tests covering:
     - 401 Unauthorized when no auth token provided.
     - 404 Not Found when file does not exist.
     - 404/400 Path traversal attempts (e.g. `../../etc/passwd`).
     - 200 OK returning valid PDF binary content for an authenticated user with an existing generated PDF.
4. Run tests and static checks.

#### Files Touched
- `apps/api/app/routes/chat_routes.py` (Modified)
- `apps/api/app/mcp_servers/pdf_server.py` (Modified)
- `apps/api/app/tests/test_pdf_download_api.py` (Created)

#### Verification Strategy
```bash
cd apps/api && .venv/bin/pytest app/tests/test_pdf_download_api.py app/tests/test_pdf_server.py -v && .venv/bin/ruff check .
```

#### Prepared Git Commit
```text
feat(api): add authenticated PDF download endpoint and tool download URLs

- Add GET /api/v1/chats/files/pdf/{filename} with path traversal protection
- Include download_url in create_pdf and merge_pdfs tool output payloads
- Add comprehensive pytest coverage for authentication, traversal, and delivery
- Verification passed: pytest app/tests/test_pdf_download_api.py
```
