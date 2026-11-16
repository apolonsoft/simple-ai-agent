# Feature Specification: Frontend Admin User Management Interface

## 1. Overview
The Administrative User Management interface provides authenticated administrators (`admin` and `super_admin`) with complete visibility and operational control over registered platform users. The interface integrates directly with the backend REST endpoints (`/api/v1/admin/users/*`) created in Feature 011.

## 2. User Stories
- **US-01: Admin Access**: As an administrator (`admin` or `super_admin`), I want an accessible `🛡️ Admin` navigation item in the global top bar so I can navigate directly to the administration dashboard.
- **US-02: Route Protection**: As a platform security owner, I want `/admin/*` routes protected by an Angular route guard (`adminGuard`) so regular users are prevented from viewing or accessing administrative pages and are redirected to `/chat`.
- **US-03: User Directory & Search**: As an administrator, I want to view a responsive list of registered users with search (name, email) and filters (role, status) and pagination so I can locate specific accounts quickly.
- **US-04: Ban & Unban Management**: As an administrator, I want to ban abusive accounts by providing a custom reason via a modal and immediately see their status update in real time. I also want to unban previously restricted users with a single click.
- **US-05: User Detail & Metrics Inspection**: As an administrator, I want to click any user to view a dedicated inspection page (`/admin/users/:id`) detailing account metadata, avatar, join date, ban status/reason, and total chat sessions count.
- **US-06: Super Admin Role Assignment**: As a super administrator, I want to promote or demote user roles (`user`, `admin`, `super_admin`) via an interactive role selector while regular administrators only see read-only badges. Guardrails prevent self-demotion.

## 3. Scope Boundaries & Non-Goals
- **In Scope**:
  - `AdminGuard` protecting all `/admin/*` child routes.
  - `AdminService` utilizing Angular Signals for state management (users list, search query, role filter, status filter, pagination, selected user, loading states).
  - Main users table component (`UserListComponent`) at `/admin/users` with sorting/filter controls and ban modal.
  - Dedicated user detail component (`UserDetailComponent`) at `/admin/users/:id` with usage metrics.
  - Top header navigation pill `🛡️ Admin` in `ChatLayoutComponent`.
  - Comprehensive unit test coverage for guard, service, and components.
- **Out of Scope (Non-Goals)**:
  - User deletion (soft or hard permanent deletion).
  - Password resetting or credential tampering from admin UI.
  - Bulk multi-user selection and batch ban operations.
  - Analytics charts or activity log timelines beyond total chat sessions count.

## 4. Acceptance Criteria
1. Unauthenticated users or users with `role: 'user'` attempting to load `/admin/*` are redirected to `/chat`.
2. Users with `role: 'admin'` or `role: 'super_admin'` can access `/admin/users` and `/admin/users/:id`.
3. The top navigation bar displays a `🛡️ Admin` button only when the logged-in user is `admin` or `super_admin`.
4. The user list displays columns: Avatar/Name, Email, Role, Status, Joined Date, and Actions.
5. Searching triggers a debounced query reload; changing role or status dropdown filters updates the list with reset pagination.
6. Clicking "Ban" opens a modal prompting for a ban reason; submitting sends `POST /api/v1/admin/users/{id}/ban` and updates the user's status to `Banned`.
7. Clicking "Unban" sends `POST /api/v1/admin/users/{id}/unban` and immediately resets the ban status.
8. Only `super_admin` users see interactive role dropdowns; regular `admin` users see static role badges.
9. On `/admin/users/:id`, the admin can inspect total chat sessions count, profile information, and execute ban/unban or role updates.
10. All frontend tests pass (`make test-web`) and production build succeeds without errors (`make build-web`).
