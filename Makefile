.PHONY: help up down logs verify test-api dev-api migrate migrations run-migrations run dev-web test-web build-web test-all benchmark lint lint-api format format-api typecheck-api

help:
	@echo "Available commands:"
	@echo "  make up               - Start local infrastructure (Postgres, Redis, Ollama)"
	@echo "  make down             - Stop local infrastructure"
	@echo "  make logs             - Tail logs for all containers"
	@echo "  make verify           - Verify monorepo layout and service connectivity"
	@echo "  make lint             - Run backend linter (Ruff) and type checker (ty)"
	@echo "  make format           - Auto-format backend code and resolve fixable lints (Ruff)"
	@echo "  make lint-api         - Run Ruff check and format check on FastAPI backend"
	@echo "  make format-api       - Format and autofix FastAPI backend with Ruff"
	@echo "  make typecheck-api    - Run Astral ty type checker on FastAPI backend"
	@echo "  make test-api         - Run FastAPI test suite (Pytest)"
	@echo "  make dev-api          - Run FastAPI backend development server"
	@echo "  make migrate          - Apply database migrations with Alembic"
	@echo "  make run migrations   - Apply database migrations with Alembic (alias)"
	@echo "  make dev-web          - Run Angular development server (pnpm start with proxy)"
	@echo "  make test-web         - Run Angular test suite (Vitest)"
	@echo "  make build-web        - Build production Angular frontend bundle"
	@echo "  make test-all         - Run both backend and frontend test suites"
	@echo "  make benchmark        - Run high-concurrency load benchmark"

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

verify:
	python3 scripts/verify_infra.py

# Backend
lint-api:
	cd apps/api && .venv/bin/ruff check . && .venv/bin/ruff format --check .

format-api:
	cd apps/api && .venv/bin/ruff format . && .venv/bin/ruff check --fix .

typecheck-api:
	cd apps/api && .venv/bin/ty check

lint: lint-api typecheck-api

format: format-api

test-api:
	cd apps/api && .venv/bin/pytest -v

migrate migrations run-migrations:
	cd apps/api && .venv/bin/alembic upgrade head

run:
	@:

dev-api:
	cd apps/api && .venv/bin/uvicorn app.main:app --reload --port 8000

# Frontend (using sandboxed pnpm and node 24)
dev-web:
	NG_CLI_ANALYTICS=false PATH="$(PWD)/.bin:$$PATH" pnpm --prefix apps/web start

test-web:
	NG_CLI_ANALYTICS=false PATH="$(PWD)/.bin:$$PATH" pnpm --prefix apps/web test --watch=false

build-web:
	NG_CLI_ANALYTICS=false PATH="$(PWD)/.bin:$$PATH" pnpm --prefix apps/web build

# Monorepo CI verification
test-all: test-api test-web

# High-concurrency benchmark load test
benchmark:
	apps/api/.venv/bin/python scripts/benchmark_concurrency.py
