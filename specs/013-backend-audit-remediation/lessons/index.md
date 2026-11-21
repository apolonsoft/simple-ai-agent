# Mentoring Lessons: Backend Audit Remediation

These lessons turn the audit findings into reusable engineering judgment. Each one teaches a **pattern** that recurs across codebases, shows where it bit this repo, and links to the tasks that fix it.

## How to use these lessons
1. Read the lesson up to **Exercises**.
2. Answer the exercises in writing, before scrolling to **Mentor Notes**. Rough or wrong answers are fine; they show what to focus on.
3. Compare with the mentor notes.
4. Do the linked task. Write the failing test first, then the fix.
5. Add the lesson's **Review Checklist** to your own pull-request habit.

## Learning path

| # | Lesson | Pattern | Tasks |
|---|---|---|---|
| 01 | [Never trust the request body](./lesson-01-trust-boundaries-and-mass-assignment.md) | Trust boundaries, mass assignment, input bounds | 02, 17, 20, 21 |
| 02 | [Resource lifetimes](./lesson-02-resource-lifetimes.md) | Connection pools, transactions, yield dependencies, cancellation | 03, 22 |
| 03 | [What your ORM does behind your back](./lesson-03-orm-loading-strategies.md) | Loading strategies, N+1, unbounded queries | 04, 16 |
| 04 | [Object-level authorization](./lesson-04-object-level-authorization.md) | IDOR/BOLA, scoped queries, symmetric permissions | 05, 07, 12 |
| 05 | [Check-then-act races](./lesson-05-check-then-act-races.md) | TOCTOU, locks, constraints, atomic operations | 05, 09, 20 |
| 06 | [What actually blocks the event loop](./lesson-06-event-loop-blocking.md) | Cooperative scheduling, thread offload, per-request setup cost | 08, 17, 19 |
| 07 | [Session revocation and failure modes](./lesson-07-session-revocation-and-failure-modes.md) | Stateless tokens, fail-open vs fail-closed, timeouts | 01, 11, 13, 15 |
| 08 | [Agent tools are untrusted input](./lesson-08-sandboxing-agent-tools.md) | Capability confinement, prompt injection, tenant isolation | 06, 07 |
| 09 | [Trusting infrastructure](./lesson-09-trusting-infrastructure.md) | Proxy headers, secure defaults, secrets in URLs, CORS | 09, 10, 21 |
| 10 | [Side channels](./lesson-10-side-channels-and-enumeration.md) | Timing-based enumeration, background work | 18 |
| 11 | [Cache correctness](./lesson-11-cache-correctness.md) | Read-modify-write, bounded caches, stampedes, measuring value | 14, 19 |

Suggested order: 01 → 02 → 03 → 04 → 05 → 06 → 07, then 08–11 in any order. That matches the task order, so each lesson comes right before the task that applies it.

## The meta-lesson
Almost every finding in the audit was a mismatch between what the code **assumes** and what is **actually guaranteed**:
- The code assumes the client sends only the fields the UI sends. Nothing guarantees it.
- It assumes a dependency's session closes when the handler returns. With streaming, it doesn't.
- It assumes loading one user loads one row. With chained `selectin`, it doesn't.
- It assumes checking one object's owner protects another object. It doesn't.
- It assumes two requests never interleave. They do.

The habit to build: for each line you write, ask *"what guarantees this?"* If the answer is "nothing", you've found the next bug.
