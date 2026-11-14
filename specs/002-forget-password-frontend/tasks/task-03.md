### Task 03: Reset Password Component & Route with Tests

- [x] Completed

#### Full Description
Create the standalone `ResetPasswordComponent` providing pre-flight token verification, single "New Password" input form (Ponytail minimal), and success state with "Sign In" button, register `/reset-password` in `app.routes.ts`, and add comprehensive unit tests.

#### Technical Instructions
1. Create `apps/web/src/app/features/auth/reset-password/reset-password.component.ts`:
   - Standalone component with `CommonModule`, `ReactiveFormsModule`, `RouterLink`.
   - Injects `AuthService`, `ActivatedRoute`, `Router`.
   - Reads `token` query param.
   - Signals: `status` ('loading' | 'valid' | 'invalid' | 'success'), `isSubmitting`, `errorMessage`.
   - `ngOnInit()` calls `authService.verifyResetToken(token)`. If invalid, sets `status.set('invalid')`.
   - Single FormControl `newPassword` with `Validators.required`, `Validators.minLength(4)`.
   - `onSubmit()` calls `authService.resetPassword(token, newPassword)`. On success, sets `status.set('success')`.
2. Create `apps/web/src/app/features/auth/reset-password/reset-password.component.html`:
   - Loading skeleton/spinner.
   - Invalid token alert with "Request new link" button.
   - Form for new password.
   - Success card with "Sign In" button.
3. Add `/reset-password` route in `apps/web/src/app/app.routes.ts` with `canActivate: [guestGuard]`.
4. Create `apps/web/src/app/features/auth/reset-password/reset-password.component.spec.ts` testing verification, invalid token, and submit flows.
5. Verify complete frontend test suite.

#### Files Touched
- `apps/web/src/app/features/auth/reset-password/reset-password.component.ts` (Created)
- `apps/web/src/app/features/auth/reset-password/reset-password.component.html` (Created)
- `apps/web/src/app/features/auth/reset-password/reset-password.component.spec.ts` (Created)
- `apps/web/src/app/app.routes.ts` (Modified)

#### Verification Strategy
```bash
NG_CLI_ANALYTICS=false PATH="$(pwd)/.bin:$PATH" pnpm --prefix apps/web test --watch=false
```

#### Prepared Git Commit
```text
feat(auth): add reset password component and route

- Create standalone ResetPasswordComponent with pre-flight token check and new password form
- Register /reset-password route guarded by guestGuard
- Add unit tests in reset-password.component.spec.ts covering loading, invalid, and success states
- Verification command passed: all frontend tests pass
```
