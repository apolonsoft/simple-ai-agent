# Master Task Roadmap: Frontend Audit Remediation

| Task ID | Name | Severity | Audit Findings | Status | Spec File |
|---|---|---|---|---|---|
| `task-01` | Extract Pure SSE Parser & Admin Permission Utilities | Refactor | Prep for #2, #4, #18, #21 | `Completed` | [`task-01-refactor-sse-and-admin-helpers.md`](./task-01-refactor-sse-and-admin-helpers.md) |
| `task-02` | Remove `bypassSecurityTrustHtml` & Optimize `MarkdownPipe` Highlighting | CRITICAL / HIGH | #1, #6 | `Completed` | [`task-02-sanitize-and-optimize-markdown-pipe.md`](./task-02-sanitize-and-optimize-markdown-pipe.md) |
| `task-03` | Fix Chat Stream Races, Session Switching, 401 Handling & Duplicate Loads | HIGH / MEDIUM | #2, #4, #6, #9, #12, #21 | `Pending` | [`task-03-harden-chat-streaming-and-sessions.md`](./task-03-harden-chat-streaming-and-sessions.md) |
| `task-04` | Harden Auth Bootstrap, Token Expiry & Multi-Store Logout Reset | HIGH | #5, #7 | `Pending` | [`task-04-auth-bootstrap-and-logout-isolation.md`](./task-04-auth-bootstrap-and-logout-isolation.md) |
| `task-05` | Add Debounced `switchMap` Search & Granular Loading in Admin List | HIGH / MEDIUM | #3, #11 | `Pending` | [`task-05-admin-list-search-and-loading.md`](./task-05-admin-list-search-and-loading.md) |
| `task-06` | Reactive User Detail Routing, Unban RBAC Guard & Shared Ban Modal | MEDIUM | #10, #11, #18 | `Pending` | [`task-06-admin-detail-rbac-and-modal.md`](./task-06-admin-detail-rbac-and-modal.md) |
| `task-07` | Replace Scroll `MutationObserver` & Timer Cascade with Smart rAF Auto-Scroll | HIGH | #8 | `Pending` | [`task-07-smart-chat-scroll.md`](./task-07-smart-chat-scroll.md) |
| `task-08` | Enable `OnPush` Everywhere & Replace Template Method Calls with Pure Pipes | MEDIUM | #13, #14, #23 | `Pending` | [`task-08-onpush-and-pure-pipes.md`](./task-08-onpush-and-pure-pipes.md) |
| `task-09` | Bundle Local PDF.js Worker, Surface Chat/PDF Errors & Clean Up Timers | MEDIUM / LOW | #15, #16, #17, #22 | `Pending` | [`task-09-pdf-worker-errors-and-timers.md`](./task-09-pdf-worker-errors-and-timers.md) |
| `task-10` | Enable Strict TypeScript, Unify Form Validators & Sync Shared Contracts | LOW / Gate | #19, #20, #24 | `Pending` | [`task-10-strict-ts-validators-and-contracts.md`](./task-10-strict-ts-validators-and-contracts.md) |
