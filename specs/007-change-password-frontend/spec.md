# Feature Specification: Change Password Frontend with Strength Meter

## 1. Overview & Context
This specification outlines the frontend implementation for authenticated password changing in the Simple AI Agent Angular web application, featuring an integrated "Security & Credentials" card on the `/profile` page, real-time 4-segment password strength feedback, client-side confirmation matching, and post-revocation session cleanup.

## 2. User Stories
- **Change Password**: As an authenticated user on my profile page, I want to update my password by providing my current password and a new password so that I can maintain account security.
- **Password Strength Feedback**: As a user typing a new password, I want real-time visual feedback on its strength (length, uppercase, lowercase, numbers, symbols) so that I choose a resilient password.
- **Confirmation Match Validation**: As a user entering a new password, I want the interface to verify that my confirmation password matches before submitting so that I don't lock myself out with a typo.
- **Session Transition**: As a user whose password was successfully changed, I want to see a confirmation banner and be cleanly redirected to `/login` to authenticate with my new credentials.

## 3. Scope & Boundaries
- **In Scope**:
  - `ChangePasswordRequest` interface in `user.model.ts`.
  - `AuthService.changePassword` HTTP method calling `POST /api/v1/auth/change-password`.
  - Adding "Security & Credentials" card to `/profile`.
  - 4-segment strength meter (Weak / Fair / Good / Strong).
  - Client-side confirmation matching validator.
  - 2-second notice before invoking `authService.logout()`.
  - Unit and component tests in Angular CLI / Vitest.
- **Out of Scope (Non-Goals)**:
  - Separate `/change-password` route (integrated directly in `/profile`).
  - Third-party bloated password strength dependencies.
  - Password visibility toggle icons (can be added optionally).

## 4. Acceptance Criteria
1. The `/profile` page displays a "Security & Credentials" card with inputs for Current Password, New Password, and Confirm Password.
2. Typing into `new_password` updates the 4-segment strength meter in real time.
3. Submitting with mismatched passwords or new password < 6 characters displays a client-side validation error without calling the backend.
4. Submitting valid passwords calls `POST /api/v1/auth/change-password` and displays a success alert.
5. After 2 seconds following successful password change, `authService.logout()` is called and the user is redirected to `/login`.
6. All automated unit and component tests pass with 0 errors.
