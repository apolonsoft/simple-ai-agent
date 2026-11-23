### Task 07: Replace Scroll `MutationObserver` & Timer Cascade with Smart rAF Auto-Scroll

- [x] Completed

#### Full Description
**HIGH (Audit Finding #8).**
`ChatWindowComponent` (`chat-window.component.ts:56–84, 243–260`) combines a `MutationObserver` (`childList`, `subtree`, `characterData`) with `scheduleScrollToBottom()` firing **four** scroll writes (`sync`, `rAF`, `setTimeout 20ms`, `setTimeout 80ms`) on every signal update, forcing synchronous layout reflows (`scrollHeight` → `scrollTop` + `scrollIntoView`) hundreds of times per second during SSE streaming and yanking the viewport to the bottom even when the user intentionally scrolled up to read earlier messages.

#### Technical Instructions
1. **Write failing tests first** in `apps/web/src/app/features/chat/chat-window/chat-window.component.spec.ts`:
   - When the user scrolls up (`scrollHeight - scrollTop - clientHeight > 100`), incoming assistant tokens do **not** overwrite `scrollTop`.
   - When the user is at/near the bottom (or submits a new prompt / switches sessions), `scrollTop` advances to `scrollHeight`.
   - Destroying the component cancels any pending `requestAnimationFrame` callback cleanly.
2. Update `apps/web/src/app/features/chat/chat-window/chat-window.component.ts` & `.html`:
   - Remove `observer?: MutationObserver`, `setupScrollObserver()`, and the `20ms`/`80ms` `setTimeout` calls.
   - Track `private stickToBottom = true` updated via `(scroll)="onViewportScroll()"` on `.messages-viewport`:
     ```ts
     onViewportScroll(): void {
       const el = this.messagesContainer?.nativeElement;
       if (!el) return;
       const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
       this.stickToBottom = distanceFromBottom <= 80;
     }
     ```
   - Reset `this.stickToBottom = true` whenever `sessionId()` changes or `sendMessage()` is called.
   - Implement `scheduleScrollToBottom(force = false)` using a single coalesced `requestAnimationFrame` ID (`private scrollRafId: number | null = null`, cancelled in `ngOnDestroy`), writing `el.scrollTop = el.scrollHeight` once per frame only when `force || this.stickToBottom`.

#### Files Touched
- `apps/web/src/app/features/chat/chat-window/chat-window.component.ts` (Modified)
- `apps/web/src/app/features/chat/chat-window/chat-window.component.html` (Modified)
- `apps/web/src/app/features/chat/chat-window/chat-window.component.spec.ts` (Modified)

#### Verification Strategy
- Command: `make test-web && make build-web`

#### Prepared Git Commit
```text
perf(web): replace MutationObserver scroll thrashing with smart rAF auto-scroll

- Remove subtree MutationObserver and 20ms/80ms setTimeout scroll cascade
  in ChatWindowComponent
- Coalesce scroll updates into a single requestAnimationFrame cleaned up
  on destroy
- Respect user upward scrolling during streaming and only auto-scroll when
  near the bottom or starting a new turn/session
- Add scroll stickiness and cleanup unit tests
- Verification: make test-web && make build-web passed
```
