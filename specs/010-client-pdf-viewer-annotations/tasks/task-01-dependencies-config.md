### Task 01: Install pdfjs-dist Dependency and Configure Worker

- [x] Completed

#### Full Description
Install `pdfjs-dist` into `apps/web` and configure worker script paths so that PDF documents can be parsed and rendered inside an HTML5 `<canvas>` in the Angular application.

#### Technical Instructions
1. In `apps/web`:
   - Run `pnpm add pdfjs-dist@^4.10.38` (or compatible latest version).
2. Configure worker source fallback:
   - Ensure the PDF.js GlobalWorkerOptions points to the bundled or CDN worker script URL to support fast background parsing without blocking the browser main thread.
3. Verify that `pdfjs-dist` imports without TypeScript or build errors in the frontend build pipeline.

#### Files Touched
- `apps/web/package.json` (Modified)
- `apps/web/pnpm-lock.yaml` (Modified)

#### Verification Strategy
```bash
PATH="$(pwd)/.bin:$PATH" pnpm --prefix apps/web build
```

#### Prepared Git Commit
```text
build(web): add pdfjs-dist dependency for client-side PDF rendering

- Install pdfjs-dist in apps/web
- Configure GlobalWorkerOptions worker script
- Verification passed: pnpm build in apps/web
```
