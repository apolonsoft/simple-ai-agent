---
trigger: always_on
---

# Step-by-Step Task Execution Rule

1. **Sequential Execution Limit:**
   - When executing from `tasks.md`, implement exactly ONE task at a time.
   - Never chain multiple tasks into a single turn without user approval.

2. **Per-Task Workflow:**
   - Read the next unchecked task (`- [ ]`) in `tasks.md`.
   - Write the required code changes for that specific task only.
   - Run the task's corresponding verification command (tests, typecheck, or linter).
   - If tests pass, mark that task as completed in `tasks.md` (`- [x]`).

3. **Mandatory Pause & Report:**
   - Immediately stop after updating the checkbox.
   - Present a concise summary of:
     - What was modified or created.
     - The verification command output (pass/fail).
     - The next upcoming task.
   - Ask: "Ready to proceed to Task X?" and wait for explicit user confirmation before continuing.