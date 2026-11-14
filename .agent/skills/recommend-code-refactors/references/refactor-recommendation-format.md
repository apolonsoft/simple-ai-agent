# Refactor Recommendation Report Format

Use this structure unless the user requests another format.

# Refactor review

## Scope

- Target reviewed:
- Repository instructions consulted:
- Evidence and checks used:
- Important exclusions:

## Baseline

Summarize current behavior, relevant architecture, test coverage, and any pre-existing check failures.

## Recommendations

Create one section per recommendation.

### RF-001: Concise action-oriented title

- **Priority:** High | Medium | Low
- **Confidence:** High | Medium | Low
- **Effort:** Small | Medium | Large
- **Evidence:** `path/to/file.ext:line`, symbols, call sites, or check output
- **Observed problem:** What is wrong now and why it matters
- **Proposed change:** The smallest coherent structural change
- **Expected benefit:** Concrete maintenance, correctness, testability, or performance benefit
- **Behavior and API constraints:** What must remain unchanged
- **Affected scope:** Files, symbols, tests, and dependencies likely involved
- **Validation plan:** Exact tests, checks, or observations that would prove success
- **Risks and tradeoffs:** Regression risks, migration concerns, and costs
- **Dependencies:** Other recommendation IDs or `None`
- **Acceptance criteria:** Verifiable completion conditions

Repeat for additional recommendations using stable IDs.

## Candidates not recommended

List tempting but rejected ideas with a brief evidence-based reason. This prevents a later implementation pass from treating every observation as approved work.

## Suggested implementation order

1. `RF-...` - reason for its position
2. `RF-...` - reason for its position

## Handoff

List the recommendation IDs suitable for independent validation by `apply-validated-refactors`. Note unresolved assumptions or decisions that could block implementation.
