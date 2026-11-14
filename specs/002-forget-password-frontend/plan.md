# Technical Architecture & Implementation Plan: Frontend Password Reset

## 1. System Architecture

```mermaid
graph TD
    A["/login (Card Footer)"] -->|"Click 'Forgot password?'"| B["/forgot-password"]
    B -->|"Submit Email"| C{"AuthService.forgotPassword()"}
    C -->|"Success"| D["Display Success Card: 'Check your inbox'"]
    C -->|"Error"| E["Display Error Alert"]
    
    F["User clicks email link"] --> G["/reset-password?token=..."]
    G -->|"OnInit"| H{"AuthService.verifyResetToken(token)"}
    H -->|"Invalid / Expired"| I["Display Invalid Link Card + 'Request New Link' Button"]
    H -->|"Valid"| J["Display Reset Form (New Password input)"]
    J -->|"Submit New Password"| K{"AuthService.resetPassword(token, pass)"}
    K -->|"Success"| L["Display Success Card + 'Sign In' Button"]
    K -->|"Error"| M["Display Submission Error Alert"]
```

---

## 2. Affected Files & Schemas

### Models & Services
- `apps/web/src/app/core/models/user.model.ts`: Adds `ForgotPasswordRequest`, `ResetPasswordRequest`, `VerifyResetTokenResponse`, `MessageResponse`.
- `apps/web/src/app/core/services/auth.service.ts`: Adds `forgotPassword`, `verifyResetToken`, `resetPassword`.
- `apps/web/src/app/core/services/auth.service.spec.ts`: Unit tests for newly added methods.

### Components & Routes
- `apps/web/src/app/features/auth/login/login.component.html`: Adds footer link.
- `apps/web/src/app/features/auth/forgot-password/forgot-password.component.ts` & `.html` & `.spec.ts`: Standalone forgot password view.
- `apps/web/src/app/features/auth/reset-password/reset-password.component.ts` & `.html` & `.spec.ts`: Standalone reset password view.
- `apps/web/src/app/app.routes.ts`: Registers routes protected by `guestGuard`.
