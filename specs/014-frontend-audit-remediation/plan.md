# Technical Architecture Plan: Frontend Audit Remediation

## 1. Architecture Overview
The remediation preserves the Angular 22 standalone, zoneless, Signal-first architecture in `apps/web` while hardening four core boundaries:

1. **SSE & Fetch Transport Extraction (Preparatory Refactor → Hardening):**
   - `ChatService` (`480` lines) currently mixes session CRUD, fetch/SSE line framing, optimistic message state, and tool-call patching.
   - Task 01 extracts a pure, stateless SSE frame parser (`app/core/utils/sse-parser.ts`) and shared admin RBAC helpers (`app/core/utils/admin-permissions.ts`) with zero behavior change, giving clean seams for Tasks 03–06.
2. **Sanitizer-Safe Markdown & Tree-Shaken Syntax Highlighting:**
   - `MarkdownPipe` drops `DomSanitizer.bypassSecurityTrustHtml`, returning plain `string` so Angular's native `[innerHTML]` sanitizer enforces an allowlist on every render.
   - `highlight.js` switches from the monolithic default import + `highlightAuto` (190 grammars) to `highlight.js/lib/core` with explicit language registration (`python`, `typescript`, `javascript`, `csharp`, `java`, `php`, `ruby`, `css`, `json`, `bash`, `sql`, `yaml`, `xml`, `markdown`, `go`, `rust`).
3. **Session Lifecycle, Cancellation & Store Reset:**
   - `AuthService` validates JWT `exp` in `getToken()`, deduplicates `/auth/me` via `shareReplay`, and exposes a single `logout()` path used by both UI sign-out and `authInterceptor` `401` responses (via lazy `Injector` lookup or direct `AuthService` token management without circular `HttpClient` DI).
   - `ChatService` tracks stream `sessionId`, attaches `AbortController` to both `/stream` and `/tool-calls/approval`, coalesces streamed token chunks per animation frame, and cancels superseded `loadMessages` calls.
4. **Reactive Cancellation, Granular Loading & `OnPush` Rendering:**
   - `UserListComponent` drives search/filter/page requests through an RxJS pipeline (`debounceTime` + `switchMap` + `takeUntilDestroyed`).
   - `AdminService` splits `isLoading` into `isLoadingList`, `isLoadingDetail`, and `mutatingUserId`.
   - Every component enables `ChangeDetectionStrategy.OnPush`, replaces template method allocations with pure pipes / `computed` / `@let`, and cleans up timers/workers via `DestroyRef`.

---

## 2. Affected Files

### New Files
- `apps/web/src/app/core/utils/sse-parser.ts` (+ `.spec.ts`) — Pure SSE block/chunk splitter & multi-line `data:` parser (Task 01, updated Task 03).
- `apps/web/src/app/core/utils/admin-permissions.ts` (+ `.spec.ts`) — Pure `canModerateUser` & `canChangeUserRole` helpers (Task 01, updated Task 06).
- `apps/web/src/app/features/admin/ban-user-modal/ban-user-modal.component.ts` (+ `.html`, `.spec.ts`) — Shared ban confirmation modal extracted from `user-list` & `user-detail` (Task 06).
- `apps/web/src/app/features/chat/pipes/tool-params.pipe.ts` & `pdf-filename.pipe.ts` (+ `.spec.ts`) — Pure pipes replacing per-check template method calls in `ChatWindowComponent` (Task 08).

### Modified Core & Shared Files
- `apps/web/angular.json` — Copy `pdf.worker.min.mjs` from `node_modules/pdfjs-dist/build/` to `/assets/` (Task 09).
- `apps/web/tsconfig.json` — Enable `"strict": true` and `"strictTemplates": true` (Task 10).
- `apps/web/src/app/shared/pipes/markdown.pipe.ts` (+ `.spec.ts`) — Remove `bypassSecurityTrustHtml` & `highlightAuto`; core `hljs` imports; `<span>` copy button (Task 02).
- `apps/web/src/app/core/services/auth.service.ts` (+ `.spec.ts`) — JWT `exp` validation, deduplicated `ensureCurrentUser()`, registered reset hooks on logout (Task 04).
- `apps/web/src/app/core/interceptors/auth.interceptor.ts` (+ `.spec.ts`) — Unified `401` logout clearing `currentUser` and feature stores (Task 04).
- `apps/web/src/app/core/guards/auth.guard.ts` & `admin.guard.ts` (+ `.spec.ts`) — Expired-token rejection & shared `/auth/me` bootstrap (Task 04).
- `apps/web/src/app/core/services/chat.service.ts` (+ `.spec.ts`) — Session-scoped streams, `AbortController` on tool approvals, `401` handling, rAF token coalescing, `switchMap` on `selectSession`, `clientId` message keys, error signals, `resetState()` (Tasks 01, 03, 04, 09).
- `apps/web/src/app/core/services/admin.service.ts` (+ `.spec.ts`) — `isLoadingList` / `isLoadingDetail` / `mutatingUserId`, clear stale `selectedUser`, `resetState()` (Tasks 04, 05, 06).
- `apps/web/src/app/core/models/*.ts` & `shared/types/api.ts` — Synchronized strict types (Task 10).

### Modified Feature Components
- `apps/web/src/app/features/chat/chat-window/chat-window.component.{ts,html,scss,spec.ts}` — `OnPush`, `promptText` signal, `track msg.id ?? msg.clientId`, pure pipes, smart rAF scroll without `MutationObserver`, keyboard copy support, PDF error/reuse handling (Tasks 02, 03, 07, 08, 09).
- `apps/web/src/app/features/chat/chat-sidebar/chat-sidebar.component.{ts,html,spec.ts}` — Remove duplicate `(click)="onSelect(...)"`, guard double-clicks, surface errors, `OnPush` (Tasks 03, 08, 09).
- `apps/web/src/app/features/chat/pdf-viewer-modal/pdf-viewer-modal.component.{ts,html,spec.ts}` — Local worker URL, `pdfDoc.destroy()` before reload, dialog ARIA, input-safe keydown, `OnPush` (Tasks 08, 09).
- `apps/web/src/app/features/admin/user-list/user-list.component.{ts,html,spec.ts}` — Debounced `switchMap` search/filter stream, granular loading, unban RBAC guard, `<app-ban-user-modal>`, `OnPush` (Tasks 01, 05, 06, 08).
- `apps/web/src/app/features/admin/user-detail/user-detail.component.{ts,html,spec.ts}` — Reactive `id = input<string>()` route binding, granular loading, unban RBAC guard, `<app-ban-user-modal>`, `OnPush` (Tasks 01, 06, 08).
- `apps/web/src/app/features/auth/{login,register,forgot-password,reset-password}/*` & `features/profile/*` — `DestroyRef` timer cleanup, `@let` / `computed` password strength, 6-char reset validator, `confirm_password` touched check, `OnPush`, trimmed imports (Tasks 08, 09, 10).
- `apps/web/src/app/app.ts` & `features/admin/admin-layout/*` — `OnPush`, trimmed imports (Task 08).

### Dependencies
Zero new npm packages required. All fixes use APIs already installed in `@angular/*` 22.2, `rxjs` 7.8, `highlight.js` 11.12, and `pdfjs-dist` 4.10.

---

## 3. Testing Strategy
All tests run via Vitest (`make test-web` / `cd apps/web && pnpm test --watch=false`) plus production bundle verification (`make build-web`). Each task writes failing unit specs first:

| Task | Target Specs | Key Assertions |
|---|---|---|
| `task-01` | `sse-parser.spec.ts`, `admin-permissions.spec.ts`, existing suite | Zero regressions after extracting pure helpers |
| `task-02` | `markdown.pipe.spec.ts`, `chat-window.component.spec.ts` | `transform()` returns plain string (not `SafeHtml` bypass); `<img onerror=...>` / `<script>` / malicious markdown combinations cannot survive `[innerHTML]`; unlabeled code skips `highlightAuto`; copy `<span>` copies code |
| `task-03` | `chat.service.spec.ts`, `chat-sidebar.component.spec.ts` | Switching session mid-stream aborts stream & ignores late chunks; `approveToolCall` aborts on cancel; `401` on stream calls `authService.logout()`; multi-line `data:` joins with `\n`; sidebar click fires 1 `GET /messages` |
| `task-04` | `auth.service.spec.ts`, `auth.guard.spec.ts`, `admin.guard.spec.ts`, `auth.interceptor.spec.ts` | Expired JWT rejected by `getToken()`/`authGuard`; concurrent bootstrap + `adminGuard` issue 1 `GET /auth/me`; `logout()` and `401` interceptor wipe `currentUser`, `ChatService`, and `AdminService` |
| `task-05` | `user-list.component.spec.ts`, `admin.service.spec.ts` | Typing 5 chars within 250ms issues 1 HTTP call; slow earlier search cancelled by `switchMap`; role/ban PATCH does not set `isLoadingList` true |
| `task-06` | `user-detail.component.spec.ts`, `user-list.component.spec.ts`, `ban-user-modal.component.spec.ts` | Route input change `/users/A` → `/users/B` reloads user & clears stale detail; regular `admin` cannot see `Unban` on banned `admin`/`super_admin` |
| `task-07` | `chat-window.component.spec.ts` | No `MutationObserver` created; upward user scroll is preserved during incoming chunks; sending a new message scrolls to bottom |
| `task-08` | `tool-params.pipe.spec.ts`, `pdf-filename.pipe.spec.ts`, `profile.component.spec.ts`, full suite | All components run under `ChangeDetectionStrategy.OnPush`; pipes memoize outputs |
| `task-09` | `pdf-viewer-modal.component.spec.ts`, `chat-window.component.spec.ts`, `register.component.spec.ts`, `profile.component.spec.ts` | Worker URL points to `/assets/pdf.worker.min.mjs`; previous `pdfDoc.destroy()` called on blob swap; modal download reuses `activePdfBlob`; timers cancelled on destroy |
| `task-10` | Full `make test-web` + `make build-web` | `"strict": true` & `"strictTemplates": true` compile cleanly; `reset-password` enforces 6 chars; `shared/types/api.ts` matches frontend models |

---

## 4. Non-Goals
See `spec.md` §4.
