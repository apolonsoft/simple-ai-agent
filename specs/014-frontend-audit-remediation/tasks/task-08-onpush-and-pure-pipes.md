### Task 08: Enable `OnPush` Everywhere & Replace Template Method Calls with Pure Pipes

- [x] Completed

#### Full Description
**MEDIUM + LOW (Audit Findings #13, #14, #23).**
1. None of the components set `ChangeDetectionStrategy.OnPush`, leaving views in `CheckAlways` mode where `document:click`, `window:keydown`, and 120Hz canvas `pointermove` listeners re-check child subtrees unnecessarily.
2. `ChatWindowComponent` calls `getToolParams(tc.arguments)` and `extractPdfFilename(tc.result)` inside `@for` templates—re-running `JSON.parse` and allocating fresh `{ key, value }[]` arrays on every historical tool call during streaming.
3. `ProfileComponent` invokes the `passwordStrength` getter 9 times per render (`4` regexes × `9`), and 9 standalone components import the entire `CommonModule` when they use `@if`/`@for` control flow.

#### Technical Instructions
1. Create two pure standalone pipes under `apps/web/src/app/features/chat/pipes/`:
   - `ToolParamsPipe` (`name: 'toolParams'`, `pure: true`): transforms `Record<string, unknown> | undefined` into `{ key: string; value: string }[]`.
   - `PdfFilenamePipe` (`name: 'pdfFilename'`, `pure: true`): extracts the `.pdf` filename from tool call `result` (moving `extractPdfFilename` logic out of template method calls).
   - Add unit tests in `tool-params.pipe.spec.ts` and `pdf-filename.pipe.spec.ts`.
2. Update `ChatWindowComponent`:
   - Convert `promptText: string = ''` to `readonly promptText = signal<string>('')` (updating `[ngModel]="promptText()"` + `(ngModelChange)="promptText.set($event)"`) so `OnPush` reacts cleanly to quick-prompt chips and clears.
   - Replace `getToolParams(tc.arguments)` with `tc.arguments | toolParams` and `extractPdfFilename(tc.result)` with `tc.result | pdfFilename` in `chat-window.component.html`.
   - Guard `onDocumentClick` (`line 211`) so it returns immediately when `!this.isToolsMenuOpen()` without walking the DOM.
3. Update `ProfileComponent`:
   - Bind `@let strength = passwordStrength;` once in `profile.component.html` (`line 239`) instead of calling `passwordStrength` 9 times per template pass.
4. Add `changeDetection: ChangeDetectionStrategy.OnPush` to every `@Component` (`App`, `AdminLayoutComponent`, `BanUserModalComponent`, `UserListComponent`, `UserDetailComponent`, `LoginComponent`, `RegisterComponent`, `ForgotPasswordComponent`, `ResetPasswordComponent`, `ChatLayoutComponent`, `ChatSidebarComponent`, `ChatWindowComponent`, `PdfViewerModalComponent`, `ProfileComponent`).
5. Replace unused `CommonModule` imports across components with only the specific standalone symbols actually used in each template (`NgClass`, `DatePipe`, or remove entirely).

#### Files Touched
- `apps/web/src/app/features/chat/pipes/tool-params.pipe.ts` (+ `.spec.ts`) (Created)
- `apps/web/src/app/features/chat/pipes/pdf-filename.pipe.ts` (+ `.spec.ts`) (Created)
- `apps/web/src/app/app.ts` (Modified)
- `apps/web/src/app/features/admin/admin-layout/admin-layout.component.ts` (Modified)
- `apps/web/src/app/features/admin/ban-user-modal/ban-user-modal.component.ts` (Modified)
- `apps/web/src/app/features/admin/user-list/user-list.component.ts` (Modified)
- `apps/web/src/app/features/admin/user-detail/user-detail.component.ts` (Modified)
- `apps/web/src/app/features/auth/login/login.component.ts` (Modified)
- `apps/web/src/app/features/auth/register/register.component.ts` (Modified)
- `apps/web/src/app/features/auth/forgot-password/forgot-password.component.ts` (Modified)
- `apps/web/src/app/features/auth/reset-password/reset-password.component.ts` (Modified)
- `apps/web/src/app/features/chat/chat-layout/chat-layout.component.ts` (Modified)
- `apps/web/src/app/features/chat/chat-sidebar/chat-sidebar.component.ts` (Modified)
- `apps/web/src/app/features/chat/chat-window/chat-window.component.{ts,html,spec.ts}` (Modified)
- `apps/web/src/app/features/chat/pdf-viewer-modal/pdf-viewer-modal.component.ts` (Modified)
- `apps/web/src/app/features/profile/profile.component.{ts,html}` (Modified)

#### Verification Strategy
- Command: `make test-web && make build-web`
- Confirm `rg "CommonModule" apps/web/src/app` returns zero matches and every `@Component` includes `ChangeDetectionStrategy.OnPush`.

#### Prepared Git Commit
```text
perf(web): enable OnPush across all components and memoize template helpers

- Add ChangeDetectionStrategy.OnPush to all standalone components and
  convert ChatWindowComponent.promptText to a Signal
- Replace getToolParams and extractPdfFilename template method calls with
  pure standalone pipes (ToolParamsPipe, PdfFilenamePipe)
- Evaluate ProfileComponent.passwordStrength once per render with @let
- Replace broad CommonModule imports with explicit NgClass/DatePipe imports
- Verification: make test-web && make build-web passed
```
