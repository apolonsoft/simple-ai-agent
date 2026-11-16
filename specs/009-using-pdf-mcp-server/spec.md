# Feature Specification: End-to-End PDF MCP Server Integration & UI Usage

## 1. Overview & Context
Building upon the pure-Python PDF MCP server introduced in Feature 008, this feature completes the end-to-end user loop. Users chatting with the AI agent can ask to create, merge, or inspect PDF documents. The backend serves generated PDFs via an authenticated, traversal-protected streaming endpoint. The Angular client provides dedicated PDF tool cards (`📄`), an interactive 1-click download button, and a native browser modal PDF viewer. Local development scripts (`dev.sh` and `Makefile`) automatically manage the PDF MCP server alongside API and frontend services.

## 2. User Stories
- **US-1**: As an authenticated user, I want to download generated PDF documents via `/api/v1/chats/files/pdf/{filename}` securely so that only authorized users can retrieve files and arbitrary file traversal is blocked.
- **US-2**: As an AI Agent, when executing `create_pdf` or `merge_pdfs`, I want the tool result to include a `download_url` so that both the LLM and the frontend can offer immediate access to the document.
- **US-3**: As a user in the Angular chat window, I want to see a dedicated `📄` PDF icon for PDF tools, click a **View PDF** button to preview documents in a clean modal dialog, and click **Download** to save them locally.
- **US-4**: As a developer running `./dev.sh`, I want the PDF MCP server to start on port `8002` automatically alongside FastAPI and the Tavily MCP server with no manual terminal commands needed.

## 3. Answered Clarifications & Boundaries
- **Clarification 1 (File Access & Download)**: Use a secure FastAPI endpoint (`GET /api/v1/chats/files/pdf/{filename}`) requiring Bearer JWT authentication (`get_current_user`), sanitized with `os.path.basename` and confined strictly inside `settings.MCP_PDF_DIR`.
- **Clarification 2 (PDF Viewer)**: In accordance with Ponytail guidelines, use native browser iframe rendering with authenticated blob URLs (`URL.createObjectURL(blob)`) fetched via Angular's `HttpClient`. No heavy external npm packages (e.g. pdf.js).
- **Clarification 3 (Dev Process)**: Add PDF MCP server (port `8002`) to `dev.sh` and provide a `dev-mcp-pdf` target in `Makefile`.
- **Boundaries & Non-Goals**:
  - In-browser PDF editing or annotation is out of scope.
  - S3 or cloud storage integration is out of scope.

## 4. Acceptance Criteria
1. `GET /api/v1/chats/files/pdf/{filename}` returns `FileResponse` (media type `application/pdf`) for authenticated requests.
2. Unauthenticated requests return `401 Unauthorized`. Non-existent files return `404 Not Found`. Path traversal attempts (e.g., `../../etc/passwd`) return `400 Bad Request` or `404 Not Found`.
3. `pdf_server.py` `create_pdf` and `merge_pdfs` JSON output includes `download_url`.
4. `dev.sh` starts `pdf_server.py` on port `8002` on startup and terminates it gracefully on Ctrl+C.
5. Angular chat client displays `📄` icon for `create_pdf`, `merge_pdfs`, and `inspect_pdf`, provides **View PDF** modal preview and **Download** buttons, and adds a `📄 Generate PDF Report` quick prompt chip.
6. All backend pytest tests and frontend vitest tests pass with zero regressions.
