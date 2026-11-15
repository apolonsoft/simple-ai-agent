# Feature Specification: PDF Creation & Manipulation MCP Server

## 1. Overview & Context
This feature introduces a dedicated Model Context Protocol (MCP) server providing PDF generation and manipulation capabilities for the AI agent backend. Using pure-Python libraries (`fpdf2` and `pypdf`), the server provides standard document generation (converting Markdown / structured text to PDF) and PDF utility actions (merge, page count/inspection) without requiring external native dependencies like Cairo or headless browsers.

## 2. User Stories
- **US-1**: As an AI Agent, I want to call a `create_pdf` MCP tool with Markdown content and title so that I can generate downloadable, formatted PDF documents for users.
- **US-2**: As an AI Agent, I want to call a `merge_pdfs` MCP tool with multiple PDF file paths so that I can combine separate PDF files into a single unified document.
- **US-3**: As an AI Agent, I want to call an `inspect_pdf` MCP tool so that I can verify page counts and metadata of generated or uploaded PDFs.
- **US-4**: As a backend developer, I want the agent's `McpClientService` to aggregate tools from multiple MCP servers (e.g., Tavily search on 8001 and PDF tools on 8002) seamlessly.

## 3. Answered Clarifications & Boundaries
- **Clarification 1 (Libraries)**: Selected `fpdf2` for document creation and `pypdf` for file inspection/merging. Both are pure-Python and require no C/system packages.
- **Clarification 2 (Scope)**: Document creation from Markdown/text with basic metadata, plus PDF merge and inspection.
- **Clarification 3 (Transport)**: FastMCP server with SSE transport running on port 8002, mirroring existing `tavily_server.py`.
- **Boundaries & Non-Goals**:
  - Full HTML/CSS rendering engine (e.g. WeasyPrint) is out of scope.
  - Complex vector drawing or PDF OCR text extraction is out of scope.
  - Direct cloud S3 upload within the MCP tool is out of scope; local paths are returned and existing app file handlers manage persistence if needed.

## 4. Acceptance Criteria
1. `fpdf2` and `pypdf` installed and available in the API environment.
2. `MCP_PDF_URL` (default `http://127.0.0.1:8002/sse`) and `MCP_PDF_DIR` (default `outputs/pdfs`) configured in settings.
3. `apps/api/app/mcp_servers/pdf_server.py` implements:
   - `create_pdf(title: str, content: str, filename: str | None, author: str | None) -> str`
   - `merge_pdfs(file_paths: list[str], output_filename: str | None) -> str`
   - `inspect_pdf(file_path: str) -> str`
4. `McpClientService` supports multiple MCP server endpoints without breaking existing single-endpoint callers.
5. All automated unit tests in `apps/api/app/tests/test_pdf_server.py` and `apps/api/app/tests/test_mcp_client.py` pass.
