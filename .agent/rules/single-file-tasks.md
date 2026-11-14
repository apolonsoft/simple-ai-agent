---
trigger: always_on
---

# Modular Task-Per-File Architecture Rule

1. **Directory Structure:**
   When generating tasks from Plan Mode, do NOT create a monolithic `tasks.md`.
   Instead, create a `tasks/` directory under the feature spec folder:
   ```text
   specs/<feature-dir>/
   ├── spec.md
   ├── plan.md
   └── tasks/
       ├── index.md           # Master roadmap listing status of all tasks
       ├── task-01.md         # Full specifications for Task 1
       ├── task-02.md         # Full specifications for Task 2
       └── ...
2. **Preparatory Refactoring Detection:**
   - When drafting tasks for a feature, inspect the existing codebase first.
   - If the new feature requires altering complex, coupled, or messy legacy code, generate `task-01-refactor-<target>.md` as a prerequisite step.
   - The refactor task must strictly modify architecture/readability with ZERO functional changes and verify that all existing tests still pass before feature tasks begin.
