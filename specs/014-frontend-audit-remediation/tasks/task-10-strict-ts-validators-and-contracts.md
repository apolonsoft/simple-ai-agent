### Task 10: Enable Strict TypeScript, Unify Form Validators & Sync Shared Contracts

- [x] Completed

#### Full Description
**LOW / Final Gate (Audit Findings #19, #20, #24).**
1. `apps/web/tsconfig.json` lacks `"strict": true` and `"strictTemplates": true`, allowing implicit `any` and template nullability bugs to bypass compilation.
2. `ResetPasswordComponent` uses `Validators.minLength(4)` while `RegisterComponent` and `ProfileComponent` use `minLength(6)` (per Clarification #3, unify to `6` now; Spec `013` Task 02 handles the backend-coordinated bump to `8`), and `ProfileComponent` displays `"Passwords do not match"` as soon as `current_password` is touched before `confirm_password` is touched (`profile.component.html:266`).
3. `shared/types/api.ts` and `apps/web/src/app/core/models/*` have drifted (`User.role: string`, `RegisterRequest.role?: string`, missing `'super_admin'`, missing admin/profile/reset interfaces).

#### Technical Instructions
1. Update `apps/web/tsconfig.json`:
   - Add `"strict": true` under `compilerOptions` and `"strictTemplates": true` under `angularCompilerOptions`.
   - Fix any resulting strict null/type errors across `src/**/*.ts`, `.html`, and `.spec.ts` (e.g., typed reactive form values, `unknown` catch variables, strict event target narrowing instead of `$any(...)` in templates).
2. Update `ResetPasswordComponent` (`.ts`, `.html`, `.spec.ts`):
   - Change `Validators.minLength(4)` → `Validators.minLength(6)` and update the validation message (`"Password must be at least 6 characters long."`).
3. Update `ProfileComponent` (`profile.component.html:266`, `.spec.ts`):
   - Gate mismatch error on `(passwordForm.get('confirm_password')?.touched || passwordForm.get('confirm_password')?.dirty) && passwordForm.hasError('passwordMismatch')`.
4. Synchronize `shared/types/api.ts` and `apps/web/src/app/core/models/{user,chat,admin}.model.ts`:
   - Narrow `User.role` to `UserRole` (`'user' | 'admin' | 'super_admin'`), remove unused client `role` from `RegisterRequest` / `UserRegisterRequest`, include `'executing' | 'failed'` in `ToolCall.status` union for forward-compatibility with Spec `013` Task 05, and align admin/profile/password-reset interfaces in `shared/types/api.ts`.
5. Mark all tasks `[x]` in `specs/014-frontend-audit-remediation/tasks.md` and `Completed` in `tasks/index.md`, and run the full monorepo verification gate.

#### Files Touched
- `apps/web/tsconfig.json` (Modified)
- `apps/web/src/app/features/auth/reset-password/reset-password.component.{ts,html,spec.ts}` (Modified)
- `apps/web/src/app/features/profile/profile.component.{html,spec.ts}` (Modified)
- `apps/web/src/app/core/models/{user,chat,admin}.model.ts` (Modified)
- `shared/types/api.ts` (Modified)
- Any `apps/web/src/**/*.ts` / `.html` requiring strict-mode type narrowing (Modified)
- `specs/014-frontend-audit-remediation/tasks.md` & `tasks/index.md` (Modified)

#### Verification Strategy
- Command: `make test-web && make build-web && make test-all && make lint`
- Zero TypeScript/template errors, zero test failures across frontend and backend, clean production bundle.

#### Prepared Git Commit
```text
chore(web): enable strict TypeScript/templates, align validators and sync types

- Enable strict and strictTemplates in apps/web/tsconfig.json and resolve
  all strict type/template checks
- Unify ResetPasswordComponent minimum password length to 6 characters and
  gate ProfileComponent mismatch error on confirm_password touch/dirty state
- Sync UserRole, ToolCall status and API DTO contracts between apps/web
  models and shared/types/api.ts
- Mark all Spec 014 remediation tasks completed
- Verification: make test-web, make build-web, make test-all, make lint passed
```
