### Task 07: Restrict PDF Downloads to the Owner

- [ ] Pending

**Lessons:** [04 — Object-level authorization](../lessons/lesson-04-object-level-authorization.md), [08 — Agent tools are untrusted input](../lessons/lesson-08-sandboxing-agent-tools.md)

#### Full Description
**HIGH.** `GET /api/v1/chats/files/pdf/{filename}` (`app/routes/chat_routes.py:203-247`) serves any file in the shared PDF directory to any authenticated user. Its path-traversal guard is correct; the missing piece is ownership. Ownership is derived from existing data: a PDF belongs to a user if its filename appears in a tool result of a message in one of that user's sessions. No new table (see spec non-goals).

Depends on Task 06 (unguessable filenames, no absolute paths in results).

#### Technical Instructions
1. **Failing test first** in `app/tests/test_pdf_download_api.py`: user A creates a PDF via an approved `create_pdf` tool call; user B requests the filename → `404`; user A → `200`.
2. `app/services/chat_service.py`: add
   ```python
   async def user_owns_generated_file(self, user_id: uuid.UUID, filename: str) -> bool:
       stmt = (
           select(ChatMessageModel.id)
           .join(ChatSessionModel, ChatMessageModel.session_id == ChatSessionModel.id)
           .where(
               ChatSessionModel.user_id == user_id,
               ChatMessageModel.tool_calls.contains(filename),
           )
           .limit(1)
       )
   ```
   `contains` compiles to `LIKE '%…%'`; escape `%`/`_` with `autoescape=True`. The filename was already validated against `[\w\-.]` + `.pdf`.
3. `download_pdf_file`: inject `db: AsyncSession = Depends(get_db)`; after the existing traversal checks, return `404` (same message as not-found) when `user_owns_generated_file` is `False`.
4. Move `_get_pdf_dir` + validation into `app/services/pdf_file_service.py` only if the route grows past ~40 lines; otherwise keep it in place.

#### Files Touched
- `apps/api/app/routes/chat_routes.py` (Modified)
- `apps/api/app/services/chat_service.py` (Modified)
- `apps/api/app/tests/test_pdf_download_api.py` (Modified)

#### Verification Strategy
- Command: `cd apps/api && .venv/bin/pytest app/tests/test_pdf_download_api.py -v && cd ../.. && make lint-api && make typecheck-api`

#### Prepared Git Commit
```text
fix(chat): only serve generated PDFs to the user who created them

- Add ChatService.user_owns_generated_file, matching the filename against
  tool results in the caller's own sessions
- Return 404 from the PDF download endpoint for files the caller does
  not own
- Add cross-user download regression test
- Verification: pytest test_pdf_download_api.py, make lint-api,
  make typecheck-api passed
```
