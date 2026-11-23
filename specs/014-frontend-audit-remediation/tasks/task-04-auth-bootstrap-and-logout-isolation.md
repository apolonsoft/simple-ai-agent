### Task 04: Harden Auth Bootstrap, Token Expiry & Multi-Store Logout Reset

- [x] Completed

#### Full Description
**HIGH (Audit Findings #5 & #7).**
1. `AuthService` fires an unshared `getMe().subscribe()` in its constructor (`auth.service.ts:20, 45`), causing duplicate `GET /api/v1/auth/me` calls on `/admin` refresh alongside `adminGuard` and stray requests in unit tests.
2. `authGuard` (`auth.guard.ts:9`) only checks truthiness of `localStorage.getItem('token')`, letting expired or malformed JWTs mount protected components and fire failing API calls.
3. `AuthService.logout()` never clears `ChatService` or `AdminService` singleton signals (multi-account data bleed in the same tab), and `authInterceptor` (`auth.interceptor.ts:21–26`) only deletes `localStorage.token` on `401` without clearing `currentUser()` or feature stores.

#### Technical Instructions
1. **Write failing tests first** in `auth.service.spec.ts`, `auth.guard.spec.ts`, `admin.guard.spec.ts`, and `auth.interceptor.spec.ts`:
   - `getToken()` returns `null` and removes the stored item when the JWT's `exp` claim is in the past; valid JWTs (and opaque test tokens without 3 dot-separated parts if used in legacy tests—check existing specs first!) behave predictably:
     - *Important compatibility check:* inspect `auth.guard.spec.ts`, `admin.guard.spec.ts`, and `auth.service.spec.ts` for fake tokens like `'fake-jwt-token'`. Validate `exp` whenever the token is a 3-part JWT with a JSON payload containing numeric `exp` (all real backend PyJWT tokens have `exp`), rejecting expired `exp * 1000 <= Date.now()`.
   - Calling `ensureCurrentUser()` concurrently from two callers issues **one** `GET /api/v1/auth/me` HTTP request (`shareReplay`).
   - Calling `logout()` aborts streams and clears `ChatService.sessions`, `ChatService.messages`, `AdminService.users`, and `AdminService.selectedUser`.
   - Receiving a `401` in `authInterceptor` clears `authService.currentUser()` and navigates to `/login`.
2. Add `resetState(): void` to:
   - `ChatService`: calls `this.abortStream()`, unsubscribes `loadMessagesSub`, resets `sessions([])`, `messages([])`, `activeSessionId(null)`, `isLoadingSessions(false)`, `isLoadingMessages(false)`, `isExecutingTool(false)`, `streamError(null)`.
   - `AdminService`: resets `users([])`, `total(0)`, `page(1)`, `totalPages(1)`, `selectedUser(null)`, `searchQuery('')`, `roleFilter('')`, `statusFilter('')`, `error(null)`, loading signals `false`.
3. Update `AuthService`:
   - Register cleanup callbacks (e.g., `registerLogoutCleanup(fn: () => void)`) called by `ChatService` and `AdminService` constructors—this avoids any circular dependency (`AuthService` ↔ `ChatService`).
   - Add `private meRequest$: Observable<User> | null = null` and `ensureCurrentUser(): Observable<User>` using `shareReplay({ bufferSize: 1, refCount: false })` cleared on completion/error/logout so `checkInitialAuth()` and `adminGuard` share one in-flight `/auth/me` call.
   - Check JWT `exp` inside `getToken()`, removing expired tokens from `localStorage`.
4. Update `adminGuard` (`admin.guard.ts:23`) to use `authService.ensureCurrentUser()`.
5. Update `authInterceptor` (`auth.interceptor.ts`):
   - Use `inject(Injector)` lazily on `401` (`injector.get(AuthService).logout()`) so there is zero `HttpClient` → `Interceptor` → `AuthService` → `HttpClient` DI cycle, while guaranteeing `401` runs the exact same full state wipe as manual logout.

#### Files Touched
- `apps/web/src/app/core/services/auth.service.ts` (Modified)
- `apps/web/src/app/core/services/auth.service.spec.ts` (Modified)
- `apps/web/src/app/core/services/chat.service.ts` (Modified)
- `apps/web/src/app/core/services/admin.service.ts` (Modified)
- `apps/web/src/app/core/guards/auth.guard.spec.ts` (Modified)
- `apps/web/src/app/core/guards/admin.guard.ts` (Modified)
- `apps/web/src/app/core/guards/admin.guard.spec.ts` (Modified)
- `apps/web/src/app/core/interceptors/auth.interceptor.ts` (Modified)
- `apps/web/src/app/core/interceptors/auth.interceptor.spec.ts` (Modified)

#### Verification Strategy
- Command: `make test-web && make build-web`
- Verify zero circular dependency warnings and all auth/guard/interceptor specs pass.

#### Prepared Git Commit
```text
fix(web): validate JWT expiry, deduplicate /auth/me and wipe stores on logout

- Check JWT exp claim in AuthService.getToken() and evict expired tokens
- Share in-flight /api/v1/auth/me requests via ensureCurrentUser() across
  startup and adminGuard
- Register resetState() hooks on ChatService and AdminService so logout
  wipes all in-memory user data and aborts active streams
- Route 401 responses in authInterceptor through AuthService.logout()
- Verification: make test-web && make build-web passed
```
