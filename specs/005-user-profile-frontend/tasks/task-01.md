### Task 01: User Profile Models & UserService Implementation

- [x] Completed

#### Full Description
Extend the TypeScript `User` model with profile properties (`full_name`, `avatar_url`, `bio`, timestamps), declare `UserProfileUpdate`, and implement `UserService` with HTTP methods to communicate with `/api/v1/users/me` backend endpoints while keeping `AuthService.currentUser` reactive signal synchronized.

#### Technical Instructions
1. In `apps/web/src/app/core/models/user.model.ts`:
   - Add `full_name?: string | null;`, `avatar_url?: string | null;`, `bio?: string | null;`, `created_at?: string | null;`, and `updated_at?: string | null;` to `User`.
   - Export `UserProfileUpdate` interface with `full_name?: string | null;` and `bio?: string | null;`.
2. Create `apps/web/src/app/core/services/user.service.ts`:
   - Inject `HttpClient` and `AuthService`.
   - Implement `getProfile(): Observable<User>` calling `GET /api/v1/users/me` and tap to update `authService.currentUser`.
   - Implement `updateProfile(data: UserProfileUpdate): Observable<User>` calling `PATCH /api/v1/users/me` and tap to update `authService.currentUser`.
   - Implement `uploadAvatar(file: File): Observable<User>`:
     - Check file size (<= 5MB: 5 * 1024 * 1024 bytes) and allowed types (`image/jpeg`, `image/png`, `image/webp`), throwing an error observable if invalid.
     - Append to `FormData` (`formData.append('file', file)`) and call `POST /api/v1/users/me/avatar`.
     - Tap to update `authService.currentUser`.
3. Create `apps/web/src/app/core/services/user.service.spec.ts`:
   - Test `getProfile`, `updateProfile`, `uploadAvatar`, validation guard on file size/type, and signal synchronization.

#### Files Touched
- `apps/web/src/app/core/models/user.model.ts` (Modified)
- `apps/web/src/app/core/services/user.service.ts` (Created)
- `apps/web/src/app/core/services/user.service.spec.ts` (Created)

#### Verification Strategy
```bash
cd apps/web && npx ng test --no-watch
```

#### Prepared Git Commit
```text
feat(users): add user profile models and user service

- Extend User model with full_name, avatar_url, bio, and timestamps
- Add UserProfileUpdate interface
- Implement UserService with getProfile, updateProfile, and uploadAvatar
- Synchronize currentUser signal in AuthService on profile/avatar changes
- Add comprehensive unit tests in user.service.spec.ts
- Verification command passed: ng test unit tests
```
