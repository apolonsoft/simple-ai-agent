# Spec: Conditional Ollama Container Service via Compose Profile

## Problem Statement
The Ollama container in `docker-compose.yml` runs unconditionally during `docker compose up` or `make up`, consuming significant system memory and local compute even when the user chooses external LLM providers (e.g. Gemini via `LLM_PROVIDER=gemini`). Users need a flag in `.env` to enable Ollama on demand, keeping it dormant by default.

## User Stories & Acceptance Criteria

### User Stories
1. **As a developer using cloud LLMs (Gemini)**, I want `docker compose up` / `make up` to launch only core databases and utilities (Postgres, Redis, Mailpit) so my machine conserves resources.
2. **As a developer using local Ollama models**, I want to enable `COMPOSE_PROFILES=ollama` in `.env` so `docker compose up` automatically includes and runs the Ollama container.
3. **As a maintainer**, I want `scripts/verify_infra.py` to intelligently check Ollama port 11434 only when Ollama is configured to run, avoiding false warning signals.

### Acceptance Criteria
- [x] Given `COMPOSE_PROFILES` is unset or empty, `docker compose config --services` outputs only `postgres`, `redis`, and `mailpit`.
- [x] Given `COMPOSE_PROFILES=ollama`, `docker compose config --services` includes `ollama`.
- [x] Given default `.env` and `.env.example`, `COMPOSE_PROFILES=ollama` is commented out.
- [x] `scripts/verify_infra.py` checks port 11434 if and only if `ollama` is activated in `COMPOSE_PROFILES`.
- [x] Documentation in `README.md` explains how to enable local Ollama.

## Boundaries & Non-Goals
- GPU reservation settings remain as commented reference blocks in `docker-compose.yml`.
- Application backend API LLM provider selection (`LLM_PROVIDER=ollama`) remains configured separately, allowing external Ollama instances outside Docker if desired.
