---
name: apply-validated-refactors
description: Independently validate proposed code refactors against the current repository, implement only recommendations that are technically sound and in scope, and verify behavior with the repository's tests and static checks. Use when the user asks to check a refactor recommendation, plan, review report, issue, or comment and then apply the valid items. Do not use for recommendation-only reviews or unrelated feature work.
---

# Apply Validated Refactors

Treat every recommendation as a hypothesis. Validate it against the current code before making changes, then implement only the valid portion.

## Accepted inputs

Use recommendations from any of these sources:

- the current conversation;
- a report or plan file;
- selected recommendation IDs such as `RF-001`;
- a pull request review, issue, or pasted comment;
- an explicit user description of a proposed refactor.

Do not invent additional refactors merely because nearby code could also be improved. Invocation with a request to apply valid recommendations is permission to make the necessary non-destructive edits; do not ask for a second confirmation.

## Safety rules

- Read and obey all applicable `AGENTS.md` and repository instructions before editing.
- Inspect `git status` and the relevant diff first. Preserve all pre-existing user changes.
- Never use destructive Git commands such as `reset`, `clean`, forced checkout, or blanket restoration. Do not stash, commit, amend, rebase, or push unless the user explicitly asks.
- Do not install, remove, or upgrade dependencies unless the validated refactor requires it and the user has authorized dependency changes.
- Keep public behavior, data formats, error semantics, and compatibility unchanged unless the user explicitly approved a breaking change.
- Do not modify generated, vendored, migration, snapshot, or lock files unless repository conventions and the validated change require it.
- Never weaken or delete meaningful tests merely to make a refactor pass.
- Do not implement recommendations classified as invalid, blocked, already resolved, or outside scope.

## Workflow

1. **Collect and normalize the recommendations**
   - Identify each requested item and preserve its existing ID when present.
   - Extract the claimed problem, proposed change, expected benefit, constraints, and validation plan.
   - If several items are supplied, determine dependencies and process them in a safe order.

2. **Establish the current baseline**
   - Read repository instructions, relevant documentation, manifests, and build configuration.
   - Inspect the current implementation, callers, tests, and public interfaces.
   - Record the starting worktree state and pre-existing diff without changing it.
   - Run the narrowest safe existing checks needed to understand current behavior. Record pre-existing failures separately.

3. **Validate each recommendation independently**
   Apply the rubric in `references/validation-rubric.md` and assign exactly one decision:
   - **VALID:** The evidence is current, the change addresses the root cause, and the proposed scope is justified.
   - **PARTIALLY_VALID:** The problem is real, but the proposal must be narrowed or corrected. Apply only the justified version and explain the deviation.
   - **INVALID:** The premise is false, the proposal would not solve it, or risk exceeds justified benefit. Make no change for this item.
   - **ALREADY_RESOLVED:** The current code no longer has the reported problem. Make no change.
   - **BLOCKED:** Validation or safe implementation requires missing information, environment access, a product decision, or an unauthorized breaking/dependency change. Make no change.

4. **Plan the smallest safe patch**
   - Preserve behavior and existing architecture contracts.
   - Prefer localized, independently testable edits over broad rewrites.
   - Identify tests to add or update before changing code.
   - Keep unrelated cleanup out of the patch.

5. **Implement one validated item at a time**
   - Follow existing naming, formatting, typing, error-handling, and test conventions.
   - Update tests when structure changes or current coverage cannot prove preserved behavior.
   - Re-check the diff after each item so changes do not expand beyond its validated scope.
   - If an item fails verification and cannot be corrected within scope, reverse only the edits introduced for that item and mark it blocked. Never discard unrelated user changes.

6. **Verify the completed work**
   - Run the relevant focused tests first, then broader format-check, lint, type-check, build, and test commands when practical. Prefer check-only formatter modes; if a repository formatter changes files, inspect the result and retain only in-scope formatting.
   - Compare failures with the recorded baseline and clearly distinguish pre-existing failures from regressions.
   - Inspect the final diff for accidental API changes, duplicated logic, debug output, generated noise, or unrelated edits.
   - Confirm each acceptance criterion for every implemented item.

7. **Report decisions and evidence**
   Use this structure:

   ```markdown
   # Refactor validation and implementation

   ## Worktree and baseline
   [Starting state, instructions followed, and pre-existing failures]

   ## Validation decisions
   | ID | Decision | Evidence and reason | Action |
   |---|---|---|---|
   | RF-001 | VALID | ... | Implemented |

   ## Changes made
   [Files and symbols changed, grouped by recommendation ID]

   ## Verification
   [Commands run and outcomes]

   ## Not applied
   [Invalid, blocked, already resolved, or out-of-scope items]

   ## Remaining risks
   [Only concrete residual risks or `None`]
   ```

## Completion standard

Do not say the refactor is complete merely because the code compiles. Completion requires a recorded validation decision, a scope-controlled diff, relevant verification, and an explanation of any item not applied.
