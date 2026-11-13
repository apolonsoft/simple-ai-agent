#!/usr/bin/env bash

# Resolve project root directory
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Trap Ctrl+C (SIGINT) and SIGTERM to gracefully shut down both services
cleanup() {
    echo ""
    echo "🛑 Shutting down backend and frontend..."
    trap - SIGINT SIGTERM EXIT
    kill 0 2>/dev/null
    exit 0
}
trap cleanup SIGINT SIGTERM EXIT

# Colors for log output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=======================================${NC}"
echo -e "${GREEN} Starting Simple AI Agent Dev Services ${NC}"
echo -e "${GREEN}=======================================${NC}"

# 1. Start Backend (apps/api)
echo -e "${GREEN}🚀 [Backend] Starting FastAPI at http://localhost:8000 ...${NC}"
(
    cd "$ROOT_DIR/apps/api" || exit 1
    if [ -f "$ROOT_DIR/.venv/bin/activate" ]; then
        source "$ROOT_DIR/.venv/bin/activate"
        python3 -m uvicorn app.main:app --reload --port 8000
    elif command -v uv &>/dev/null; then
        uv run fastapi dev app/main.py --port 8000
    else
        python3 -m uvicorn app.main:app --reload --port 8000
    fi
) &

# 2. Start Tavily MCP Server (apps/api/app/mcp_servers)
echo -e "${GREEN}🔧 [MCP Server] Starting Tavily Search MCP Server at http://localhost:8001/sse ...${NC}"
(
    cd "$ROOT_DIR/apps/api" || exit 1
    if [ -f "$ROOT_DIR/apps/api/.venv/bin/python" ]; then
        "$ROOT_DIR/apps/api/.venv/bin/python" -m app.mcp_servers.tavily_server
    elif command -v uv &>/dev/null; then
        uv run python -m app.mcp_servers.tavily_server
    else
        python3 -m app.mcp_servers.tavily_server
    fi
) &

# 3. Start Frontend (apps/web)
if [ -f "$ROOT_DIR/apps/web/package.json" ]; then
    echo -e "${BLUE}💻 [Frontend] Starting Web App ...${NC}"
    (
        cd "$ROOT_DIR/apps/web" || exit 1
        if [ -f "pnpm-lock.yaml" ] && command -v pnpm &>/dev/null; then
            pnpm dev
        elif [ -f "bun.lockb" ] && command -v bun &>/dev/null; then
            bun dev
        elif [ -f "yarn.lock" ] && command -v yarn &>/dev/null; then
            yarn dev
        elif command -v npm &>/dev/null; then
            npm run dev
        fi
    ) &
else
    echo -e "${YELLOW}ℹ️  [Frontend] No package.json found in apps/web yet.${NC}"
    echo -e "${YELLOW}   (Once your frontend is added to apps/web, it will start automatically)${NC}"
fi

# Keep script running and wait for background jobs
wait
