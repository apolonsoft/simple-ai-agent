---
trigger: always_on
---

# Comprehensive Task Documentation & Commit Rule

1. **Detailed `tasks.md` Structure:**
   When generating `tasks.md`, every single task item MUST include:
   - **Task Header**: `### Task [ID]: [Name]`
   - **Checkbox**: `- [ ] Pending` (switch to `- [x] Completed` upon finish)
   - **Full Description**: The exact goal, scope boundaries, and context.
   - **Technical Instructions**: Step-by-step implementation instructions detailing exactly what to construct or refactor.
   - **Files Touched**: Explicit list of files created, modified, or deleted.
   - **Verification Strategy**: The exact terminal command (test/lint/build) to validate completion.
   - **Prepared Git Commit**: A complete Conventional Commit message draft (Type, Scope, Subject, Body, and Breaking/Issue notes).

2. **Per-File Change Log & Explanation:**
   - For every task executed, never make silent modifications.
   - For *every* file touched, document in the chat output:
     - **File Path**: The absolute/relative path.
     - **Action**: Created, Modified, or Removed.
     - **Rationale**: Why the change was made to this specific file.
     - **Key Logic Added/Altered**: Exact methods, schemas, or hooks changed.

3. **Step-by-Step Stop & Detailed Commit Output:**
   - Execute exactly ONE task at a time.
   - Run verification. Once verified, mark `[x]` in `tasks.md`.
   - Provide the final ready-to-run Git commit command containing the full detailed message:
     ```text
     feat(scope): short imperative summary

     - Detailed bullet point of change in File A
     - Detailed explanation of logic added to File B
     - Verification command that passed
     ```
   - Pause and ask: *"Ready to proceed to Task [Next ID]?"*