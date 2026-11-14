# Technical Architecture & Implementation Plan: User Profile Endpoints

## 1. Architecture Overview
The user profile feature follows the existing three-tier architecture in `apps/api`:
- **Routes Layer (`app/routes/user_routes.py`)**: Defines FastAPI endpoints, validates input, handles authentication dependency via `get_current_user`.
- **Controller Layer (`app/controllers/user_controller.py`)**: Coordinates between request payloads and the service layer.
- **Service Layer (`app/services/user_service.py` & `app/services/storage_service.py`)**: Business logic for database transactions and S3 file operations.
- **Data Layer (`app/models/user.py` & Alembic)**: Database schema updates for PostgreSQL.

## 2. Affected Files
- `docker-compose.yml`: Add `seaweedfs` container service.
- `apps/api/pyproject.toml`: Add `boto3`.
- `apps/api/app/core/config.py`: Add S3 settings.
- `.env.example` / `.env`: Add S3 environment variables.
- `apps/api/app/models/user.py`: Add `full_name`, `avatar_url`, and `bio`.
- `apps/api/alembic/versions/`: New migration script.
- `apps/api/app/schemas/user.py`: Add `UserProfileResponse`, `UserProfileUpdate`.
- `apps/api/app/services/storage_service.py`: S3 storage client wrapper.
- `apps/api/app/services/user_service.py`: Profile business logic.
- `apps/api/app/controllers/user_controller.py`: Profile controller.
- `apps/api/app/routes/user_routes.py`: Profile API routes.
- `apps/api/app/main.py`: Include `user_routes.router`.
- `apps/api/app/tests/test_user_profile_api.py`: Comprehensive test suite.

## 3. Storage Architecture (SeaweedFS S3)
- Container: `chrislusf/seaweedfs:latest`
- Command: `server -s3 -dir=/data`
- S3 Endpoint: `http://localhost:8333`
- Default bucket: `avatars`
- Service interaction via `boto3.client("s3")` executed inside `asyncio.to_thread` for non-blocking I/O.
