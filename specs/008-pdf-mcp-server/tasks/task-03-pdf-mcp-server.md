### Task 03: Implement PDF MCP Server with create_pdf, merge_pdfs, and inspect_pdf

- [x] Completed

#### Full Description
Create the standalone FastMCP server `apps/api/app/mcp_servers/pdf_server.py` exposing three tools: `create_pdf`, `merge_pdfs`, and `inspect_pdf` using `fpdf2` and `pypdf`. The server supports SSE transport on port 8002 and ensures output directories are properly initialized and sanitized.

#### Technical Instructions
1. In `apps/api/app/mcp_servers/pdf_server.py`:
   - Initialize FastMCP server: `mcp = MCPServer("custom-pdf-tools")`.
   - Setup default output folder using `settings.MCP_PDF_DIR` or environment variable `MCP_PDF_DIR` (with fallback to `outputs/pdfs`). Ensure directory exists via `os.makedirs(..., exist_ok=True)`.
   - Implement `@mcp.tool() def create_pdf(title: str, content: str, filename: str | None = None, author: str | None = None) -> str`:
     - Use `fpdf.FPDF` with Unicode font support (UTF-8).
     - Set metadata (Title, Author).
     - Add page, print header/title, parse markdown/text blocks (using `fpdf.FPDF.write_html` or clean paragraph cell rendering).
     - Output PDF to sanitized filename path.
     - Return JSON or structured string with path, page count, and byte size.
   - Implement `@mcp.tool() def merge_pdfs(file_paths: list[str], output_filename: str | None = None) -> str`:
     - Use `pypdf.PdfMerger`.
     - Validate input paths exist, append each, and write to destination.
     - Return result summary with merged file path and total pages.
   - Implement `@mcp.tool() def inspect_pdf(file_path: str) -> str`:
     - Use `pypdf.PdfReader` to read page count, metadata, and outline or text snippet from first page.
     - Return structured info.
   - Provide standard `if __name__ == "__main__":` entrypoint running SSE transport on host/port from environment/settings.

#### Files Touched
- `apps/api/app/mcp_servers/pdf_server.py` (Created)

#### Verification Strategy
```bash
cd apps/api && uv run python -c "from app.mcp_servers.pdf_server import create_pdf, inspect_pdf; res = create_pdf('Test Title', 'Hello World'); print(res); print(inspect_pdf(eval(res)['file_path']))"
```

#### Prepared Git Commit
```text
feat(mcp): implement PDF MCP server with create_pdf, merge_pdfs, and inspect_pdf

- Create FastMCP server custom-pdf-tools in apps/api/app/mcp_servers/pdf_server.py
- Implement create_pdf using fpdf2 with UTF-8 and formatting support
- Implement merge_pdfs and inspect_pdf using pypdf
- Support standalone execution with SSE transport
- Verification command passed: python smoke test of create_pdf and inspect_pdf
```
