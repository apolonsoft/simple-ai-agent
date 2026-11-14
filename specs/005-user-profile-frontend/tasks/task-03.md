### Task 03: Top Navbar Integration & Avatar Thumbnail Rendering

- [ ] Pending

#### Full Description
Update the top navigation bar in `apps/web/src/app/features/chat/chat-layout/chat-layout.component.html` so the user chip links directly to `/profile`, highlights on hover, and dynamically renders the user's uploaded avatar image thumbnail if available, falling back to the initial letter circle.

#### Technical Instructions
1. In `apps/web/src/app/features/chat/chat-layout/chat-layout.component.html`:
   - Update `.user-chip` to include `[routerLink]="['/profile']"`, `role="button"`, and cursor/hover styles (`hover:bg-[#e8e6e1] cursor-pointer transition-colors`).
   - Check `@if (user.avatar_url)` to display `<img [src]="user.avatar_url" alt="Avatar" class="w-5 h-5 rounded-full object-cover">`, otherwise render existing initial letter circle.
2. In `apps/web/src/app/features/chat/chat-layout/chat-layout.component.ts`:
   - Ensure `RouterLink` is imported in `imports` array.
3. Update `apps/web/src/app/features/chat/chat-layout/chat-layout.component.spec.ts` to ensure router and template bindings pass all test assertions.

#### Files Touched
- `apps/web/src/app/features/chat/chat-layout/chat-layout.component.html` (Modified)
- `apps/web/src/app/features/chat/chat-layout/chat-layout.component.ts` (Modified)
- `apps/web/src/app/features/chat/chat-layout/chat-layout.component.spec.ts` (Modified if needed)

#### Verification Strategy
```bash
cd apps/web && npx ng test --no-watch
```

#### Prepared Git Commit
```text
feat(navigation): integrate user profile link and avatar in chat header

- Link user chip in top navbar to /profile route
- Render dynamic avatar thumbnail with fallback initial badge
- Update ChatLayoutComponent imports with RouterLink
- Verification command passed: ng test full suite
```
