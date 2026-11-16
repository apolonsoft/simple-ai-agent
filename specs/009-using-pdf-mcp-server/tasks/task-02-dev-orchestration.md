### Task 02: Development Orchestration in dev.sh and Makefile

- [ ] Pending

#### Full Description
Add automated orchestration for the PDF MCP server (`apps/api/app/mcp_servers/pdf_server.py`) into the monorepo local development scripts (`dev.sh` and `Makefile`). Running `./dev.sh` will automatically launch the PDF MCP server on port `8002` alongside FastAPI, the Tavily MCP server, and the web app, and ensure clean process termination upon exit.

#### Technical Instructions
1. In `dev.sh`:
   - Add a step to launch the PDF MCP server:
     ```bash
     echo -e "${GREEN}📄 [MCP Server] Starting PDF Tools MCP Server at http://localhost:8002/sse ...${NC}"
     (
         cd "$ROOT_DIR/apps/api" || exit 1
         if [ -f "$ROOT_DIR/apps/api/.venv/bin/python" ]; then
             "$ROOT_DIR/apps/api/.venv/bin/python" -m app.mcp_servers.pdf_server
         elif command -v uv &>/dev/null; then
             uv run python -m app.mcp_servers.pdf_server
         else
             python3 -m app.mcp_servers.pdf_server
         fi
     ) &
     ```
2. In `Makefile`:
   - Add `dev-mcp-pdf` target:
     ```makefile
     dev-mcp-pdf:
     	cd apps/api && .venv/bin/python -m app.mcp_servers.pdf_server
     ```
   - Update `.PHONY` and `help` commands to include `dev-mcp-pdf`.
3. Verify syntax and execution.

#### Files Touched
- `dev.sh` (Modified)
- `Makefile` (Modified)

#### Verification Strategy
```bash
bash -n dev.sh && make help | grep "dev-mcp-pdf"
```

#### Prepared Git Commit
```text
feat(dev): orchestrate PDF MCP server on port 8002 in dev scripts

- Add PDF MCP server background worker to dev.sh
- Add dev-mcp-pdf target to Makefile
- Verification passed: bash syntax check and make help check
```
