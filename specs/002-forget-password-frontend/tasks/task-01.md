### Task 01: Core Models & AuthService Methods with Tests

- [x] Completed

#### Full Description
Add TypeScript interfaces for password reset in `user.model.ts`, implement `forgotPassword`, `verifyResetToken`, and `resetPassword` in `AuthService`, and write unit tests in `auth.service.spec.ts`.

#### Technical Instructions
1. Update `apps/web/src/app/core/models/user.model.ts`:
   - `ForgotPasswordRequest { email: string; }`
   - `ResetPasswordRequest { token: string; new_password: string; }`
   - `VerifyResetTokenResponse { valid: boolean; email?: string; }`
   - `MessageResponse { message: string; }`
2. Update `apps/web/src/app/core/services/auth.service.ts`:
   - `forgotPassword(email: string): Observable<MessageResponse>` calling `POST /api/v1/auth/forgot-password`.
   - `verifyResetToken(token: string): Observable<VerifyResetTokenResponse>` calling `GET /api/v1/auth/verify-reset-token?token=...`.
   - `resetPassword(token: string, newPassword: string): Observable<MessageResponse>` calling `POST /api/v1/auth/reset-password`.
3. Update `apps/web/src/app/core/services/auth.service.spec.ts` adding unit tests verifying each HTTP request path and payload.

#### Files Touched
- `apps/web/src/app/core/models/user.model.ts` (Modified)
- `apps/web/src/app/core/services/auth.service.ts` (Modified)
- `apps/web/src/app/core/services/auth.service.spec.ts` (Modified)

#### Verification Strategy
```bash
NG_CLI_ANALYTICS=false PATH="$(pwd)/.bin:$PATH" pnpm --prefix apps/web test --watch=false
```

#### Prepared Git Commit
```text
feat(auth): add password reset models, service methods, and unit tests

- Add ForgotPasswordRequest, ResetPasswordRequest, VerifyResetTokenResponse, and MessageResponse to user.model.ts
- Add forgotPassword, verifyResetToken, and resetPassword methods to AuthService
- Add unit tests in auth.service.spec.ts verifying endpoint contracts
- Verification command passed: pnpm test passes
```
