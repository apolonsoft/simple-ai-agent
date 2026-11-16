# Scalable AI Agent API

FastAPI backend with asynchronous PostgreSQL (`asyncpg`), Redis rate limiting & caching, pluggable LLM integrations (Gemini + Ollama), and Model Context Protocol (MCP) tool servers.

## Model Context Protocol (MCP) Servers

The API integrates with external and internal tool servers using the standard **Model Context Protocol (MCP 2.x)** over Server-Sent Events (SSE). The `McpClientService` automatically connects to all configured MCP endpoints, pools their tool schemas for LLM inference, and routes execution calls dynamically.

### Available MCP Servers

#### 1. PDF Creation & Manipulation Server (`app/mcp_servers/pdf_server.py`)
Provides pure-Python PDF generation and document utilities powered by `fpdf2` and `pypdf` (zero native C library dependencies).

- **Default Port**: `8002` (`http://127.0.0.1:8002/sse`)
- **Configuration**:
  - `MCP_PDF_URL`: Endpoint URL for the agent backend to connect to (default: `http://127.0.0.1:8002/sse`)
  - `MCP_PDF_DIR`: Target directory where generated PDFs are stored (default: `outputs/pdfs`)
  - `MCP_PDF_PORT`: Port to bind when running standalone (default: `8002`)
  - `MCP_PDF_HOST`: Host to bind when running standalone (default: `127.0.0.1`)

**Exposed Tools:**
- `create_pdf(title: str, content: str, filename: str | None, author: str | None) -> str`:
  Generates a cleanly formatted A4 PDF from Markdown (headings `#`, `##`, `###`, bullet lists `- `, `* `, bold `**`, italics `*`) or HTML content with running page headers and footers (`Page X/{nb}`). Returns JSON with `file_path`, `filename`, `download_url`, `page_count`, and `file_size_bytes`.
- `merge_pdfs(file_paths: list[str], output_filename: str | None) -> str`:
  Merges multiple input PDF files into a single unified document using `pypdf.PdfWriter`. Returns JSON with `merged_file_path`, `filename`, `download_url`, and `total_pages`.
- `inspect_pdf(file_path: str) -> str`:
  Extracts page count, document metadata (Title, Author, CreationDate), and a first-page text preview.

**Running the PDF Server:**
```bash
# Using uv:
../../.bin/uv run python -m app.mcp_servers.pdf_server

# Or using the local virtualenv:
python -m app.mcp_servers.pdf_server

# Or via Makefile from project root:
make dev-mcp-pdf
```

### PDF File Delivery & Download API
Generated PDFs stored in `MCP_PDF_DIR` (`outputs/pdfs`) are served via an authenticated endpoint:
- **Route**: `GET /api/v1/chats/files/pdf/{filename}`
- **Authentication**:
  - `Authorization: Bearer <access_token>` header (used by Angular HTTP client).
  - Or `?token=<access_token>` URL query parameter (enabling direct browser address bar navigations and iframe embedding).
- **Security**: Validates filename extensions (`.pdf`) and enforces canonical path confinement (`os.path.commonpath`) to block directory traversal attacks (e.g. `../../etc/passwd`).
- **Response**: Streams binary PDF content via Starlette `FileResponse` with `application/pdf` MIME type.

#### 2. Tavily Web Search Server (`app/mcp_servers/tavily_server.py`)
Provides real-time web search capability over SSE using the Tavily API.
- **Default Port**: `8001` (`http://127.0.0.1:8001/sse`)
- **Exposed Tools**: `search_web(query: str, max_results: int = 5)`

**Running the Tavily Server:**
```bash
python -m app.mcp_servers.tavily_server
```

---

## Running Tests

Run the full pytest suite including MCP client and server tests:
```bash
pytest -v
```

Run only MCP and PDF tests:
```bash
pytest app/tests/test_pdf_download_api.py app/tests/test_pdf_server.py app/tests/test_mcp_client.py -v
```
