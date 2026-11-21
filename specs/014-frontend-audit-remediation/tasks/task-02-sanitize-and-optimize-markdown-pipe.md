### Task 02: Remove `bypassSecurityTrustHtml` & Optimize `MarkdownPipe` Highlighting

- [ ] Pending

#### Full Description
**CRITICAL + HIGH (Audit Findings #1 & #6).**
1. `MarkdownPipe.transform` (`apps/web/src/app/shared/pipes/markdown.pipe.ts:16`) calls `this.sanitizer.bypassSecurityTrustHtml(html)`, completely disabling Angular's HTML sanitizer on LLM/search-tool output while the user's JWT lives in `localStorage`.
2. `MarkdownPipe.highlightCode` (`line 76`) falls back to `hljs.highlightAuto(rawCode)` across all ~190 bundled `highlight.js` grammars on every streamed token whenever a fenced code block lacks a language tag, stalling the main thread and inflating the JS bundle (`import hljs from 'highlight.js'`).

#### Technical Instructions
1. **Write failing tests first** in `apps/web/src/app/shared/pipes/markdown.pipe.spec.ts`:
   - Assert `typeof pipe.transform('**bold**') === 'string'` (plain string, not `SafeHtmlImpl` bypass).
   - Assert adversarial inputs (`<img src=x onerror=alert(1)>`, `[x](javascript:alert(1))`, nested formatting inside link URLs `[click](https://example.com/**onload=alert(1)**)`) produce output sanitized cleanly by `DomSanitizer.sanitize(SecurityContext.HTML, ...)`.
   - Assert unlabeled code blocks (` ```\nconst x = 1;\n``` `) render escaped code inside `<pre><code class="hljs">` **without** invoking `highlightAuto`.
2. Update `apps/web/src/app/shared/pipes/markdown.pipe.ts`:
   - Remove `DomSanitizer` / `SafeHtml` imports and `bypassSecurityTrustHtml`; return `string` directly from `transform(value: string | null | undefined): string` so Angular's `[innerHTML]` applies built-in `SecurityContext.HTML` sanitization automatically.
   - Replace `import hljs from 'highlight.js'` with `import hljs from 'highlight.js/lib/core'` and register explicit grammars (`python`, `typescript`, `javascript`, `csharp`, `java`, `php`, `ruby`, `css`, `json`, `bash`, `sql`, `yaml`, `xml`, `markdown`, `go`, `rust`).
   - Delete the `hljs.highlightAuto` fallback in `highlightCode`; when `language` is empty or unregistered, return `this.escapeHtml(rawCode)`.
   - Replace `<button type="button" class="copy-code-btn">...<svg>...</svg><span class="copy-text">Copy</span></button>` (`lines 95–101`) with sanitizer-safe markup (`<span>` elements survive Angular's HTML sanitizer; `<button>` and `<svg>` are stripped):
     ```html
     <span class="copy-code-btn"><span class="copy-text">Copy</span></span>
     ```
   - Perform link replacement (`[text](https://...)`) **before** inline bold/italic replacement, or escape quotes/tags in captured URLs so markdown emphasis tokens inside URLs (`https://en.wikipedia.org/wiki/Foo_bar`) are not mangled into `<em>`/`<strong>` tags inside `href`.
3. Update `apps/web/src/app/features/chat/chat-window/chat-window.component.scss` (if needed) so `.copy-code-btn` as a `<span>` retains identical cursor, hover, border, and layout styling, and update `chat-window.component.ts` (`onMessagesClick`, `line 220`) type cast from `HTMLButtonElement` to `HTMLElement`.

#### Files Touched
- `apps/web/src/app/shared/pipes/markdown.pipe.ts` (Modified)
- `apps/web/src/app/shared/pipes/markdown.pipe.spec.ts` (Modified)
- `apps/web/src/app/features/chat/chat-window/chat-window.component.ts` (Modified)
- `apps/web/src/app/features/chat/chat-window/chat-window.component.scss` (Modified)
- `apps/web/src/app/features/chat/chat-window/chat-window.component.spec.ts` (Modified)

#### Verification Strategy
- Command: `make test-web && make build-web`
- Confirm `rg "bypassSecurityTrust|highlightAuto" apps/web/src` returns zero matches and production bundle size decreases.

#### Prepared Git Commit
```text
fix(web): remove bypassSecurityTrustHtml and highlightAuto in MarkdownPipe

- Return plain string from MarkdownPipe so Angular [innerHTML] natively
  sanitizes all rendered assistant markdown
- Render code-block Copy control with sanitizer-safe <span> markup
- Import highlight.js/lib/core with explicit languages and remove O(N)
  highlightAuto fallback on unlabeled code blocks
- Prevent bold/italic regexes from mutating underscores/asterisks inside URLs
- Add XSS sanitization and unlabeled-code regression tests
- Verification: make test-web && make build-web passed
```
