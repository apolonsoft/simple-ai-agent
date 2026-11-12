# Enterprise Scalable AI Agent Monorepo

An enterprise-grade, high-concurrency, full-stack AI Agent application designed for multi-tenant real-time streaming conversations. Built with a decoupled monorepo architecture featuring a **FastAPI (Python 3.10)** asynchronous backend and an **Angular 22** standalone frontend powered by Angular Signals.

> 📖 **Deep Dive Code Walkthrough**: For an exhaustive line-by-line breakdown of every service, database transaction decoupling, streaming algorithm, and security logic, refer to [`docs/ARCHITECTURE_AND_CODE_WALKTHROUGH.md`](docs/ARCHITECTURE_AND_CODE_WALKTHROUGH.md).

---

## Architecture Overview

```mermaid
flowchart TD
    Client["Angular 22 Client (Signals, Standalone)"] -->|Reverse Proxy / Vite| API["FastAPI API Workers (Stateless, Async)"]

    subgraph Data & Persistence
        API -->|AsyncPG Connection Pool| PG[(PostgreSQL 16: Users, Sessions, Messages)]
        API -->|Sliding-Window Rate Limiting & Context Cache| Redis[(Redis 7+)]
    end

    subgraph Pluggable LLM Strategy Layer
        API -->|Strategy Pattern| LLMFactory["LLM Provider Factory"]
        LLMFactory -->|Cloud SSE Stream| Gemini["Google Gemini API"]
        LLMFactory -->|Local Engine Stream| Ollama["Ollama Local Instance"]
    end
```

---

## Key Features & Highlights

### ⚡ Backend Architecture (FastAPI & AsyncPG)
- **Database Connection Decoupling During Long Streams**: LLM inference takes 5–30 seconds. The streaming coordinator uses a 2-phase decoupled transaction pattern, releasing database connections back to the `asyncpg` pool during token generation. This guarantees zero connection starvation under heavy concurrency.
- **Pluggable LLM Strategy Layer**: Switch seamlessly between cloud providers (**Google Gemini API**) and self-hosted on-premise engines (**Ollama**) using a unified `BaseLLMProvider` interface.
- **Human-in-the-Loop Tool Calling & Dynamic Introspection Layer**: Built-in tool calling framework supporting dynamic schema generation from native Python functions (`function_to_tool_definition`), callable dispatch (`tool_execution`), autonomous agent loops, arithmetic `calculator` tools, and web search (`search_web` via Tavily). In the web platform, LLM tool call requests are safely held until explicitly approved or rejected by the user in the frontend, preventing unauthorized tool execution.
- **Distributed Redis Rate Limiter**: ZSET-based sliding-window rate limiting per authenticated user or IP address with automatic `Retry-After` calculation and fail-open resilience.
- **Redis Turn Context Caching**: Active conversation turns are cached in Redis with a 1-hour sliding TTL, completely eliminating PostgreSQL `SELECT` query contention during multi-turn exchanges.
- **Context Memory Manager**: Sliding-window context pruner (`MemoryManager`) that automatically truncates older turns, preventing token context blowouts and runaway inference costs.
- **Enterprise Security**: Argon2id non-blocking password hashing and OAuth2 JWT authentication with strict row-level multi-tenant data isolation.

### 💻 Frontend Architecture (Angular 22)
- **Modern Angular Signals**: Fine-grained reactive state for sessions, active thread, loading states, tool execution states, and live streaming tokens without RxJS boilerplate.
- **Real-Time SSE Streaming Consumer**: Built using native `ReadableStreamDefaultReader` with boundary chunk buffering, token-by-token live UI updates, and an `AbortController` stop trigger.
- **Interactive Tool Approval Cards**: Real-time rendering of pending tool calls with argument inspection, live status badges (`Approval Required`, `Approved`, `Executed`, `Rejected`), and one-click user action buttons (**Approve & Run** / **Reject**).
- **Self-Contained Markdown & Code Viewer**: Safe Markdown rendering pipeline with XSS HTML sanitization, language header tags, preformatted code fences, and auto-scrolling message viewports.
- **Session Thread Sidebar**: "+ New Chat" action, thread list with active indicators, instant hover deletion, and route parameter input binding (`/chat/:sessionId`).
- **Guards & Interceptors**: Functional `authGuard` and `guestGuard` for seamless route protection, plus a functional HTTP interceptor injecting Bearer JWT tokens.

### 🧪 Comprehensive Quality & Testing (111/111 Tests Passed)
- **Code Quality & Type Safety**:
  - **[Astral Ruff](https://docs.astral.sh/ruff)**: Lightning-fast Python linting, isort import sorting, and code formatting.
  - **[Astral ty](https://docs.astral.sh/ty)**: Ultra-fast Rust-based Python type checker and language server.
- **100% Automated Test Suite**:
  - **54 Backend Pytest tests**: Async persistence, Argon2id auth, Redis rate limiting, Gemini & Ollama adapters, tool execution, dynamic function introspection (`function_to_tool_definition`), Tavily web search (`search_web`), autonomous multi-turn tool loops, approval/rejection lifecycle, context sliding window, SSE streaming generator, Redis cache hits/invalidation, and concurrent pool safety.
  - **57 Frontend Vitest tests across 12 suites**: Signal stores, streaming readers, tool call SSE events, approval/rejection workflows, Markdown parsing, component views, auth forms, interceptors, and route guards.
- **Load Testing & Concurrency Benchmark**: Automated load test tool measuring RPS, token throughput, and p50, p90, p95, and p99 latency percentiles under concurrent user load.

---

## Monorepo Directory Layout

```text
simple-ai-agent/
├── docker-compose.yml              # Local infrastructure: Postgres 16, Redis 7, Ollama
├── Makefile                        # Unified command runner (dev, test, build, benchmark)
├── docs/
│   └── ARCHITECTURE_AND_CODE_WALKTHROUGH.md # Line-by-line code explanation & design rationale
├── scripts/
│   ├── verify_infra.py             # Infrastructure & port connectivity health checker
│   └── benchmark_concurrency.py    # High-concurrency load testing & percentile reporter
├── apps/
│   ├── api/                        # FastAPI Backend Application
│   │   ├── alembic/                # Database migrations
│   │   ├── app/
│   │   │   ├── api/v1/             # Route endpoints (auth, chat)
│   │   │   ├── core/               # Redis singleton, rate limiter, security, settings
│   │   │   ├── db/                 # AsyncPG engine, pool settings, sessionmaker
│   │   │   ├── models/             # SQLAlchemy 2.0 ORM models (User, ChatSession, ChatMessage)
│   │   │   ├── providers/          # Gemini & Ollama streaming adapters
│   │   │   ├── services/           # ChatService, ChatStreamService, ChatCacheService, MemoryManager
│   │   │   ├── tools/              # Dynamic tool introspection, calculator, search & execution registry
│   │   │   └── tests/              # 54 Pytest unit and integration suites
│   │   └── pyproject.toml          # Python dependencies & tools
│   └── web/                        # Angular 22 Frontend Application
│       ├── src/
│       │   ├── app/
│       │   │   ├── core/           # AuthService, ChatService, guards, interceptors, models
│       │   │   ├── features/       # Auth (login/register) and Chat (layout, sidebar, window)
│       │   │   └── shared/         # Markdown pipe & shared styling
│       │   └── styles.scss         # Global terminal & dark mode themes
│       ├── proxy.conf.json         # Reverse proxy mapping /api to FastAPI (port 8000)
│       └── package.json            # Node dependencies
└── shared/                         # Shared schemas and interface contracts
    ├── openapi.json                # Complete auto-generated OpenAPI 3.1.0 specification
    └── types/
        └── api.ts                  # Shared TypeScript API models & event contracts
```

---

## Prerequisites

Ensure you have the following installed on your machine:
- **Docker & Docker Compose** (for PostgreSQL, Redis, Ollama)
- **Python 3.10+** (with virtual environment support)
- **Node.js 22+ or 24+** (Node `v24.15.0` recommended)
- **pnpm** (Package manager for the frontend)

---

## Quick Start (Using Makefile)

The root `Makefile` provides one-command shortcuts for all developer operations:

```bash
# 1. Start local database & cache containers (PostgreSQL, Redis, Ollama)
make up

# 2. Verify infrastructure connectivity
make verify

# 3. Apply database migrations (or: make run migrations)
make migrate

# 4. Lint and Typecheck (Astral Ruff & Astral ty)
make lint

# 5. Run full test suite (Backend Pytest + Frontend Vitest)
make test-all

# 6. Run the high-concurrency benchmark
make benchmark
```

---

## Step-by-Step Installation & Setup

### 1. Infrastructure Setup (Docker)

Start PostgreSQL, Redis, and Ollama in the background:

```bash
docker compose up -d
```

Verify all services are listening:
```bash
python3 scripts/verify_infra.py
```

---

### 2. Backend Setup (`apps/api`)

Navigate to the backend directory:
```bash
cd apps/api
```

#### a. Create & Activate Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

#### b. Install Dependencies
```bash
pip install -e ".[dev]"
```

#### c. Environment Configuration
Copy the template configuration file:
```bash
cp ../../.env.example .env
```
Key configuration values in `.env`:
```ini
ENVIRONMENT=development
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/simple_ai_agent
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-super-secret-random-jwt-key
LLM_PROVIDER=gemini        # 'gemini' or 'ollama'
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-flash
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

#### d. Apply Database Migrations
```bash
# Run migrations using Makefile alias or direct alembic:
make run migrations
# or: alembic upgrade head
```

#### e. Run Backend Tests
```bash
pytest -v
```

#### f. Start Backend Development Server
```bash
uvicorn app.main:app --reload --port 8000
```
- API Documentation (Swagger UI): `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

---

### 3. Frontend Setup (`apps/web`)

Open a new terminal and navigate to the frontend directory:
```bash
cd apps/web
```

#### a. Set Node.js Version
```bash
# If using nvm:
nvm use 24.15.0
```

#### b. Install Dependencies
```bash
pnpm install
```

#### c. Run Frontend Tests
```bash
pnpm test --watch=false
```

#### d. Build for Production
```bash
pnpm build
```

#### e. Start Frontend Development Server
```bash
pnpm start
```
The application will launch at `http://localhost:4200/`. API requests prefixed with `/api` are automatically proxied to `http://127.0.0.1:8000` via `proxy.conf.json`.

---

## Running Development Services Concurrently

From the root repository directory:

```bash
# Terminal 1: Backend
make dev-api

# Terminal 2: Frontend
make dev-web
```

Open your browser at `http://localhost:4200` to register, log in, create conversation threads, and stream responses in real time.

---

## Load Testing & Concurrency Benchmarking

The monorepo includes a load testing suite ([`scripts/benchmark_concurrency.py`](file:///home/ahmad/projects/simple-ai-agent/scripts/benchmark_concurrency.py)) to test multi-tenant throughput:

```bash
# Run benchmark with default 20 concurrent users, 3 turns each:
make benchmark

# Or configure custom concurrency:
apps/api/.venv/bin/python scripts/benchmark_concurrency.py --url http://localhost:8000 --concurrency 50 --turns 5
```

The benchmark reports:
- Total requests and global success rate ($\ge 99.0\%$ target)
- Throughput (Requests per second and Tokens per second)
- Min, Mean, p50, p90, p95, and p99 latencies for TTFB (Time to First Token) and stream durations.

---

## License

This project is licensed under the MIT License.
