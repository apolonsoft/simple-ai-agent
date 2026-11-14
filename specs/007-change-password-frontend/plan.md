# Technical Architecture & Implementation Plan: Change Password Frontend

## 1. Architecture Overview
- **Service Layer**:
  - `user.model.ts`: `ChangePasswordRequest` interface.
  - `auth.service.ts`: `changePassword(req: ChangePasswordRequest): Observable<MessageResponse>`.
- **UI & Presentation Layer**:
  - `ProfileComponent`:
    - `passwordForm: FormGroup` with `current_password`, `new_password`, `confirm_password` and custom `passwordMatchValidator`.
    - `passwordStrength`: computed signal evaluating length, uppercase, lowercase, numbers, and symbols (0 to 4 score).
    - `onChangePassword()` handler invoking `changePassword` and scheduling `authService.logout()` after 2 seconds.
    - Minimalist 4-bar progress indicator beneath the new password input.

## 2. Affected Files
- `apps/web/src/app/core/models/user.model.ts` (Modified)
- `apps/web/src/app/core/services/auth.service.ts` (Modified)
- `apps/web/src/app/core/services/auth.service.spec.ts` (Modified)
- `apps/web/src/app/features/profile/profile.component.ts` (Modified)
- `apps/web/src/app/features/profile/profile.component.html` (Modified)
- `apps/web/src/app/features/profile/profile.component.spec.ts` (Modified)
