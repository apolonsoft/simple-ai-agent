---
name: recommend-code-refactors
description: Review source code or a repository for evidence-backed refactoring opportunities and produce a prioritized, implementation-ready recommendation report without modifying project files. Use when the user asks to inspect code quality, identify maintainability problems, recommend refactors, prepare a refactor plan, or review a module before changing it. Do not use when the user asks to implement the refactor; use apply-validated-refactors instead.
---

# Recommend Code Refactors

Review the actual implementation and produce an actionable refactor plan. Keep the repository read-only.

## Boundaries

- Do not edit, format, rename, move, or delete source, configuration, test, generated, or documentation files. Create a report file only when the user explicitly requests one.
- Do not install or upgrade dependencies.
- Do not commit, stash, reset, clean, check out files, or otherwise alter Git state.
- Run only commands that are reasonably non-mutating. Avoid tests or scripts that write to external systems, production services, shared databases, or user data.
- Treat repository instructions such as `AGENTS.md` as authoritative.
- Base every recommendation on concrete code evidence. Do not give generic style advice.
- Say explicitly when no worthwhile refactor is justified.

## Workflow

1. **Establish scope**
   - Resolve the target from the user request: repository, directory, files, diff, pull request, or named component.
   - When no target is named, inspect the current worktree and focus on the files relevant to the request, current diff, or central execution path. State the chosen scope.
   - Read applicable `AGENTS.md` files, project documentation, manifests, build configuration, and architecture notes.
   - Inspect `git status` and the relevant diff so current user work is understood but never changed.

2. **Understand current behavior**
   - Trace callers, callees, data flow, state changes, error paths, and public interfaces.
   - Locate relevant tests and repository-provided format, lint, type-check, build, and test commands.
   - Run existing checks only when they are safe and useful. Record failures as baseline evidence rather than assuming the reviewed code caused them.

3. **Find candidate opportunities**
   Look for material problems such as:
   - duplicated behavior or divergent implementations of the same rule;
   - mixed responsibilities, high coupling, or unclear module boundaries;
   - deeply nested or hard-to-follow control flow;
   - leaky abstractions, unnecessary state, or hidden side effects;
   - inconsistent error handling or lifecycle management;
   - dead or unreachable code supported by call-site evidence;
   - testability barriers caused by design rather than missing mocks alone;
   - performance or resource-management problems supported by measurements or a clear hot path.

   Ignore cosmetic preferences unless they materially reduce defects or maintenance cost. Do not recommend a rewrite merely because a file is large.

4. **Challenge each candidate**
   Before recommending it, verify that:
   - the problem exists in the current code;
   - the proposal addresses the root cause rather than a symptom;
   - the scope is proportional to the expected benefit;
   - observable behavior and required compatibility can be preserved;
   - a concrete validation method exists;
   - a simpler local change would not achieve the same result with less risk.

   Reject speculative, outdated, redundant, or unjustifiably broad candidates.

5. **Prioritize the valid recommendations**
   - Rank by expected maintenance or reliability benefit, confidence, risk, and effort.
   - Separate prerequisites from optional follow-ups.
   - Prefer a small sequence of independently verifiable changes over a large rewrite.

6. **Produce the report**
   - Follow `references/refactor-recommendation-format.md`.
   - Assign stable IDs such as `RF-001` so another agent can validate and apply selected items.
   - Cite evidence as `path:line` or a precise symbol when line numbers are unstable.
   - Distinguish observed facts from hypotheses.
   - Do not claim that a recommendation is safe unless its risks and validation plan are stated.

## Handoff rules

- End with an ordered implementation sequence and the IDs recommended for the next pass.
- State that each recommendation remains a hypothesis until `apply-validated-refactors` checks it against the then-current repository.
- When the user requests a saved report, write only to the requested report path; otherwise return the report in the response and leave the worktree unchanged.
