### Task 03: Frontend Angular Integration with Native PDF Viewer and Download

- [ ] Pending

#### Full Description
Integrate PDF MCP server tool calling into the Angular chat frontend. Display dedicated `📄` PDF icons for `create_pdf`, `merge_pdfs`, and `inspect_pdf` in tool cards. When a PDF document has been created or merged, provide an interactive **View PDF** button (opening a clean modal dialog with a native browser PDF iframe) and a **Download** button. Add a quick prompt chip `📄 Generate PDF Report` in the empty conversation state.

#### Technical Instructions
1. In `apps/web/src/app/core/services/chat.service.ts`:
   - Add `getPdfBlob(filename: string): Observable<Blob>` calling `this.http.get('/api/v1/chats/files/pdf/' + filename, { responseType: 'blob' })`.
2. In `apps/web/src/app/features/chat/chat-window/chat-window.component.ts`:
   - Import `DomSanitizer`, `SafeResourceUrl`.
   - Add signals `previewPdfUrl = signal<SafeResourceUrl | null>(null)` and `previewFilename = signal<string | null>(null)`.
   - Helper methods:
     - `isPdfTool(toolName: string): boolean` (`['create_pdf', 'merge_pdfs', 'inspect_pdf'].includes(toolName)`).
     - `extractPdfFilename(result: any): string | null` (parses JSON string if needed, looks for `filename` ending in `.pdf`).
     - `openPdfViewer(filename: string)`: calls `chatService.getPdfBlob(filename)`, creates object URL, sanitizes URL, and updates signals.
     - `closePdfViewer()`: clears signals and revokes created object URL to prevent memory leaks.
     - `downloadPdf(filename: string)`: fetches blob via `chatService.getPdfBlob(filename)`, creates anchor element, sets download attribute, and clicks it.
3. In `apps/web/src/app/features/chat/chat-window/chat-window.component.html`:
   - Set icon to `📄` if `isPdfTool(tc.tool)`.
   - If `tc.status === 'executed'` and `extractPdfFilename(tc.result)` is present:
     - Render **View PDF** button and **Download** button styled with Perplexity design tokens.
   - Add modal overlay when `previewPdfUrl()` is present:
     - Clean card with header (filename, close button) and `<iframe [src]="previewPdfUrl()" class="w-full h-[80vh] border-0 rounded-b-2xl"></iframe>`.
   - In empty state, add quick-chip button: `📄 Generate PDF Report`.
4. In `apps/web/src/app/features/chat/chat-window/chat-window.component.spec.ts`:
   - Add unit tests verifying PDF tool icon rendering, View PDF action opening modal, and Download action triggering blob download.
5. Run Vitest suite.

#### Files Touched
- `apps/web/src/app/core/services/chat.service.ts` (Modified)
- `apps/web/src/app/features/chat/chat-window/chat-window.component.ts` (Modified)
- `apps/web/src/app/features/chat/chat-window/chat-window.component.html` (Modified)
- `apps/web/src/app/features/chat/chat-window/chat-window.component.spec.ts` (Modified)

#### Verification Strategy
```bash
PATH="$(pwd)/.bin:$PATH" pnpm --prefix apps/web test --watch=false
```

#### Prepared Git Commit
```text
feat(web): add PDF tool recognition, native preview modal, and download actions

- Add getPdfBlob to ChatService
- Add PDF tool card badge and icon recognition (📄)
- Add 1-click View PDF modal using native browser PDF iframe
- Add 1-click Download button and empty state PDF quick prompt chip
- Add comprehensive Vitest unit tests
- Verification passed: pnpm test in apps/web
```
