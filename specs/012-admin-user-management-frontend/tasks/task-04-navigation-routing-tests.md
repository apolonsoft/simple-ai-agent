### Task 04: Navigation Integration, Routing Configuration, and Verification
- [ ] Pending

#### Full Description
Integrate the admin subsystem into the application routing structure and navigation header. Configure `/admin` routes in `app.routes.ts` secured with `adminGuard`, lazy-loading the admin layout and child components (`/admin/users` and `/admin/users/:id`). Update `ChatLayoutComponent` top bar with a `🛡️ Admin` pill visible exclusively to users with `role: 'admin'` or `role: 'super_admin'`. Run full frontend test suites (`make test-web`) and production build verification (`make build-web`) to ensure 100% build health and zero regressions.

#### Technical Instructions
1. **Routing Setup** (`apps/web/src/app/app.routes.ts`):
   - Add route definition:
     ```typescript
     {
       path: 'admin',
       canActivate: [authGuard, adminGuard],
       loadComponent: () => import('./features/admin/admin-layout/admin-layout.component').then(m => m.AdminLayoutComponent),
       children: [
         {
           path: '',
           pathMatch: 'full',
           redirectTo: 'users'
         },
         {
           path: 'users',
           loadComponent: () => import('./features/admin/user-list/user-list.component').then(m => m.UserListComponent)
         },
         {
           path: 'users/:id',
           loadComponent: () => import('./features/admin/user-detail/user-detail.component').then(m => m.UserDetailComponent)
         }
       ]
     }
     ```
2. **Top Navigation Pill** (`apps/web/src/app/features/chat/chat-layout/chat-layout.component.html|ts`):
   - In `ChatLayoutComponent`, add computed signal or helper `isAdminOrSuperAdmin = computed(() => { const r = this.currentUser()?.role; return r === 'admin' || r === 'super_admin'; })`.
   - In `chat-layout.component.html`, render `🛡️ Admin` navigation pill before the user profile chip:
     ```html
     @if (isAdminOrSuperAdmin()) {
       <a
         routerLink="/admin/users"
         class="admin-nav-pill px-2.5 py-1 rounded-full text-xs font-semibold bg-[#faf8f5] text-[#016a71] border border-[#b2dddf] hover:bg-[#eef7f7] transition-colors flex items-center gap-1.5 cursor-pointer shadow-2xs"
         title="Go to Admin Console"
       >
         <span>🛡️</span>
         <span>Admin</span>
       </a>
     }
     ```
3. **Unit Tests Update** (`apps/web/src/app/features/chat/chat-layout/chat-layout.component.spec.ts`):
   - Verify `🛡️ Admin` pill appears when user role is `admin` or `super_admin`.
   - Verify `🛡️ Admin` pill does NOT appear when user role is `user`.
4. **Full Verification**:
   - Run `make test-web` (verify all frontend tests pass).
   - Run `make test-api` (verify all backend tests still pass).
   - Run `make build-web` (verify 0 compilation errors).

#### Files Touched
- `apps/web/src/app/app.routes.ts` (Modified)
- `apps/web/src/app/features/chat/chat-layout/chat-layout.component.ts` (Modified)
- `apps/web/src/app/features/chat/chat-layout/chat-layout.component.html` (Modified)
- `apps/web/src/app/features/chat/chat-layout/chat-layout.component.spec.ts` (Modified)

#### Verification Strategy
Run tests and build:
```bash
make test-web
make build-web
```

#### Prepared Git Commit
```text
feat(web): configure admin routes and add admin navigation pill in header

- Register /admin lazy-loaded routes in app.routes.ts protected by authGuard and adminGuard
- Add 🛡️ Admin navigation button in chat-layout.component top bar visible only to admin and super_admin
- Update chat-layout unit tests verifying role-based visibility of admin button
- Verification passed: make test-web (all suites pass) and make build-web (0 errors)
```
