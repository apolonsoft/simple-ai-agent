---
trigger: always_on
---

# Spec-Kit Artifact Generation Rule

When working in Plan Mode:

1. **Clarification Phase:**
   - Ask 2–4 targeted clarifying questions before finalizing any plan.

2. **UI Planning Phase:**
   - Present the implementation strategy using the native Plan Mode Artifact for user review.

3. **Disk Persistence (Spec-Kit Files):**
   - As soon as the user approves the plan (or gives the go-ahead), create a feature directory under `specs/` (e.g., `specs/001-<feature-name>/`) and write the following three files to disk:
     - `spec.md`: User stories, acceptance criteria, boundaries, and answered clarifications.
     - `plan.md`: Technical architecture, affected files, schemas, and dependencies.
     - `tasks.md`: Ordered markdown checklist (`- [ ]`) broken into atomic, verifiable phases.

4. **Execution Phase:**
   - Only begin modifying application code after the Spec-Kit files are written to disk.
   - Update `tasks.md` checkboxes (`- [x]`) as each phase is completed and verified.