### Task 01: Extract Pure SSE Parser & Admin Permission Utilities

- [ ] Pending

#### Full Description
Preparatory refactoring step (per `.agent/rules/single-file-tasks.md` §2) with **zero functional change**.
`ChatService` (`480` lines) currently embeds raw SSE buffer splitting and `event:`/`data:` frame parsing inside `sendMessageStream`, `approveToolCall`, and `processSseBlock`. Similarly, `UserListComponent` and `UserDetailComponent` duplicate identical RBAC helper logic (`canBan`, `canChangeRole`). Extracting both into pure, standalone utility modules gives clean, unit-tested seams before Tasks 03 and 06 change runtime behavior.

#### Technical Instructions
1. Create `apps/web/src/app/core/utils/sse-parser.ts`:
   - Export `splitSseBuffer(buffer: string): { blocks: string[]; remainder: string }` preserving the exact regex `/(?:\r\n\r\n|\r\r|\n\n)/` used in `ChatService` (`lines 180–181`).
   - Export `parseSseBlock(block: string): { eventType: string; dataStr: string } | null` preserving current parsing behavior from `ChatService.processSseBlock` (`lines 307–321`).
2. Create `apps/web/src/app/core/utils/sse-parser.spec.ts` covering single chunks, split boundaries, CRLF/LF delimiters, and empty blocks.
3. Update `apps/web/src/app/core/services/chat.service.ts` to delegate buffer splitting and block header extraction to `splitSseBuffer` and `parseSseBlock` without altering any public signatures, state updates, or error handling.
4. Create `apps/web/src/app/core/utils/admin-permissions.ts`:
   - Export `canBanUser(actor: { id: string; role: string } | null | undefined, target: { id: string; role: string } | null | undefined): boolean`.
   - Export `canChangeUserRole(actor: { id: string; role: string } | null | undefined, target: { id: string; role: string } | null | undefined): boolean`.
5. Create `apps/web/src/app/core/utils/admin-permissions.spec.ts` testing `user`, `admin`, `super_admin`, and self-action cases.
6. Update `UserListComponent` (`canBan`, `canChangeRole`) and `UserDetailComponent` (`canBan`, `canChangeRole` computed signals) to call `canBanUser` and `canChangeUserRole` with zero behavioral change.

#### Files Touched
- `apps/web/src/app/core/utils/sse-parser.ts` (Created)
- `apps/web/src/app/core/utils/sse-parser.spec.ts` (Created)
- `apps/web/src/app/core/utils/admin-permissions.ts` (Created)
- `apps/web/src/app/core/utils/admin-permissions.spec.ts` (Created)
- `apps/web/src/app/core/services/chat.service.ts` (Modified)
- `apps/web/src/app/features/admin/user-list/user-list.component.ts` (Modified)
- `apps/web/src/app/features/admin/user-detail/user-detail.component.ts` (Modified)

#### Verification Strategy
- Command: `make test-web && make build-web`
- All existing and new unit specs pass with zero functional changes.

#### Prepared Git Commit
```text
refactor(web): extract pure SSE frame parser and admin permission helpers

- Add app/core/utils/sse-parser.ts (+ unit tests) for SSE chunk boundary
  splitting and event/data block extraction
- Add app/core/utils/admin-permissions.ts (+ unit tests) for shared admin
  role hierarchy checks
- Delegate SSE framing in ChatService and RBAC checks in UserListComponent
  and UserDetailComponent to the shared utilities with zero behavior change
- Verification: make test-web && make build-web passed
```
