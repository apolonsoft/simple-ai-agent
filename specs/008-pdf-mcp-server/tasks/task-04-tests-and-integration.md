### Task 04: Implement Comprehensive Tests and Service Integration

- [x] Completed

#### Full Description
Write comprehensive pytest unit tests for the PDF MCP tools in `apps/api/app/tests/test_pdf_server.py`, add multi-server integration tests in `apps/api/app/tests/test_mcp_client.py`, and register `MCP_PDF_URL` in the default `McpClientService` client so the AI agent chat pipeline automatically discovers PDF tools.

#### Technical Instructions
1. In `apps/api/app/tests/test_pdf_server.py`:
   - Test `create_pdf`: Verify creating basic text PDF returns valid JSON, file exists, starts with `%PDF-`, and has valid page count.
   - Test `create_pdf` with custom filename and formatting.
   - Test `merge_pdfs`: Generate 2 sample PDFs, merge them, verify result has sum of pages.
   - Test `inspect_pdf`: Verify inspect returns accurate page count and metadata.
   - Test error cases: Non-existent files in merge/inspect return readable error messages rather than unhandled crashes.
2. In `apps/api/app/services/mcp_client_service.py`:
   - Include `settings.MCP_PDF_URL` in default server URL list if configured.
3. In `apps/api/app/tests/test_mcp_client.py`:
   - Add test verifying aggregation across multiple configured MCP server endpoints.
4. Run full test suite and linting.

#### Files Touched
- `apps/api/app/tests/test_pdf_server.py` (Created)
- `apps/api/app/services/mcp_client_service.py` (Modified)
- `apps/api/app/tests/test_mcp_client.py` (Modified)

#### Verification Strategy
```bash
cd apps/api && uv run pytest app/tests/test_pdf_server.py app/tests/test_mcp_client.py -v && uv run ruff check app/mcp_servers/pdf_server.py app/services/mcp_client_service.py app/tests/test_pdf_server.py
```

#### Prepared Git Commit
```text
test(mcp): add unit tests for PDF tools and multi-server MCP client integration

- Add test_pdf_server.py covering create_pdf, merge_pdfs, and inspect_pdf
- Add multi-server aggregation test in test_mcp_client.py
- Register MCP_PDF_URL in McpClientService default servers
- Verification command passed: pytest and ruff check
```
