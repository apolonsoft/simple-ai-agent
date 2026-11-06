.PHONY: help up down logs verify test-api dev-api migrate

help:
	@echo "Available commands:"
	@echo "  make up         - Start local infrastructure (Postgres, Redis, Ollama)"
	@echo "  make down       - Stop local infrastructure"
	@echo "  make logs       - Tail logs for all containers"
	@echo "  make verify     - Verify monorepo layout and service connectivity"
	@echo "  make test-api   - Run API automated test suite (Pytest)"
	@echo "  make dev-api    - Run FastAPI backend development server"
	@echo "  make migrate    - Apply database migrations with Alembic"

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

verify:
	python3 scripts/verify_infra.py

test-api:
	cd apps/api && .venv/bin/pytest -v

migrate:
	cd apps/api && .venv/bin/alembic upgrade head

dev-api:
	cd apps/api && .venv/bin/uvicorn app.main:app --reload --port 8000
