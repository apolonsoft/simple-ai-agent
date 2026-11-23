### Task 03: Fix Chat Stream Races, Session Switching, 401 Handling & Duplicate Loads

- [x] Completed

#### Full Description
**HIGH + MEDIUM + LOW (Audit Findings #2, #4, #6, #9, #12, #21).**
1. Switching sessions (`ChatService.selectSession`) neither aborts active streams nor cancels in-flight `loadMessages` requests, allowing Session A's stream tokens or slow HTTP responses to overwrite Session B's `messages`.
2. `sendMessageStream` and `approveToolCall` use raw `fetch()`, bypassing `authInterceptor` `401` logout handling; `approveToolCall` has no `AbortController`; both read `localStorage` directly without SSR guards.
3. Every streamed token synchronously clones `messages()`, triggering change detection 50+ times/sec instead of coalescing per animation frame.
4. `ChatSidebarComponent` binds both `[routerLink]` and `(click)="onSelect(session.id)"`, firing duplicate `GET /api/v1/chats/{id}/messages` calls on every click.
5. `ChatWindowComponent` tracks messages by `$index` (`@for (msg of messages(); track $index)`), causing DOM reuse across sessions.
6. Multi-line SSE `data:` lines overwrite instead of joining with `\n`.

Depends on Task 01 (`sse-parser.ts`).

#### Technical Instructions
1. **Write failing tests first** in `sse-parser.spec.ts`, `chat.service.spec.ts`, and `chat-sidebar.component.spec.ts`:
   - `parseSseBlock` joins multi-line `data: line1\ndata: line2` with `\n`.
   - Starting `sendMessageStream('session-1', ...)` and calling `selectSession('session-2')` aborts the `fetch` signal and ignores any trailing chunks from `'session-1'`.
   - `approveToolCall` passes an `AbortSignal` and aborts when `abortStream()` or `selectSession()` is called.
   - HTTP `401` from `/stream` or `/tool-calls/approval` invokes `authService.logout()`.
   - Clicking a session link in `ChatSidebarComponent` triggers navigation without a duplicate `selectSession` call from `(click)`.
2. Update `apps/web/src/app/core/utils/sse-parser.ts`:
   - Collect all `data:` lines into `dataLines: string[]` and join with `'\n'`.
3. Update `apps/web/src/app/core/models/chat.model.ts`:
   - Add optional `clientId?: string` on `ChatMessage`.
4. Update `apps/web/src/app/core/services/chat.service.ts`:
   - Inject `AuthService` and read tokens via `this.authService.getToken()`.
   - Track `private loadMessagesSub?: Subscription` and `private streamingSessionId: string | null = null`.
   - In `selectSession(sessionId)`:
     - If `sessionId === this.activeSessionId()` and either messages are already loaded or currently loading for that session, return early (idempotent).
     - Call `this.abortStream()` and `this.loadMessagesSub?.unsubscribe()`.
     - Subscribe to `this.loadMessages(sessionId)` storing `this.loadMessagesSub`, guarding `next` with `if (this.activeSessionId() === sessionId)`.
   - Assign `clientId: crypto.randomUUID()` (with fallback) to optimistic `userMsg` and `assistantMsg`, preserving `clientId` when `updateAssistantMessageId` sets the server `id`.
   - Pass `this.abortController.signal` into `approveToolCall`'s `fetch()`, and reset optimistic tool status back to `'pending'` on `AbortError` or HTTP failure.
   - On `response.status === 401` in both `sendMessageStream` and `approveToolCall`, call `this.authService.logout(); return;`.
   - Guard `processSseBlock`, `finalizeAssistantMessage`, and `handleStreamError` so chunks for a superseded `sessionId` are discarded.
   - Coalesce `appendAssistantToken` via a `pendingTokenBuffer` flushed on `requestAnimationFrame` (and flushed synchronously before `tool_call`, `done`, `error`, or `finalizeAssistantMessage` so event ordering stays exact).
5. Update `apps/web/src/app/features/chat/chat-sidebar/chat-sidebar.component.html` & `.ts`:
   - Remove `(click)="onSelect(session.id)"` from `.session-item` (`[routerLink]="['/chat', session.id]"` drives `ChatWindowComponent`'s `sessionId` route input cleanly).
6. Update `apps/web/src/app/features/chat/chat-window/chat-window.component.html` (`line 51`):
   - Change `@for (msg of messages(); track $index)` to `@for (msg of messages(); track msg.id ?? msg.clientId ?? $index)`.

#### Files Touched
- `apps/web/src/app/core/utils/sse-parser.ts` (Modified)
- `apps/web/src/app/core/utils/sse-parser.spec.ts` (Modified)
- `apps/web/src/app/core/models/chat.model.ts` (Modified)
- `apps/web/src/app/core/services/chat.service.ts` (Modified)
- `apps/web/src/app/core/services/chat.service.spec.ts` (Modified)
- `apps/web/src/app/features/chat/chat-sidebar/chat-sidebar.component.html` (Modified)
- `apps/web/src/app/features/chat/chat-sidebar/chat-sidebar.component.ts` (Modified)
- `apps/web/src/app/features/chat/chat-sidebar/chat-sidebar.component.spec.ts` (Modified)
- `apps/web/src/app/features/chat/chat-window/chat-window.component.html` (Modified)

#### Verification Strategy
- Command: `make test-web && make build-web`
- Verify stream cancellation, `401` logout redirect, multi-line SSE `data:`, and single `GET /messages` per click in Vitest.

#### Prepared Git Commit
```text
fix(web): isolate SSE streams per session, handle 401s and deduplicate loads

- Abort active chat/tool SSE streams and cancel in-flight loadMessages on
  session switch; ignore late chunks from superseded sessions
- Attach AbortController to approveToolCall and trigger AuthService.logout()
  on HTTP 401 from raw fetch streaming endpoints
- Coalesce streamed token updates per animation frame and flush before
  state transitions
- Concatenate multi-line SSE data: fields per WHATWG specification
- Remove duplicate (click) session load alongside [routerLink] and track
  messages by stable id/clientId instead of $index
- Verification: make test-web && make build-web passed
```
