### Task 09: Bundle Local PDF.js Worker, Surface Chat/PDF Errors & Clean Up Timers

- [x] Completed

#### Full Description
**MEDIUM + LOW (Audit Findings #15, #16, #17, #22).**
1. `PdfViewerModalComponent` (`pdf-viewer-modal.component.ts:18`) loads executable worker code from `https://cdnjs.cloudflare.com/...` at runtime (breaks under strict CSP / offline networks), fails to `destroy()` a prior `pdfDoc` when `pdfBlob` updates, lacks `role="dialog"`/`aria-modal`, and captures `ArrowLeft`/`ArrowRight` globally even if focus is in an input.
2. Chat session load/create/delete and PDF preview/download swallow errors silently, `+ New Chat` has no in-flight double-click guard, and clicking `Download` inside the open PDF modal re-downloads the blob over HTTP instead of reusing `activePdfBlob()`.
3. `RegisterComponent`, `ProfileComponent`, and `ChatWindowComponent`'s copy button leave `setTimeout` handles uncleaned on destroy.

#### Technical Instructions
1. **Write failing tests first** in `pdf-viewer-modal.component.spec.ts`, `chat-window.component.spec.ts`, `chat-sidebar.component.spec.ts`, `register.component.spec.ts`, and `profile.component.spec.ts`:
   - `GlobalWorkerOptions.workerSrc` resolves to `/assets/pdf.worker.min.mjs` (never `cdnjs.cloudflare.com`).
   - Passing a second `pdfBlob` calls `destroy()` on the previous `pdfDoc` instance.
   - Triggering `downloadPdf(filename)` while `activePdfBlob()` matches `previewFilename()` does **not** issue a second `getPdfBlob` HTTP request.
   - Failed `openPdfViewer` / `downloadPdf` / `createSession` sets a visible error signal.
   - Destroying `RegisterComponent` or `ProfileComponent` before the redirect timer elapses cancels navigation/logout.
2. Update `apps/web/angular.json` (`projects.web.architect.build.options.assets`):
   - Add `{ "glob": "pdf.worker.min.mjs", "input": "node_modules/pdfjs-dist/build", "output": "/assets/" }`.
3. Update `PdfViewerModalComponent` (`pdf-viewer-modal.component.ts` & `.html`):
   - Set `pdfjsLib.GlobalWorkerOptions.workerSrc = '/assets/pdf.worker.min.mjs'`.
   - At the start of `loadPdfFromBlob`, cancel any active `renderTask` and `await this.pdfDoc?.destroy()` before loading the new document; guard async completion against a newer load sequence counter.
   - Add `role="dialog"` and `aria-modal="true"` on `.pdf-modal-card`, and ignore `ArrowLeft`/`ArrowRight` in `handleKeyboardEvent` if `event.target` is an `HTMLInputElement` / `HTMLTextAreaElement` / `isContentEditable`.
4. Update `ChatService`, `ChatSidebarComponent`, and `ChatWindowComponent`:
   - Add `isCreatingSession = signal(false)` on `ChatService` (guarding duplicate `+ New Chat` clicks) and surface `loadSessions` / `createSession` / `deleteSession` / `loadMessages` / PDF errors via `streamError` (or `sidebarError` banner).
   - In `ChatWindowComponent.downloadPdf(filename)`, reuse `this.activePdfBlob()` directly if `this.activePdfBlob() && this.previewFilename() === filename`.
5. Clean up `setTimeout` handles via `DestroyRef` in `RegisterComponent`, `ProfileComponent`, and `ChatWindowComponent` (copy button reset + blob URL revoke).

#### Files Touched
- `apps/web/angular.json` (Modified)
- `apps/web/src/app/features/chat/pdf-viewer-modal/pdf-viewer-modal.component.{ts,html,spec.ts}` (Modified)
- `apps/web/src/app/core/services/chat.service.ts` (Modified)
- `apps/web/src/app/features/chat/chat-sidebar/chat-sidebar.component.{ts,html,spec.ts}` (Modified)
- `apps/web/src/app/features/chat/chat-window/chat-window.component.{ts,spec.ts}` (Modified)
- `apps/web/src/app/features/auth/register/register.component.{ts,spec.ts}` (Modified)
- `apps/web/src/app/features/profile/profile.component.{ts,spec.ts}` (Modified)

#### Verification Strategy
- Command: `make test-web && make build-web`
- Verify `apps/web/dist/web/browser/assets/pdf.worker.min.mjs` is emitted by `make build-web` and `rg "cdnjs" apps/web/src` returns nothing.

#### Prepared Git Commit
```text
fix(web): self-host PDF.js worker, surface chat/PDF errors and clean up timers

- Bundle pdf.worker.min.mjs via angular.json assets instead of loading from
  cdnjs at runtime
- Destroy prior pdfDoc on blob replacement and add dialog ARIA attributes
- Guard + New Chat against duplicate clicks, surface session/PDF errors in UI,
  and reuse activePdfBlob when downloading from the preview modal
- Clear redirect and UI feedback timers on component destroy via DestroyRef
- Verification: make test-web && make build-web passed
```
