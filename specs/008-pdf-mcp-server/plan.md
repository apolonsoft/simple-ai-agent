# Technical Architecture & Plan: PDF Creation MCP Server

## 1. Architecture Overview
The system follows the FastMCP architecture standard used in `apps/api/app/mcp_servers/tavily_server.py`.

```
                    +-----------------------+
                    |  chat_stream_service  |
                    +-----------------------+
                               |
                               v
                    +-----------------------+
                    |   McpClientService    |
                    +-----------------------+
                     /                     \
                    / (SSE:8001)            \ (SSE:8002)
                   v                         v
        +---------------------+   +---------------------+
        |  tavily_server.py   |   |    pdf_server.py    |
        +---------------------+   +---------------------+
                                             |
                                  +----------+----------+
                                  |                     |
                                  v                     v
                              [ fpdf2 ]             [ pypdf ]
                                (PDF)                 (PDF)
```

## 2. Affected Files & Schema
- `apps/api/pyproject.toml`: Add dependencies `fpdf2>=2.8.2` and `pypdf>=5.1.0`.
- `apps/api/app/core/config.py`: Add settings `MCP_PDF_URL: str = "http://127.0.0.1:8002/sse"` and `MCP_PDF_DIR: str = "outputs/pdfs"`.
- `apps/api/app/services/mcp_client_service.py`: Refactor to accept `server_urls: list[str] | str | None` and aggregate tools.
- `apps/api/app/mcp_servers/pdf_server.py`: New MCP server providing `create_pdf`, `merge_pdfs`, and `inspect_pdf`.
- `apps/api/app/tests/test_pdf_server.py`: New unit tests for PDF tools.
- `apps/api/app/tests/test_mcp_client.py`: Update/extend unit tests for multi-server aggregation.

## 3. Tool Schemas
- `create_pdf`:
  - `title` (str): Title of the document.
  - `content` (str): Body content formatted in Markdown or plain text.
  - `filename` (str, optional): Target file name (defaults to slugified title + timestamp).
  - `author` (str, optional): Author name in PDF metadata.
- `merge_pdfs`:
  - `file_paths` (list[str]): List of absolute or relative paths of existing PDFs.
  - `output_filename` (str, optional): Target merged file name.
- `inspect_pdf`:
  - `file_path` (str): Path of the PDF to inspect.
