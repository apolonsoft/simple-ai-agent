# Feature Specification: Admin User Management & Banning API

## 1. Overview
This specification defines the administrative REST API (`/api/v1/admin/users`) for managing system users, enforcing a two-tier administrative hierarchy (`super_admin` > `admin` > `user`), tracking ban states with dedicated database attributes, immediately terminating active user sessions via Redis revocation, and applying self-action guardrails.

---

## 2. User Stories & Acceptance Criteria

### US-1: User Listing & Querying
- **As an** `admin` or `super_admin`,
- **I want to** list all registered users with page-based pagination (`page`, `limit`), search queries (`search`), and filters (`role`, `status`),
- **So that** I can easily inspect, search, and monitor user accounts across the platform.
- **Acceptance Criteria**:
  - `GET /api/v1/admin/users` returns paginated user records (`items`, `total`, `page`, `limit`, `total_pages`).
  - Search performs case-insensitive substring matching on `email` and `full_name`.
  - Filters allow restricting by `role` (`user`, `admin`, `super_admin`) and `status` (`active`, `banned`).
  - Standard users (`role: user`) calling this endpoint receive `403 Forbidden`.

### US-2: Detailed User Inspection
- **As an** `admin` or `super_admin`,
- **I want to** retrieve full details for a specific user ID,
- **So that** I can view profile data, ban timestamps, ban reasons, and chat usage statistics.
- **Acceptance Criteria**:
  - `GET /api/v1/admin/users/{user_id}` returns user details including `chat_sessions_count`.
  - Non-existent user returns `404 Not Found`.

### US-3: Banning Users with Instant Session Revocation
- **As an** `admin` or `super_admin`,
- **I want to** ban a problematic user with an optional reason,
- **So that** their account is flagged as banned and all their active JWT sessions are immediately invalidated.
- **Acceptance Criteria**:
  - `POST /api/v1/admin/users/{user_id}/ban` sets `is_banned = True`, records `banned_at`, and stores `ban_reason`.
  - An invalidation timestamp is immediately written to Redis under `revoked_user:{user_id}`.
  - Any subsequent request by the banned user (even with an unexpired token) is rejected with `403 Forbidden` ("Account has been suspended").

### US-4: Unbanning Users
- **As an** `admin` or `super_admin`,
- **I want to** unban a previously banned user,
- **So that** their access to the platform is restored.
- **Acceptance Criteria**:
  - `POST /api/v1/admin/users/{user_id}/unban` clears `is_banned`, `banned_at`, and `ban_reason`.
  - User can log in and access protected endpoints once again.

### US-5: Role Management & Hierarchy Guardrails
- **As a** `super_admin`,
- **I want to** promote or demote user roles (`user`, `admin`, `super_admin`),
- **So that** administrative permissions are strictly managed.
- **Acceptance Criteria**:
  - `PATCH /api/v1/admin/users/{user_id}/role` requires `super_admin`. Regular `admin` receives `403 Forbidden`.
  - Regular `admin` cannot ban other `admin` or `super_admin` accounts (`403 Forbidden`).
  - Neither `admin` nor `super_admin` can ban their own account (`400 Bad Request`).
  - A `super_admin` cannot modify their own role (`400 Bad Request`).

---

## 3. Boundaries & Non-Goals
- **Non-Goal**: Frontend UI for the admin dashboard is out of scope for this API phase.
- **Non-Goal**: Hard database deletion of user records is intentionally excluded to preserve chat logs and audit trails.
