# Feature Specification: Frontend Audit Remediation

## 1. Overview
This specification defines the remediation plan for all 24 findings (1 critical, 7 high, 10 medium, 6 low) identified during the staff-level frontend audit of `apps/web` (Angular 22.2, standalone components, Signals, RxJS, Tailwind v4, PDF.js, highlight.js).

It eliminates the `bypassSecurityTrustHtml` XSS exposure, fixes stream/session/search race conditions, restores global `401` handling on raw `fetch()` SSE streams, prevents cross-account singleton state bleed on logout, removes main-thread bottlenecks (`hljs.highlightAuto`, layout-thrashing `MutationObserver` + 4-timer scroll cascade, missing `OnPush`), bundles the PDF.js worker locally, and tightens TypeScript strictness and shared contracts.

---

## 2. User Stories & Acceptance Criteria

### US-1: Sanitizer-Safe Markdown Rendering & Fast Code Highlighting (CRITICAL + HIGH)
- **As a** platform user reading streamed AI responses,
- **I want** markdown and code blocks to render without disabling Angular's HTML sanitizer or freezing the browser on unlabeled code blocks,
- **So that** prompt-injected outputs cannot execute JavaScript (XSS) and streaming stays smooth at 60fps.
- **Acceptance Criteria**:
  - `MarkdownPipe` never calls `DomSanitizer.bypassSecurityTrustHtml`; `transform()` returns plain `string` sanitized natively by Angular's `[innerHTML]` binding (or `sanitizer.sanitize(SecurityContext.HTML, ...)`).
  - Code-block headers render the Copy trigger using sanitizer-safe `<span class="copy-code-btn" role="button" tabindex="0">` markup (preserving click & keyboard copy behavior).
  - `hljs.highlightAuto` is removed; unlabeled/unknown code blocks render escaped plaintext cleanly.
  - `highlight.js` imports `'highlight.js/lib/core'` and registers only explicit supported languages, reducing bundle weight.

### US-2: Isolated, Cancellable SSE Streaming & Session Switching (HIGH + MEDIUM + LOW)
- **As a** user switching between conversations or signing out during generation,
- **I want** active streams and pending message fetches for the previous session to cancel cleanly and never bleed tokens into another session,
- **So that** conversation histories never corrupt each other and expired tokens redirect cleanly to `/login`.
- **Acceptance Criteria**:
  - Switching sessions aborts any active message or tool-approval stream (`AbortController`) and cancels any in-flight `loadMessages` HTTP request (`switchMap` / subscription teardown).
  - Stream callbacks verify `sessionId === activeSessionId()` before mutating `messages`.
  - Both `sendMessageStream` and `approveToolCall` pass an `AbortSignal`, read tokens via `AuthService.getToken()` (SSR/environment-safe), concatenate multi-line SSE `data:` frames per spec, coalesce token updates via `requestAnimationFrame`, and call `authService.logout()` immediately on HTTP `401`.
  - Clicking a sidebar session triggers **one** `GET /api/v1/chats/{id}/messages` request (router `:sessionId` param is the single source of truth; duplicate `(click)` call removed).
  - Optimistic messages receive a stable client key (`clientId`) so `@for` tracks `msg.id ?? msg.clientId` instead of `$index`.

### US-3: Clean Session Bootstrap & Multi-Account Logout Isolation (HIGH)
- **As a** user logging in, refreshing a protected route, or switching accounts in the same tab,
- **I want** authentication state to initialize once without duplicate `/auth/me` requests and wipe all singleton stores on logout or `401`,
- **So that** expired tokens don't mount broken views and User A's chats/admin data never flash for User B.
- **Acceptance Criteria**:
  - `AuthService.getToken()` validates JWT structure and `exp` timestamp, clearing expired/malformed tokens immediately.
  - Initial user bootstrap shares a single in-flight `/api/v1/auth/me` observable (`shareReplay`) across app startup and `adminGuard`.
  - `AuthService.logout()` resets `ChatService` (aborts streams, clears sessions/messages/errors) and `AdminService` (clears users/selectedUser/filters/errors).
  - `authInterceptor` delegates `401` handling to `AuthService.logout()` instead of only deleting `localStorage.token` while leaving `currentUser()` populated.

### US-4: Race-Free Admin Console & Granular Loading States (HIGH + MEDIUM)
- **As an** administrator searching, filtering, inspecting, and moderating users,
- **I want** rapid search typing to debounce and cancel stale requests, row actions not to blank the whole table, and moderation controls to match RBAC rules,
- **So that** table results always match the current input and single-row updates feel instant.
- **Acceptance Criteria**:
  - Search input is debounced (`250ms`) and flattened with `switchMap` so stale responses cannot overwrite newer queries; filter/page changes also cancel prior in-flight list requests.
  - `AdminService` separates list/detail loading (`isLoadingList`, `isLoadingDetail`) from row/user mutations (`mutatingUserId`), keeping the table and detail view mounted during ban/unban/role PATCHes.
  - `UserDetailComponent` binds route `id` reactively (`input<string>()`) so navigating `/admin/users/A` → `/admin/users/B` reloads cleanly and clears stale `selectedUser` first.
  - Regular `admin` users do not see active `Unban` buttons on banned `admin`/`super_admin` accounts; hierarchy helpers (`canModerateUser`, `canChangeUserRole`) and `<app-ban-user-modal>` are shared instead of duplicated.

### US-5: Smooth 60fps Rendering, Smart Auto-Scroll & Explicit `OnPush` (HIGH + MEDIUM)
- **As a** user reading long streaming conversations or annotating PDFs,
- **I want** auto-scroll to respect manual upward scrolling without layout thrashing and components to skip redundant change-detection passes,
- **So that** reading earlier messages mid-stream works naturally and UI interactions stay responsive.
- **Acceptance Criteria**:
  - `ChatWindowComponent` removes `MutationObserver` and the `20ms`/`80ms` `setTimeout` cascade, scrolling once per animation frame only when the user is already near the bottom (or just sent a message).
  - All components declare `ChangeDetectionStrategy.OnPush` (`promptText` converted to a Signal).
  - Template-bound computations (`getToolParams`, `extractPdfFilename`, `passwordStrength`) are memoized via pure pipes / `@let` / `computed()` instead of re-allocating on every check.

### US-6: Self-Hosted PDF Worker, Resilient Error Feedback & Clean Timers (MEDIUM)
- **As a** user creating chats, viewing/downloading PDFs, or updating credentials,
- **I want** visible feedback when operations fail, zero external CDN dependencies for PDF rendering, and cleanly disposed timers/workers,
- **So that** errors aren't swallowed silently and PDF viewing works under strict CSP or offline environments.
- **Acceptance Criteria**:
  - `pdf.worker.min.mjs` is copied into build assets via `angular.json` and loaded from `/assets/pdf.worker.min.mjs` (no `cdnjs.cloudflare.com` request).
  - `PdfViewerModalComponent` destroys any prior `pdfDoc` before loading a new blob, adds dialog ARIA attributes, and ignores arrow-key shortcuts when focus is in an editable element.
  - Chat session load/create/delete and PDF preview/download surface user-visible error messages, prevent double-click duplicate creates, and reuse `activePdfBlob()` when downloading from the open modal.
  - Redirect timers in `RegisterComponent`, `ProfileComponent`, and copy-code feedback clean up via `DestroyRef`.

### US-7: Strict TypeScript, Unified Form Validation & Shared Contracts (LOW)
- **Acceptance Criteria**:
  - `tsconfig.json` enables `"strict": true` and `"strictTemplates": true` with zero compiler errors.
  - `ResetPasswordComponent` enforces `Validators.minLength(6)` matching register/change-password (deferred 6→8 bump stays owned by Backend Spec `013` Task 02), and `ProfileComponent` only displays password-mismatch after `confirm_password` is touched/dirty.
  - Unused `CommonModule` imports are replaced with explicit standalone imports (`NgClass`, `DatePipe`) where needed.
  - `apps/web/src/app/core/models/*` and `shared/types/api.ts` are synchronized (`UserRole`, tool statuses, admin & profile models, no client `RegisterRequest.role`).

---

## 3. Clarifications & Resolved Decisions

| Question | Decision |
|---|---|
| How should `MarkdownPipe` keep the Copy button without `bypassSecurityTrustHtml`? | **Sanitizer-safe `<span>`**: Render `<span class="copy-code-btn" role="button" tabindex="0">Copy</span>` (styled via CSS) and let Angular's native HTML sanitizer clean `[innerHTML]`. |
| How should the PDF.js Web Worker be served? | **Local asset**: Copy `node_modules/pdfjs-dist/build/pdf.worker.min.mjs` via `angular.json` assets to `/assets/pdf.worker.min.mjs`. |
| How should password minimum length coordinate with Backend Spec `013`? | **Keep 6-char min in Spec `014`**: Unify `reset-password` from `4` → `6` now; Spec `013` Task 02 owns the coordinated `6` → `8` bump with the backend. |

---

## 4. Boundaries & Non-Goals
- **Non-Goal**: Backend API changes (all backend fixes live in `specs/013-backend-audit-remediation/`).
- **Non-Goal**: Migrating JWT storage from `localStorage` to `HttpOnly` cookies (requires coordinated backend cookie + CSRF endpoints).
- **Non-Goal**: Adding `@angular/cdk` virtual scrolling to the chat feed (deferred unless sessions regularly exceed 200+ turns).
- **Non-Goal**: Redesigning visual themes, layouts, or user workflows.
