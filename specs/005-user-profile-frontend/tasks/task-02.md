### Task 02: ProfileComponent & Routing

- [ ] Pending

#### Full Description
Create standalone `ProfileComponent` under `apps/web/src/app/features/profile/` with reactive form editing, avatar file upload trigger, error/success banners, and register the `/profile` route guarded by `authGuard`.

#### Technical Instructions
1. Create `apps/web/src/app/features/profile/profile.component.ts`:
   - Standalone component importing `CommonModule`, `ReactiveFormsModule`, `RouterLink`.
   - Injects `UserService`, `AuthService`, `FormBuilder`.
   - Signals: `isLoading`, `isSaving`, `isUploadingAvatar`, `errorMessage`, `successMessage`.
   - Form group: `full_name` (validators: maxLength(100)), `bio` (validators: maxLength(500)).
   - Methods: `loadProfile()`, `onSubmit()`, `onFileSelected(event)`, `dismissAlerts()`.
2. Create `apps/web/src/app/features/profile/profile.component.html`:
   - Styled with Tailwind matching the project's minimalist aesthetic.
   - Header with "← Back to Chat" link to `/chat` and title "Account Profile".
   - Avatar card with current image or initial circle fallback, "Change Photo" button, hidden file input, and loading spinner when uploading.
   - Form card with read-only email, role badge, full name input, and bio textarea.
   - "Save Changes" button with loading state.
   - Dismissible success and error alert banners.
3. Create `apps/web/src/app/features/profile/profile.component.scss` (empty or minimal custom rules).
4. In `apps/web/src/app/app.routes.ts`:
   - Add `{ path: 'profile', canActivate: [authGuard], loadComponent: () => import('./features/profile/profile.component').then((m) => m.ProfileComponent) }`.
5. Create `apps/web/src/app/features/profile/profile.component.spec.ts`:
   - Test loading and rendering user profile data.
   - Test form submission and save success.
   - Test avatar upload trigger.

#### Files Touched
- `apps/web/src/app/features/profile/profile.component.ts` (Created)
- `apps/web/src/app/features/profile/profile.component.html` (Created)
- `apps/web/src/app/features/profile/profile.component.scss` (Created)
- `apps/web/src/app/features/profile/profile.component.spec.ts` (Created)
- `apps/web/src/app/app.routes.ts` (Modified)

#### Verification Strategy
```bash
cd apps/web && npx ng test --no-watch
```

#### Prepared Git Commit
```text
feat(profile): create profile component and register /profile route

- Implement ProfileComponent with reactive form for full_name and bio
- Add file picker upload handler for avatars with client-side validation
- Add responsive minimalist UI with back-to-chat navigation
- Register /profile route with authGuard in app.routes.ts
- Add unit tests in profile.component.spec.ts
- Verification command passed: ng test component tests
```
