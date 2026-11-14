# Technical Architecture & Implementation Plan: User Profile Frontend

## 1. Architecture Overview
- **Data & Service Layer**:
  - `user.model.ts`: Extended `User` interface and `UserProfileUpdate` interface.
  - `user.service.ts`: Communicates with `/api/v1/users/me` backend endpoints using Angular `HttpClient`. Mutates `AuthService.currentUser` signal to keep application state synchronized across components.
- **UI & Presentation Layer**:
  - `ProfileComponent`: Standalone Angular component implementing Reactive Forms with validation constraints (`full_name` <= 100, `bio` <= 500), file input handler, and responsive layout styled with Tailwind CSS.
  - `ChatLayoutComponent`: Updated header user chip with `[routerLink]="['/profile']"` and conditional avatar image thumbnail with initial fallback.
- **Routing**:
  - Protected route at `/profile` requiring `authGuard`.

## 2. Affected Files
- `apps/web/src/app/core/models/user.model.ts` (Modified)
- `apps/web/src/app/core/services/user.service.ts` (Created)
- `apps/web/src/app/core/services/user.service.spec.ts` (Created)
- `apps/web/src/app/features/profile/profile.component.ts` (Created)
- `apps/web/src/app/features/profile/profile.component.html` (Created)
- `apps/web/src/app/features/profile/profile.component.scss` (Created)
- `apps/web/src/app/features/profile/profile.component.spec.ts` (Created)
- `apps/web/src/app/app.routes.ts` (Modified)
- `apps/web/src/app/features/chat/chat-layout/chat-layout.component.html` (Modified)
