### Task 02: Implement Standalone PdfViewerModalComponent with Zoom and Annotation Toolbar

- [x] Completed

#### Full Description
Implement a standalone Angular 22 component `PdfViewerModalComponent` under `apps/web/src/app/features/chat/pdf-viewer-modal/`. The component renders PDF pages on an HTML5 canvas using `pdfjs-dist` and provides a transparent drawing canvas overlay for freehand pen and highlighter annotations. It provides comprehensive toolbar controls: page navigation (Prev, Next, Page X of Y), zoom controls (Zoom In, Zoom Out, Fit Width, 100% Reset), drawing controls (Pan/Select, Pen with colors, Highlighter with colors, Clear Annotations), Download action, and Close button.

#### Technical Instructions
1. Create directory `apps/web/src/app/features/chat/pdf-viewer-modal/`.
2. Implement `pdf-viewer-modal.component.ts`:
   - Standalone component using signals.
   - Inputs: `pdfBlob = input<Blob | null>(null)`, `filename = input<string>('')`.
   - Outputs: `closeModal = output<void>()`, `download = output<string>()`.
   - State signals:
     - `currentPage = signal<number>(1)`, `totalPages = signal<number>(1)`
     - `zoomScale = signal<number>(1.0)`
     - `activeTool = signal<'pan' | 'pen' | 'highlighter'>('pan')`
     - `activeColor = signal<string>('#ef4444')`
     - `strokeWidth = signal<number>(3)`
     - `isLoading = signal<boolean>(true)`
   - PDF rendering logic:
     - Use `pdfjsLib.getDocument({ data: arrayBuffer })` to load document.
     - Render active page to base `<canvas>` with DPR scaling (`window.devicePixelRatio`).
   - Annotation layer logic:
     - Stack transparent `<canvas>` over base canvas.
     - Store strokes per page in memory (`Map<number, Stroke[]>`).
     - Handle pointer events (`pointerdown`, `pointermove`, `pointerup`) with proper coordinate scaling.
     - Support highlighter blending (`globalAlpha = 0.4` or `globalCompositeOperation = 'multiply'`).
   - Toolbar methods:
     - `zoomIn()` (+25%, max 3.0x), `zoomOut()` (-25%, min 0.5x), `fitWidth()`, `resetZoom()`.
     - `prevPage()`, `nextPage()`.
     - `selectTool(tool)`, `selectColor(color)`, `clearAnnotations()`.
3. Implement `pdf-viewer-modal.component.html`:
   - Modal backdrop and card with Perplexity design styling.
   - Comprehensive floating/fixed top toolbar.
   - Canvas wrapper and loading indicator.
4. Implement `pdf-viewer-modal.component.scss`:
   - Positioning, responsive scroll container, touch-action styles.
5. Create `pdf-viewer-modal.component.spec.ts` with unit tests for controls and state.

#### Files Touched
- `apps/web/src/app/features/chat/pdf-viewer-modal/pdf-viewer-modal.component.ts` (Created)
- `apps/web/src/app/features/chat/pdf-viewer-modal/pdf-viewer-modal.component.html` (Created)
- `apps/web/src/app/features/chat/pdf-viewer-modal/pdf-viewer-modal.component.scss` (Created)
- `apps/web/src/app/features/chat/pdf-viewer-modal/pdf-viewer-modal.component.spec.ts` (Created)

#### Verification Strategy
```bash
PATH="$(pwd)/.bin:$PATH" pnpm --prefix apps/web test src/app/features/chat/pdf-viewer-modal --watch=false
```

#### Prepared Git Commit
```text
feat(web): implement PdfViewerModalComponent with zoom and annotation toolbar

- Add standalone PdfViewerModalComponent with canvas rendering via pdfjs-dist
- Add interactive drawing and highlighter overlay with per-page persistence
- Add toolbar with page navigation, zoom controls, tool selector, and colors
- Add comprehensive Vitest unit tests
- Verification passed: pnpm test in apps/web
```
