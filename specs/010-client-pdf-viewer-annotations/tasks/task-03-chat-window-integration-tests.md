### Task 03: Integrate PdfViewerModalComponent into ChatWindow and Add Vitest Tests

- [ ] Pending

#### Full Description
Replace the native `<iframe>` PDF preview modal in `ChatWindowComponent` with the newly created `PdfViewerModalComponent`. Wire the blob stream from `ChatService` into the modal component, connect download and close events, and update the Vitest test suite to verify end-to-end integration.

#### Technical Instructions
1. In `apps/web/src/app/features/chat/chat-window/chat-window.component.ts`:
   - Import `PdfViewerModalComponent`.
   - Add state signal `activePdfBlob = signal<Blob | null>(null)`.
   - In `openPdfViewer(filename: string)`: fetch blob via `chatService.getPdfBlob(filename)`, set `activePdfBlob.set(blob)`, `previewFilename.set(filename)`.
   - In `closePdfViewer()`: set `activePdfBlob.set(null)`, `previewFilename.set(null)`.
2. In `apps/web/src/app/features/chat/chat-window/chat-window.component.html`:
   - Remove `<div class="pdf-modal-backdrop">...<iframe [src]="previewPdfUrl()"></iframe>...</div>`.
   - Add:
     ```html
     @if (activePdfBlob()) {
       <app-pdf-viewer-modal
         [pdfBlob]="activePdfBlob()"
         [filename]="previewFilename() || 'document.pdf'"
         (closeModal)="closePdfViewer()"
         (download)="downloadPdf($event)"
       ></app-pdf-viewer-modal>
     }
     ```
3. In `apps/web/src/app/features/chat/chat-window/chat-window.component.spec.ts`:
   - Update tests to verify that `openPdfViewer` populates `activePdfBlob` and displays `<app-pdf-viewer-modal>`.
4. Run full test suite and build.

#### Files Touched
- `apps/web/src/app/features/chat/chat-window/chat-window.component.ts` (Modified)
- `apps/web/src/app/features/chat/chat-window/chat-window.component.html` (Modified)
- `apps/web/src/app/features/chat/chat-window/chat-window.component.spec.ts` (Modified)

#### Verification Strategy
```bash
PATH="$(pwd)/.bin:$PATH" pnpm --prefix apps/web test --watch=false && PATH="$(pwd)/.bin:$PATH" pnpm --prefix apps/web build
```

#### Prepared Git Commit
```text
feat(web): integrate canvas PdfViewerModalComponent into chat window

- Replace iframe modal with PdfViewerModalComponent in ChatWindow
- Connect authenticated PDF blob stream and download triggers
- Update Vitest test suite for modal integration
- Verification passed: pnpm test and pnpm build
```
