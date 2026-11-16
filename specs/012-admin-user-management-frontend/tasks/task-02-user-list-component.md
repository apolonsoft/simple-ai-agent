### Task 02: Admin Layout & User List Component with Ban Modal
- [x] Completed

#### Full Description
Construct the administrative layout shell and main user management directory table at `/admin/users`. The component includes search input with debounce, role filter dropdown (`All`, `user`, `admin`, `super_admin`), status filter dropdown (`All`, `Active`, `Banned`), responsive table with pagination controls, and action triggers. For banning, a clean modal prompts for a required custom ban reason before dispatching the ban request. Super administrators receive an interactive dropdown to alter user roles, while regular administrators view read-only badges.

#### Technical Instructions
1. **Admin Layout Component** (`apps/web/src/app/features/admin/admin-layout/admin-layout.component.ts|html`):
   - Standalone component containing the top admin header bar with "🛡️ Admin Console" title and "← Back to Chat" link (`/chat`).
   - Renders `<router-outlet></router-outlet>` in the main area.
2. **User List Component** (`apps/web/src/app/features/admin/user-list/user-list.component.ts|html`):
   - Standalone component injecting `AdminService` and `AuthService`.
   - Search bar with clear button and 300ms debounce.
   - Filter dropdowns:
     - Role: All Roles, User, Admin, Super Admin.
     - Status: All Statuses, Active, Banned.
   - Table columns:
     - User (Avatar circle with initials fallback, Full Name, Email).
     - Role (Interactive dropdown for `super_admin` except self; static badge for `admin`).
     - Status (Emerald `Active` badge or Rose `Banned` badge with tooltip for ban reason).
     - Joined Date (formatted e.g. `MMM d, yyyy`).
     - Actions:
       - "View Details" button linking to `/admin/users/:id`.
       - "Ban" button (opens modal) if not banned and target is not `super_admin` or self.
       - "Unban" button if banned.
   - Pagination footer with "Previous", "Next", current page, and total count.
   - Ban Confirmation Modal:
     - Shows target user's email and name.
     - Textarea for custom ban reason (minimum 3 characters).
     - "Cancel" and "Confirm Ban" action buttons.
3. **Unit Tests** (`apps/web/src/app/features/admin/user-list/user-list.component.spec.ts`):
   - Test table rendering with mocked users list.
   - Test search and filter changes trigger service reloads.
   - Test ban modal opening, inputting reason, and confirming.
   - Test unban button invokes service.
   - Test role dropdown permission check (`super_admin` vs `admin`).

#### Files Touched
- `apps/web/src/app/features/admin/admin-layout/admin-layout.component.ts` (Created)
- `apps/web/src/app/features/admin/admin-layout/admin-layout.component.html` (Created)
- `apps/web/src/app/features/admin/user-list/user-list.component.ts` (Created)
- `apps/web/src/app/features/admin/user-list/user-list.component.html` (Created)
- `apps/web/src/app/features/admin/user-list/user-list.component.spec.ts` (Created)

#### Verification Strategy
Run Vitest on `user-list.component.spec.ts`:
```bash
pnpm --filter web test apps/web/src/app/features/admin/user-list/user-list.component.spec.ts
```

#### Prepared Git Commit
```text
feat(web): implement admin layout and user list component with ban modal

- Create AdminLayoutComponent with navigation header and back-to-chat link
- Implement UserListComponent with responsive data table, search, role/status filters, and pagination
- Add BanConfirmationModal prompting for custom ban reason
- Support interactive role dropdown for super_admin with guardrails against self-demotion
- Add unit tests for UserListComponent verifying table rendering, filtering, and ban actions
- Verification: Vitest component tests pass
```
