# Feature Specification: User Profile Frontend

## 1. Overview & Context
This specification outlines the frontend implementation for user profile management in the Simple AI Agent Angular web application, enabling authenticated users to view their account details, edit their name and bio, upload an avatar image to SeaweedFS S3, and navigate smoothly between chat and profile views.

## 2. User Stories
- **View Profile**: As an authenticated user, I want to access my profile details (`email`, `role`, `full_name`, `bio`, `created_at`, `avatar_url`) so that I can see my current identity settings.
- **Edit Profile**: As an authenticated user, I want to edit my `full_name` and `bio` and save changes with immediate validation and feedback.
- **Upload Avatar**: As an authenticated user, I want to upload a profile picture (JPEG, PNG, WebP up to 5MB) that immediately updates my avatar in the profile view and top navigation bar.
- **Navigate to Profile**: As an authenticated user in `/chat`, I want to click on my user chip in the top navigation bar to go directly to `/profile`, and click "Back to Chat" to return.

## 3. Scope & Boundaries
- **In Scope**:
  - Updating `User` model and defining `UserProfileUpdate`.
  - Implementing `UserService` with `getProfile`, `updateProfile`, and `uploadAvatar` methods syncing with `AuthService.currentUser` signal.
  - Creating `ProfileComponent` (`/profile`) guarded by `authGuard`.
  - Updating the chat layout header to link the user chip to `/profile` and render avatar thumbnail if available.
  - Automated unit and component tests via Vitest / Angular CLI.
- **Out of Scope (Non-Goals)**:
  - Password change or two-factor authentication management.
  - Client-side image cropping canvas.
  - Public profile pages for anonymous visitors.

## 4. Acceptance Criteria
1. Clicking the user chip in the top navbar routes the user to `/profile`.
2. `/profile` displays user's email, role, full name, bio, and avatar.
3. Submitting the profile form updates `full_name` and `bio` via `PATCH /api/v1/users/me` and displays success feedback.
4. Selecting a valid image file uploads via `POST /api/v1/users/me/avatar` and updates both the profile avatar and the top navbar user avatar without page refresh.
5. Files over 5MB or invalid MIME types are rejected on the client before network transmission with a clear error message.
6. "Back to Chat" navigates back to `/chat`.
7. All automated unit and component tests pass with 0 errors.
