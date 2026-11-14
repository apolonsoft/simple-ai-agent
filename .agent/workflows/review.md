---
description: Review uncommitted changes or current task against specs, tests, and security
---

# Code Review Workflow

Target: {{input}} (defaults to uncommitted git diff if not specified)

1. **Context & Diff Gathering:**
   - Run `git diff HEAD` to capture all staged and unstaged changes.
   - If a task file was referenced or is active (e.g. `tasks/task-01.md`), verify the diff against that task's acceptance criteria.

2. **Audit Categories:**
   - 🔴 **Bugs & Edge Cases**: Unhandled exceptions, missing null checks, boundary bugs.
   - 🟡 **Security & Perf**: Unsanitized inputs, leaking secrets, avoidable memory/query loops.
   - 🟢 **Spec Adherence**: Did we follow the task requirements without adding unneeded bloat?

3. **Output Format:**
   - Group findings by file and line.
   - Keep remarks short and actionable.
   - Conclude with a clear verdict: **Ready to Commit** or **Needs Changes**.
   - Do NOT edit code automatically; ask if you should fix the issues.