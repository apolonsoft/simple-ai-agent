# Feature Specification: Client-Side PDF Canvas Viewer & Annotation Toolbar

## 1. Overview & Context
This feature upgrades the PDF viewing experience in the Angular web frontend by replacing the browser-native iframe with a dedicated client-side HTML5 canvas renderer powered by `pdfjs-dist`. It provides seamless inline PDF document display across desktop and mobile webviews (eliminating mobile download prompts), accompanied by an interactive toolbar for page navigation, zoom adjustments, and freehand drawing / highlighter annotations.

## 2. User Stories
- **US-1**: As a user on mobile or desktop, when I click "View PDF", I want the document to render inline on an HTML5 canvas without triggering a forced file download.
- **US-2**: As a user reading a multi-page PDF, I want page controls (Prev, Next, Page X of Y) to easily navigate across pages.
- **US-3**: As a user inspecting document details, I want zoom controls (Zoom In, Zoom Out, 100% Reset, Fit Width) to adjust the view smoothly.
- **US-4**: As a user reviewing or highlighting a report, I want interactive Pen and Highlighter drawing tools with color selection and clear actions that persist per page.
- **US-5**: As a user, I want 1-click Download and Close actions accessible directly from the viewer toolbar.

## 3. Answered Clarifications & Boundaries
- **Clarification 1 (Toolbar Scope)**: Full annotation suite: Page navigation, Zoom controls, Pen drawing, Highlighter, color swatches, and clear actions.
- **Clarification 2 (Engine)**: Official `pdfjs-dist` rendering directly to HTML5 canvas within a standalone Angular 22 component.
- **Clarification 3 (Device Support)**: Replaces the native iframe across all devices for consistent styling and guaranteed mobile webview compatibility.
- **Boundaries & Non-Goals**:
  - Raw binary PDF document editing or embedding vector annotations into the downloaded PDF file is out of scope.
  - Server-side rasterization is out of scope.

## 4. Acceptance Criteria
1. `pdfjs-dist` installed and configured in `apps/web`.
2. `PdfViewerModalComponent` renders the active PDF page onto an HTML5 `<canvas>` using `pdfjs-dist` with high-DPI scaling.
3. Page navigation controls accurately update current page and render the target page.
4. Zoom controls adjust magnification scale (0.5x to 3.0x) and update canvas dimensions and annotations proportionally.
5. Interactive drawing overlay captures touch/mouse pointer events for Pen and Highlighter strokes with color choices and stroke persistence across page switches.
6. `ChatWindowComponent` invokes `PdfViewerModalComponent` when "View PDF" is clicked.
7. All automated unit tests in `apps/web` pass with zero regressions.
