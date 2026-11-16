# Master Task List: Frontend Admin User Management Interface

### Task 01: Core Admin Models, Admin Guard, and Admin Service
- [x] Completed
- **Description**: Define TypeScript data contracts matching backend admin schemas, implement `adminGuard` with role verification and fallback, and build `AdminService` with signals for user listings, pagination, filters, and actions.
- **Files**:
  - `apps/web/src/app/core/models/admin.model.ts`
  - `apps/web/src/app/core/guards/admin.guard.ts`
  - `apps/web/src/app/core/guards/admin.guard.spec.ts`
  - `apps/web/src/app/core/services/admin.service.ts`
  - `apps/web/src/app/core/services/admin.service.spec.ts`
- **Verification**: `pnpm --filter web test apps/web/src/app/core/guards/admin.guard.spec.ts apps/web/src/app/core/services/admin.service.spec.ts`

### Task 02: Admin Layout & User List Component with Ban Modal
- [x] Completed
- **Description**: Implement `AdminLayoutComponent` shell and `UserListComponent` with responsive data table, search input, role & status filter dropdowns, pagination controls, ban confirmation modal with custom reason, and super admin role dropdowns.
- **Files**:
  - `apps/web/src/app/features/admin/admin-layout/admin-layout.component.ts`
  - `apps/web/src/app/features/admin/admin-layout/admin-layout.component.html`
  - `apps/web/src/app/features/admin/user-list/user-list.component.ts`
  - `apps/web/src/app/features/admin/user-list/user-list.component.html`
  - `apps/web/src/app/features/admin/user-list/user-list.component.spec.ts`
- **Verification**: `pnpm --filter web test apps/web/src/app/features/admin/user-list/user-list.component.spec.ts`

### Task 03: User Detail Component & Metrics Page
- [ ] Pending
- **Description**: Build dedicated inspection page at `/admin/users/:id` with "Back to Users" navigation, user identity details, total chat sessions count metric card, ban status banner, and ban/unban/role action controls.
- **Files**:
  - `apps/web/src/app/features/admin/user-detail/user-detail.component.ts`
  - `apps/web/src/app/features/admin/user-detail/user-detail.component.html`
  - `apps/web/src/app/features/admin/user-detail/user-detail.component.spec.ts`
- **Verification**: `pnpm --filter web test apps/web/src/app/features/admin/user-detail/user-detail.component.spec.ts`

### Task 04: Navigation Integration, Routing Configuration, and Verification
- [ ] Pending
- **Description**: Configure lazy-loaded `/admin` child routes in `app.routes.ts`, add the role-protected `🛡️ Admin` pill in `chat-layout.component.html|ts`, and run comprehensive frontend test suite and production build verification.
- **Files**:
  - `apps/web/src/app/app.routes.ts`
  - `apps/web/src/app/features/chat/chat-layout/chat-layout.component.ts`
  - `apps/web/src/app/features/chat/chat-layout/chat-layout.component.html`
  - `apps/web/src/app/features/chat/chat-layout/chat-layout.component.spec.ts`
- **Verification**: `make test-web && make build-web`
