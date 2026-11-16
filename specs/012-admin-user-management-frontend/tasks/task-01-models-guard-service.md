### Task 01: Core Admin Models, Admin Guard, and Admin Service
- [x] Completed

#### Full Description
Establish the foundational data models, authentication guard, and stateful HTTP service for the Admin User Management module. The models correspond directly to the FastAPI Pydantic schemas created in Feature 011 (`AdminUserResponse`, `AdminUserDetailResponse`, `AdminUserListResponse`, `BanUserRequest`, `UpdateUserRoleRequest`). The `AdminGuard` validates that the user is logged in and possesses `admin` or `super_admin` permissions, redirecting unauthorized users to `/chat`. The `AdminService` provides reactive signals for the user list, total count, loading state, error state, and methods for fetching, filtering, banning, unbanning, and role modifications.

#### Technical Instructions
1. **Data Models** (`apps/web/src/app/core/models/admin.model.ts`):
   - Define interfaces:
     - `AdminUser`: `id: string`, `email: string`, `full_name: string | null`, `avatar_url: string | null`, `bio: string | null`, `role: 'user' | 'admin' | 'super_admin'`, `is_active: boolean`, `is_verified: boolean`, `is_banned: boolean`, `banned_at: string | null`, `ban_reason: string | null`, `created_at: string`, `updated_at: string`.
     - `AdminUserDetail` extends `AdminUser`: `chat_sessions_count: number`.
     - `AdminUserListResponse`: `items: AdminUser[]`, `total: number`, `page: number`, `limit: number`, `total_pages: number`.
     - `BanUserRequest`: `reason: string`.
     - `UpdateUserRoleRequest`: `role: 'user' | 'admin' | 'super_admin'`.
     - `AdminUserFilter`: `search?: string`, `role?: string`, `status?: 'active' | 'banned'`, `page?: number`, `limit?: number`.

2. **Route Guard** (`apps/web/src/app/core/guards/admin.guard.ts`):
   - Implement `adminGuard: CanActivateFn`.
   - Inject `AuthService` and `Router`.
   - Check if `authService.currentUser()?.role` is `'admin'` or `'super_admin'`.
   - If user is not yet loaded in signal but token exists, call `authService.getMe()` and evaluate role.
   - If unauthorized, redirect to `/chat` and return `false`.

3. **Route Guard Unit Tests** (`apps/web/src/app/core/guards/admin.guard.spec.ts`):
   - Test allow for `admin` and `super_admin`.
   - Test reject and redirect to `/chat` for `user`.
   - Test reject and redirect to `/login` when unauthenticated.

4. **Admin Service** (`apps/web/src/app/core/services/admin.service.ts`):
   - Mark `@Injectable({ providedIn: 'root' })`.
   - Maintain signals:
     - `users = signal<AdminUser[]>([])`
     - `total = signal<number>(0)`
     - `page = signal<number>(1)`
     - `limit = signal<number>(10)`
     - `totalPages = signal<number>(1)`
     - `isLoading = signal<boolean>(false)`
     - `error = signal<string | null>(null)`
     - `selectedUser = signal<AdminUserDetail | null>(null)`
   - Implement methods:
     - `loadUsers(filter?: AdminUserFilter): Observable<AdminUserListResponse>`
     - `getUserDetail(userId: string): Observable<AdminUserDetail>`
     - `banUser(userId: string, reason: string): Observable<AdminUser>`
     - `unbanUser(userId: string): Observable<AdminUser>`
     - `updateRole(userId: string, role: string): Observable<AdminUser>`

5. **Admin Service Unit Tests** (`apps/web/src/app/core/services/admin.service.spec.ts`):
   - Test `loadUsers` sets signals.
   - Test `banUser` sends correct body and updates existing item in signals.
   - Test `unbanUser` updates status in signals.
   - Test `updateRole` updates role in signals.
   - Test error handling.

#### Files Touched
- `apps/web/src/app/core/models/admin.model.ts` (Created)
- `apps/web/src/app/core/guards/admin.guard.ts` (Created)
- `apps/web/src/app/core/guards/admin.guard.spec.ts` (Created)
- `apps/web/src/app/core/services/admin.service.ts` (Created)
- `apps/web/src/app/core/services/admin.service.spec.ts` (Created)

#### Verification Strategy
Run Vitest on the newly created guard and service tests:
```bash
pnpm --filter web test apps/web/src/app/core/guards/admin.guard.spec.ts apps/web/src/app/core/services/admin.service.spec.ts
```

#### Prepared Git Commit
```text
feat(web): add admin data models, admin guard, and admin state service

- Define TypeScript interfaces for AdminUser, AdminUserDetail, and AdminUserListResponse matching backend schemas
- Implement adminGuard with role validation ('admin' | 'super_admin') and redirect to /chat
- Implement AdminService using Angular Signals for reactive user listing, pagination, and ban/role actions
- Add unit tests for adminGuard and AdminService verifying permissions and API operations
- Verification: Vitest unit tests pass with 100% coverage
```
