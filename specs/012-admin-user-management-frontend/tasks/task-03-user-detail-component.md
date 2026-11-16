### Task 03: User Detail Component & Metrics Page
- [x] Completed

#### Full Description
Construct the dedicated user inspection page at `/admin/users/:id`. The page provides detailed visibility into a specific user account: personal details (avatar, name, email, bio, email verification status), account activity metrics (total chat sessions count, created date, last updated date), and prominent ban information (if banned: timestamp and custom ban reason). The page includes operational controls to ban or unban the user and modify user roles (for `super_admin`), plus a "← Back to Users" button to return to the directory.

#### Technical Instructions
1. **User Detail Component** (`apps/web/src/app/features/admin/user-detail/user-detail.component.ts|html`):
   - Standalone component reading `id` parameter from `ActivatedRoute`.
   - Injects `AdminService` and `AuthService`.
   - Layout:
     - Header: "← Back to Users" breadcrumb/button, User Full Name / Email, Action buttons (Ban / Unban / Role Selector).
     - Ban Alert Banner (displayed if `is_banned` is true): Warning styling showing banned timestamp and reason.
     - Metric Cards grid:
       - Total Chat Sessions count card (`chat_sessions_count`).
       - Account Status card (`Active` / `Banned` + `Verified` / `Unverified`).
       - Joined Date card.
       - Role card.
     - Profile Details card:
       - Avatar, Full Name, Email, Bio (or "No bio provided").
       - Account UUID and Timestamps (Created at, Updated at).
   - Ban Modal integration (reused or embedded modal for ban action with custom reason).
2. **Unit Tests** (`apps/web/src/app/features/admin/user-detail/user-detail.component.spec.ts`):
   - Test loading user by route param and displaying profile details.
   - Test display of chat sessions count metric card.
   - Test ban alert banner visibility when `is_banned: true`.
   - Test ban and unban actions update the displayed user.
   - Test role modification behavior for `super_admin`.

#### Files Touched
- `apps/web/src/app/features/admin/user-detail/user-detail.component.ts` (Created)
- `apps/web/src/app/features/admin/user-detail/user-detail.component.html` (Created)
- `apps/web/src/app/features/admin/user-detail/user-detail.component.spec.ts` (Created)

#### Verification Strategy
Run Vitest on `user-detail.component.spec.ts`:
```bash
pnpm --filter web test apps/web/src/app/features/admin/user-detail/user-detail.component.spec.ts
```

#### Prepared Git Commit
```text
feat(web): build admin user detail component with activity metrics

- Implement UserDetailComponent at /admin/users/:id with usage metrics and metadata inspection
- Display total chat sessions count metric card and account status badges
- Render prominent ban banner displaying timestamp and ban reason when account is restricted
- Integrate ban modal, unban action, and super admin role selector
- Add unit tests validating profile presentation, metric cards, and administrative actions
- Verification: Vitest component tests pass
```
