.PHONY: help up down logs verify test-api dev-api dev

help:
	@echo "Available commands:"
	@echo "  make up         - Start local infrastructure (Postgres, Redis, Ollama)"
	@echo "  make down       - Stop local infrastructure"
	@echo "  make logs       - Tail logs for all containers"
	@echo "  make verify     - Verify monorepo layout and service connectivity"
	@echo "  make dev        - Run both backend and frontend development servers"
	@echo "  make dev-api    - Run FastAPI backend development server"

dev:
	./dev.sh

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

verify:
	python3 scripts/verify_infra.py

dev-api:
	cd apps/api && python3 -m uvicorn app.main:app --reload --port 8000
