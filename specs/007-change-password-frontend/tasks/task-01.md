### Task 01: Model & AuthService Method for Change Password

- [x] Completed

#### Full Description
Export `ChangePasswordRequest` interface in `apps/web/src/app/core/models/user.model.ts`, implement `changePassword` in `AuthService`, and verify with a unit test in `auth.service.spec.ts`.

#### Technical Instructions
1. In `apps/web/src/app/core/models/user.model.ts`:
   - Export `ChangePasswordRequest` with:
     - `current_password: string;`
     - `new_password: string;`
2. In `apps/web/src/app/core/services/auth.service.ts`:
   - Implement `changePassword(req: ChangePasswordRequest): Observable<MessageResponse>`:
     - Calls `this.http.post<MessageResponse>('/api/v1/auth/change-password', req)`.
3. In `apps/web/src/app/core/services/auth.service.spec.ts`:
   - Add unit test verifying that `changePassword` sends `POST /api/v1/auth/change-password` with correct payload and returns `MessageResponse`.

#### Files Touched
- `apps/web/src/app/core/models/user.model.ts` (Modified)
- `apps/web/src/app/core/services/auth.service.ts` (Modified)
- `apps/web/src/app/core/services/auth.service.spec.ts` (Modified)

#### Verification Strategy
```bash
cd apps/web && npx ng test --no-watch
```

#### Prepared Git Commit
```text
feat(auth): add changePassword method to AuthService and model

- Export ChangePasswordRequest interface in user.model.ts
- Implement changePassword in AuthService calling /api/v1/auth/change-password
- Add unit test in auth.service.spec.ts
- Verification command passed: ng test auth service suite
```
