### Task 02: ProfileComponent Change Password Card with Strength Meter & Tests

- [ ] Pending

#### Full Description
Add a "Security & Credentials" card to `ProfileComponent` in `apps/web/src/app/features/profile/` with a reactive form, confirmation equality validator, a 4-segment visual password strength meter, 2-second logout transition, and comprehensive component tests.

#### Technical Instructions
1. In `apps/web/src/app/features/profile/profile.component.ts`:
   - Add `passwordForm: FormGroup`:
     - `current_password`: `['', [Validators.required]]`
     - `new_password`: `['', [Validators.required, Validators.minLength(6)]]`
     - `confirm_password`: `['', [Validators.required]]`
     - Form-level validator checking `new_password === confirm_password`.
   - Signals:
     - `isChangingPassword = signal<boolean>(false)`
     - `passwordErrorMessage = signal<string | null>(null)`
     - `passwordSuccessMessage = signal<string | null>(null)`
   - Computed strength evaluation:
     - Method or computed signal calculating password score 0-4 based on length >= 8, uppercase, lowercase, numbers, and symbols.
     - Strength label ('Too short', 'Weak', 'Fair', 'Good', 'Strong').
   - Method `onChangePassword()`:
     - If form invalid, mark all as touched & return.
     - Calls `authService.changePassword({ current_password, new_password })`.
     - On success: sets `passwordSuccessMessage`, resets form, and schedules `setTimeout(() => this.authService.logout(), 2000)`.
     - On error: sets `passwordErrorMessage`.
2. In `apps/web/src/app/features/profile/profile.component.html`:
   - Append "Security & Credentials" card beneath Profile Details:
     - Current Password, New Password, Confirm Password inputs.
     - 4-bar minimalist progress bar beneath New Password with dynamic color and strength label.
     - Validation error hints (required, min 6 characters, passwords mismatch).
     - Inline success and error banners.
     - "Update Password" button with loading spinner.
3. In `apps/web/src/app/features/profile/profile.component.spec.ts`:
   - Add tests verifying password form validation, mismatch detection, strength meter score, submission, and logout call.

#### Files Touched
- `apps/web/src/app/features/profile/profile.component.ts` (Modified)
- `apps/web/src/app/features/profile/profile.component.html` (Modified)
- `apps/web/src/app/features/profile/profile.component.spec.ts` (Modified)

#### Verification Strategy
```bash
cd apps/web && npx ng test --no-watch
```

#### Prepared Git Commit
```text
feat(profile): add change password card with strength meter

- Add passwordForm with confirmation match validation to ProfileComponent
- Implement real-time 4-segment password strength meter widget
- Display confirmation alert and trigger 2-second logout transition
- Add unit tests for password strength, validation, and submission
- Verification command passed: ng test full suite
```
