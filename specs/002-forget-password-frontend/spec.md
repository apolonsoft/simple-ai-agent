# Feature Specification: Frontend Password Reset (Angular)

## 1. Overview & Problem Statement
With the backend password reset endpoints available, the Angular frontend (`apps/web`) requires user-facing screens to request password reset emails, pre-validate tokens from email links, and establish new passwords.

---

## 2. Clarifications & Architecture Decisions
- **Entry Point**: A "Forgot password?" link added to the card footer of `/login` next to "Create one".
- **Form Design (Ponytail)**: Single "New Password" input (min length 4), avoiding redundant confirm-password input bloat.
- **Pre-flight Token Verification**: Validates token on page load via `GET /api/v1/auth/verify-reset-token?token=...`, showing an invalid/expired link card if bad.
- **Post-Reset Action**: Displays a success card with a "Sign In" button navigating to `/login`.
- **Route Protection**: Both `/forgot-password` and `/reset-password` are guarded by `guestGuard`.

---

## 3. User Stories & Acceptance Criteria

### Story 1: Navigate & Request Reset Link
**As a** user who forgot their password,
**I want to** click "Forgot password?" on the login page and submit my email,
**So that** I receive a recovery link.

- **Acceptance Criteria**:
  - The login card footer contains a clickable link to `/forgot-password`.
  - `/forgot-password` provides an email input and submit button.
  - On submit, calls `AuthService.forgotPassword(email)`.
  - On response, renders a confirmation screen: "If an account with that email exists, a password reset link has been sent. Check your inbox." with a link back to `/login`.

### Story 2: Pre-validate Token & Reset Password
**As a** user arriving from an email link (`/reset-password?token=...`),
**I want to** enter a new password if the link is valid, or see an error if expired,
**So that** I can recover my account securely.

- **Acceptance Criteria**:
  - Reading `token` from URL query parameters. If missing or invalid per `AuthService.verifyResetToken(token)`, displays an error card with a "Request new link" button.
  - If token is valid, displays a form with a single "New Password" field (min length 4).
  - On submission, calls `AuthService.resetPassword(token, newPassword)`.
  - On success, displays a confirmation card with a "Sign In" button routing to `/login`.

---

## 4. Boundaries & Non-Goals
- Multi-field confirm password validation (Ponytail simplification).
- Custom password strength meters or complex regex.
