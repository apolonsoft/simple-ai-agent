### Task 06: Sandbox PDF Tool File Access

- [ ] Pending

**Lesson:** [08 — Agent tools are untrusted input](../lessons/lesson-08-sandboxing-agent-tools.md)

#### Full Description
**HIGH.** `merge_pdfs` and `inspect_pdf` (`app/mcp_servers/pdf_server.py:239-247`, `:287-296`) accept arbitrary filesystem paths from LLM-generated arguments. They are also registered in-process (`app/tools/calculator.py:31-37`) and run by `execute_tool` (`app/services/chat_stream_service.py:336`). A user can probe file existence anywhere, read any PDF on the host, and copy it into the shared download directory. `create_pdf` with a user-chosen `filename` overwrites other users' files (`pdf_server.py:94-95`).

#### Technical Instructions
1. **Failing tests first** in `app/tests/test_pdf_server.py`:
   - `inspect_pdf("/etc/passwd")` and `inspect_pdf("../../x.pdf")` → `status: error`, message does **not** echo the path or reveal existence.
   - `merge_pdfs(["/tmp/outside.pdf"])` → error.
   - Two `create_pdf(filename="report.pdf")` calls → two different files.
2. In `pdf_server.py` add:
   ```python
   def _resolve_in_output_dir(path: str) -> str | None:
       base = os.path.realpath(_get_output_dir())
       candidate = os.path.realpath(os.path.join(base, os.path.basename(path)))
       if os.path.commonpath([base, candidate]) != base or not candidate.lower().endswith(".pdf"):
           return None
       return candidate
   ```
   Accept only bare filenames (as returned in `filename` by `create_pdf`), never absolute paths.
3. Use it in `inspect_pdf` and for every element in `merge_pdfs`. On `None` or missing file return `{"status": "error", "error": "PDF not found."}`.
4. `_sanitize_filename`: always append `_<uuid4 hex[:12]>` before `.pdf`, even when a name is given. Open the target with mode `"xb"` so an existing file is never overwritten.
5. Update tool docstrings: "`file_path`: filename returned by create_pdf" — the docstring becomes the LLM tool description.
6. Stop returning absolute `file_path` / `merged_file_path` in tool results; return `filename` and `download_url` only (absolute server paths are an information leak into chat history).

#### Files Touched
- `apps/api/app/mcp_servers/pdf_server.py` (Modified)
- `apps/api/app/tests/test_pdf_server.py` (Modified)

#### Verification Strategy
- Command: `cd apps/api && .venv/bin/pytest app/tests/test_pdf_server.py app/tests/test_pdf_download_api.py -v && cd ../.. && make lint-api && make typecheck-api`

#### Prepared Git Commit
```text
fix(tools): confine PDF tools to the output directory

- Add _resolve_in_output_dir and reject paths outside the PDF directory
  in inspect_pdf and merge_pdfs
- Always add a random suffix to generated filenames and refuse to
  overwrite existing files
- Stop exposing absolute server paths in tool results
- Add tests for traversal, absolute paths and filename collisions
- Verification: pytest test_pdf_server.py test_pdf_download_api.py,
  make lint-api, make typecheck-api passed
```
