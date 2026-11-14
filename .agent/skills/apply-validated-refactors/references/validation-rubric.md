# Refactor Validation Rubric

Evaluate every proposed refactor against all categories below. A recommendation does not become valid merely because it sounds reasonable.

## 1. Factual basis

- Does the claimed duplication, coupling, complexity, dead code, performance issue, or testability problem exist in the current revision?
- Are cited files, symbols, and call paths still present?
- Is the evidence representative rather than an isolated example?

## 2. Root-cause fit

- Would the proposal remove or reduce the actual cause?
- Could it move complexity elsewhere, duplicate a different abstraction, or hide the problem?
- Is a smaller change equally effective?

## 3. Behavioral safety

- What observable behavior, API, schema, ordering, timing, error contract, or side effect could change?
- Are callers and downstream consumers accounted for?
- Can behavior preservation be tested or otherwise demonstrated?

## 4. Architectural fit

- Does the change follow repository boundaries and conventions?
- Does it improve cohesion and reduce coupling rather than create a premature abstraction?
- Is the abstraction supported by multiple real use cases?

## 5. Scope and proportionality

- Is the expected benefit worth the patch size, review cost, and regression risk?
- Can the work be split into independently verifiable steps?
- Does the proposal avoid unrelated cleanup and speculative future requirements?

## 6. Verification quality

- Are existing tests relevant and trustworthy?
- Are new tests needed to lock in current behavior?
- Which format, lint, type-check, build, test, benchmark, or manual checks prove success?

## Decision guidance

- Use **VALID** only when all material concerns are resolved.
- Use **PARTIALLY_VALID** when a narrower or corrected implementation satisfies the real need.
- Use **INVALID** when the premise or solution is unsound.
- Use **ALREADY_RESOLVED** when the current code already addresses the issue.
- Use **BLOCKED** when safe validation or implementation cannot be completed with available authority or evidence.
