# Simple AI Agent — Web Client

A modern, high-performance streaming AI Agent frontend built with **Angular 22** (standalone components & signals) and styled using **Tailwind CSS v4** following the **Perplexity AI** research terminal design system.

---

## Key Features

- **Signals Reactive State**: Fine-grained reactive architecture for session tracking, active message feeds, live streaming tokens, and tool approvals without RxJS overhead.
- **Perplexity-Inspired Design System**: Built following [`DESIGN.md`](../../DESIGN.md):
  - Canvas: Aged paper warm background (`#faf8f5`)
  - Containers: Pure card white (`#ffffff`) with pebble hairline borders (`#d1d1cd`)
  - Typography: Narrow document-like scale with `Inter` / `pplxSans` fallback
  - Accents: Restrained Deep Teal (`#016a71`) for active and selected states
  - Controls: Full pill rounding (`rounded-full` / `9999px`) on interactive elements
- **Multi-Language Syntax Highlighting**: Integrated `highlight.js` with full grammar recognition and styling for:
  - **Python** (`python`, `py`)
  - **C#** (`c#`, `csharp`, `cs`)
  - **TypeScript / JavaScript** (`typescript`, `ts`, `javascript`, `js`)
  - **Java** (`java`)
  - **PHP** (`php`)
  - **Ruby** (`ruby`, `rb`)
  - **CSS** (`css`, `scss`, `less`)
  - 1-click clipboard copy button with feedback
- **Real-Time SSE Streaming**: Native `ReadableStreamDefaultReader` streaming client with token buffering and cancellation via `AbortController`.
- **Human-in-the-Loop Tool Approval**: Real-time rendering of tool call cards (`search_web`, `calculator`) with argument inspection and interactive **Approve & Run** / **Reject** buttons.

---

## Styling Architecture (Tailwind CSS v4)

- Configured using `@tailwindcss/postcss` and native [`src/styles.css`](src/styles.css).
- Global theme definitions (`@theme`) define palette tokens, radii, and shadows directly in CSS.
- Zero Sass deprecation warnings through pure CSS nesting and PostCSS processing.

---

## Development & Build Commands

### Start Development Server
```bash
pnpm start
# or
ng serve
```
Navigate to `http://localhost:4200/`. The reverse proxy configured in `proxy.conf.json` forwards `/api` requests to the FastAPI backend at `http://localhost:8000`.

### Build for Production
```bash
pnpm build
# or
ng build
```
Generates optimized static production bundles in `dist/web/browser`.

### Run Unit Tests
```bash
pnpm test -- --watch=false
# or
ng test --watch=false
```
Executes all 65 frontend tests across 12 suites using the Vitest test runner.
