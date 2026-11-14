### Task 02: Forgot Password Component, Login Footer Link & Route

- [x] Completed

#### Full Description
Create the standalone `ForgotPasswordComponent` providing an email input form and confirmation screen, add a link in `LoginComponent`'s card footer, register `/forgot-password` in `app.routes.ts` protected by `guestGuard`, and add unit tests.

#### Technical Instructions
1. Add "Forgot password?" link to `apps/web/src/app/features/auth/login/login.component.html` in the card footer next to "Create one".
2. Create `apps/web/src/app/features/auth/forgot-password/forgot-password.component.ts`:
   - Standalone component with `CommonModule`, `ReactiveFormsModule`, `RouterLink`.
   - `email` FormControl with `Validators.required` and `Validators.email`.
   - Signals: `isSubmitting`, `isSent`, `errorMessage`.
   - `onSubmit()` calling `authService.forgotPassword(email)`.
3. Create `apps/web/src/app/features/auth/forgot-password/forgot-password.component.html`:
   - Form state with email input, loading spinner, and submit button.
   - Success state showing check icon, confirmation message, and "Return to Sign In" link.
4. Add `/forgot-password` route in `apps/web/src/app/app.routes.ts` with `canActivate: [guestGuard]`.
5. Create `apps/web/src/app/features/auth/forgot-password/forgot-password.component.spec.ts` testing form validity and submit flow.

#### Files Touched
- `apps/web/src/app/features/auth/login/login.component.html` (Modified)
- `apps/web/src/app/features/auth/forgot-password/forgot-password.component.ts` (Created)
- `apps/web/src/app/features/auth/forgot-password/forgot-password.component.html` (Created)
- `apps/web/src/app/features/auth/forgot-password/forgot-password.component.spec.ts` (Created)
- `apps/web/src/app/app.routes.ts` (Modified)

#### Verification Strategy
```bash
NG_CLI_ANALYTICS=false PATH="$(pwd)/.bin:$PATH" pnpm --prefix apps/web test --watch=false
```

#### Prepared Git Commit
```text
feat(auth): add forgot password component, login link, and route

- Add Forgot password link to login page card footer
- Create standalone ForgotPasswordComponent with email submission and success states
- Register /forgot-password route with guestGuard
- Add unit tests in forgot-password.component.spec.ts
- Verification command passed: pnpm test passes
```
