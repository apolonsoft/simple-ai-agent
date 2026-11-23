### Task 06: Reactive User Detail Routing, Unban RBAC Guard & Shared Ban Modal

- [x] Completed

#### Full Description
**MEDIUM (Audit Findings #10, #11, #18).**
1. `UserDetailComponent` reads `route.snapshot.paramMap.get('id')` once in `ngOnInit` (`user-detail.component.ts:52`) and `AdminService.getUserDetail` never clears `selectedUser` before fetching—navigating `/admin/users/A` → `/admin/users/B` fails to reload, and errors leave User A rendered under User B's URL.
2. Both `UserListComponent` and `UserDetailComponent` render an active `Unban` button to regular `admin`s on banned `admin`/`super_admin` accounts (missing `canModerateUser` check on unban).
3. The 75-line Ban Confirmation Modal markup and state are duplicated verbatim across `user-list` and `user-detail`.

Depends on Task 01 (`admin-permissions.ts`) and Task 05 (`isLoadingDetail` / `mutatingUserId`).

#### Technical Instructions
1. **Write failing tests first** in `ban-user-modal.component.spec.ts`, `user-detail.component.spec.ts`, and `user-list.component.spec.ts`:
   - Regular `admin` viewing a banned `admin` or `super_admin` does **not** see the `Unban` / `Restore Account Access` button; `super_admin` does see it for a banned `admin`.
   - Updating the route `id` input on `UserDetailComponent` from `'user-1'` to `'user-2'` cancels any pending `'user-1'` fetch, clears stale `selectedUser`, and loads `'user-2'`.
2. Update `apps/web/src/app/core/utils/admin-permissions.ts`:
   - Rename/alias `canBanUser` → `canModerateUser` (keep `canBanUser` re-exported if needed) and apply it to **both** ban and unban actions (except `super_admin` accounts, which cannot be moderated by regular admins).
3. Create `apps/web/src/app/features/admin/ban-user-modal/ban-user-modal.component.{ts,html,spec.ts}`:
   - Inputs: `targetUser = input.required<AdminUser>()`, `isSubmitting = input<boolean>(false)`.
   - Outputs: `cancel = output<void>()`, `confirm = output<string>()` (trimmed reason).
   - Keyboard `Escape` closes modal when not submitting; includes `role="dialog"` and `aria-modal="true"`.
4. Update `AdminService.getUserDetail(userId)`:
   - Set `this.selectedUser.set(null)` on entry so stale user details never display under a new ID.
5. Update `UserDetailComponent` & `.html`:
   - Use route input binding `readonly id = input<string | null>(null)` (`withComponentInputBinding()` is enabled in `app.config.ts`) with `toObservable(this.id)` + `filter(Boolean)` + `distinctUntilChanged()` + `switchMap((id) => ...)` + `takeUntilDestroyed()` (keep fallback to `ActivatedRoute.paramMap` if existing specs provide `ActivatedRoute` instead of setting `fixture.componentRef.setInput('id', ...)`—merging `route.paramMap` ensures 100% test backward compatibility while supporting dynamic route updates!).
   - Switch template loading check from `adminService.isLoading()` to `adminService.isLoadingDetail()`, disable role/unban controls while `adminService.mutatingUserId() === u.id`, gate unban with `canBan()`, and replace inline modal HTML with `<app-ban-user-modal>`.
6. Update `UserListComponent` & `.html`:
   - Gate `Unban` button with `@if (user.is_banned && canBan(user))` and replace inline modal HTML with `<app-ban-user-modal>`.

#### Files Touched
- `apps/web/src/app/core/utils/admin-permissions.ts` (Modified)
- `apps/web/src/app/core/utils/admin-permissions.spec.ts` (Modified)
- `apps/web/src/app/core/services/admin.service.ts` (Modified)
- `apps/web/src/app/features/admin/ban-user-modal/ban-user-modal.component.ts` (Created)
- `apps/web/src/app/features/admin/ban-user-modal/ban-user-modal.component.html` (Created)
- `apps/web/src/app/features/admin/ban-user-modal/ban-user-modal.component.spec.ts` (Created)
- `apps/web/src/app/features/admin/user-detail/user-detail.component.ts` (Modified)
- `apps/web/src/app/features/admin/user-detail/user-detail.component.html` (Modified)
- `apps/web/src/app/features/admin/user-detail/user-detail.component.spec.ts` (Modified)
- `apps/web/src/app/features/admin/user-list/user-list.component.ts` (Modified)
- `apps/web/src/app/features/admin/user-list/user-list.component.html` (Modified)
- `apps/web/src/app/features/admin/user-list/user-list.component.spec.ts` (Modified)

#### Verification Strategy
- Command: `make test-web && make build-web`

#### Prepared Git Commit
```text
fix(web): make user detail route reactive, guard unban RBAC and share ban modal

- Reactively subscribe to route paramMap in UserDetailComponent with
  switchMap + takeUntilDestroyed and clear stale selectedUser before load
- Enforce admin hierarchy checks on Unban controls in both list and detail
- Use isLoadingDetail and mutatingUserId in UserDetailComponent
- Extract duplicated ban modal into standalone BanUserModalComponent
- Verification: make test-web && make build-web passed
```
