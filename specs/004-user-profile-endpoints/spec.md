# Feature Specification: User Profile Endpoints & SeaweedFS S3 Storage

## 1. Overview & Context
This specification outlines the backend requirements for user profile management endpoints in the Simple AI Agent platform, and the integration of SeaweedFS as a lightweight, Apache 2.0-licensed S3-compatible object store replacing MinIO.

## 2. User Stories
- **View Profile**: As an authenticated user, I want to retrieve my full profile information (`email`, `role`, `is_active`, `full_name`, `avatar_url`, `bio`, timestamps) so that my client application can display my identity.
- **Update Profile**: As an authenticated user, I want to update my personal details (`full_name`, `bio`) to keep my information accurate.
- **Upload Avatar**: As an authenticated user, I want to upload an image file (JPEG, PNG, or WebP up to 5MB) to serve as my avatar, which gets stored in SeaweedFS S3 and updates my profile's `avatar_url`.

## 3. Scope & Boundaries
- **In Scope**:
  - SeaweedFS container definition in `docker-compose.yml` with S3 server enabled (`:8333`).
  - S3 configuration variables in `app/core/config.py`, `.env.example`, `.env`.
  - Addition of `full_name`, `avatar_url`, and `bio` columns to `UserModel` with an Alembic migration.
  - S3 storage service utilizing `boto3`.
  - User profile endpoints under `/api/v1/users/me` (`GET`, `PATCH`, `POST /avatar`).
  - Comprehensive automated tests.
- **Out of Scope (Non-Goals)**:
  - Frontend Angular UI implementation (scheduled as a separate frontend feature).
  - Public profile visibility for unauthorized visitors.
  - Image resizing / cropping or multi-resolution thumbnail generation.

## 4. Acceptance Criteria
1. `GET /api/v1/users/me` returns HTTP 200 with user's id, email, role, is_active, full_name, avatar_url, bio, and timestamps when authenticated.
2. `PATCH /api/v1/users/me` accepts partial updates for `full_name` and `bio`, returning updated profile on HTTP 200.
3. `POST /api/v1/users/me/avatar` accepts `multipart/form-data`, validates that MIME type is in `image/jpeg`, `image/png`, `image/webp`, and size <= 5MB. Uploads file to SeaweedFS S3, sets `avatar_url`, and returns updated profile.
4. Requesting profile endpoints without a valid Bearer token returns HTTP 401 Unauthorized.
5. All test suites pass with 100% test success.
