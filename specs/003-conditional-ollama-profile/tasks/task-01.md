### Task 01: Configure Docker Compose Profiles for Ollama and Update Environment Files

- [x] Completed

#### Full Description
Configure Docker Compose profiles on the `ollama` service so it does not launch by default during `docker compose up`. Add documented `COMPOSE_PROFILES` entries to `.env.example` and `.env` (commented out by default).

#### Technical Instructions
1. In `docker-compose.yml`, add `profiles: ["ollama"]` to the `ollama` service definition while preserving existing ports, volumes, and commented GPU deployment blocks.
2. In `.env.example`, add a section for Docker Compose Profiles explaining how to enable local Ollama:
   ```bash
   # Docker Compose Profiles
   # Leave empty/commented to run only core services (PostgreSQL, Redis, Mailpit).
   # Set to 'ollama' to start the local Ollama container:
   # COMPOSE_PROFILES=ollama
   ```
3. In `.env`, add the corresponding commented `COMPOSE_PROFILES=ollama` entry.
4. Verify using Docker Compose CLI that `ollama` is excluded by default and included when `COMPOSE_PROFILES=ollama`.

#### Files Touched
- `docker-compose.yml` (Modified)
- `.env.example` (Modified)
- `.env` (Modified)

#### Verification Strategy
```bash
# Verify ollama is excluded by default
docker compose config --services | grep -v ollama
# Verify ollama is included when profile is set
COMPOSE_PROFILES=ollama docker compose config --services | grep ollama
```

#### Prepared Git Commit
```text
feat(docker): make ollama service conditional via compose profile

- Add profiles: ["ollama"] to ollama service in docker-compose.yml
- Add commented COMPOSE_PROFILES=ollama setting to .env.example and .env
- Verification command passed: docker compose config service filtering
```
