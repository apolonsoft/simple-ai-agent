### Task 05: Add Debounced `switchMap` Search & Granular Loading in Admin List

- [ ] Pending

#### Full Description
**HIGH + MEDIUM (Audit Findings #3 & #11).**
1. `UserListComponent.onSearch` (`user-list.component.ts:60–64`) fires an uncancelled `GET /api/v1/admin/users` on every single keystroke; out-of-order responses overwrite newer search/filter/pagination state.
2. `AdminService` uses a single `isLoading` signal across `loadUsers`, `getUserDetail`, `banUser`, `unbanUser`, and `updateRole` (`admin.service.ts:28`). Any single-row role change or ban/unban flips `isLoading()` to `true`, destroying the entire users `<tbody>` and flashing a full-table spinner.

#### Technical Instructions
1. **Write failing tests first** in `admin.service.spec.ts` and `user-list.component.spec.ts`:
   - Rapidly calling `onSearch('a')`, `onSearch('al')`, `onSearch('ali')` within `250ms` dispatches only **one** HTTP request (`search=ali`).
   - If request 1 (`role=admin`) is still pending when request 2 (`role=user`) is triggered, request 1 is cancelled (`req1.cancelled === true`) and cannot overwrite `users()`.
   - Calling `updateRole`, `banUser`, or `unbanUser` sets `mutatingUserId()` without setting `isLoadingList()` or `isLoadingDetail()` to `true`.
2. Update `apps/web/src/app/core/services/admin.service.ts`:
   - Add granular signals: `readonly isLoadingList = signal(false)`, `readonly isLoadingDetail = signal(false)`, and `readonly mutatingUserId = signal<string | null>(null)`.
   - Keep `readonly isLoading = computed(() => this.isLoadingList() || this.isLoadingDetail())` (for backward compatibility until `UserDetailComponent` updates in Task 06) and use `finalize(() => ...)` so cancelled observables always reset loading flags cleanly!
   - Note: `tap` + `catchError` alone **does not** reset `isLoadingList` when `switchMap` unsubscribes an in-flight request—`finalize` is mandatory.
3. Update `apps/web/src/app/features/admin/user-list/user-list.component.ts` & `.html`:
   - Drive list fetches through two subjects (`searchInput$` with `debounceTime(250)` + `distinctUntilChanged()`, merged with immediate `reload$` for filter/page/clear/refresh actions) piped into `switchMap(() => this.adminService.loadUsers(...).pipe(catchError(...)))` + `takeUntilDestroyed()`.
   - Bind table loading skeleton to `adminService.isLoadingList()` and disable row controls while `adminService.mutatingUserId() === user.id`.

#### Files Touched
- `apps/web/src/app/core/services/admin.service.ts` (Modified)
- `apps/web/src/app/core/services/admin.service.spec.ts` (Modified)
- `apps/web/src/app/features/admin/user-list/user-list.component.ts` (Modified)
- `apps/web/src/app/features/admin/user-list/user-list.component.html` (Modified)
- `apps/web/src/app/features/admin/user-list/user-list.component.spec.ts` (Modified)

#### Verification Strategy
- Command: `make test-web && make build-web`
- Verify fake-timer debounce and `switchMap` cancellation specs pass in Vitest.

#### Prepared Git Commit
```text
fix(web): debounce admin search with switchMap and split loading signals

- Debounce admin user search (250ms) and cancel superseded list requests
  with switchMap + takeUntilDestroyed
- Use finalize() in AdminService so cancelled requests always clear loading
- Split AdminService.isLoading into isLoadingList, isLoadingDetail and
  mutatingUserId so row actions no longer tear down the users table
- Add debounce, cancellation and row-mutation loading tests
- Verification: make test-web && make build-web passed
```
