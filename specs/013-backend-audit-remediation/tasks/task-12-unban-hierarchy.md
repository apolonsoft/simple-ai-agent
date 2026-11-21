### Task 12: Enforce Hierarchy on Unban

- [ ] Pending

**Lesson:** [04 — Object-level authorization](../lessons/lesson-04-object-level-authorization.md)

#### Full Description
**MEDIUM.** `AdminService.ban_user` enforces "regular admins can't act on admins" (`app/services/admin_service.py:140-151`), but `unban_user` (`:175-205`) has no such check. A regular admin can undo a super_admin's ban of another admin. Authorization rules for an action and its inverse must match.

#### Technical Instructions
1. **Failing test first** in `app/tests/test_admin_api.py`: super_admin bans admin X; regular admin Y calls unban on X → `403`; super_admin unban → `200`.
2. Extract the hierarchy check into a private method shared by ban and unban:
   ```python
   def _assert_can_moderate(self, actor: UserModel, target: UserModel) -> None:
       if actor.id == target.id:
           raise HTTPException(400, "Administrators cannot moderate their own account.")
       if actor.role != "super_admin" and target.role in ("admin", "super_admin"):
           raise HTTPException(403, "Insufficient permissions to moderate administrative accounts.")
   ```
   Keep the existing ban-specific message texts if tests assert them (check `test_admin_api.py`) — pass the verb in, or keep separate messages.
3. Keep "super_admin cannot be banned" as a ban-only rule.

#### Files Touched
- `apps/api/app/services/admin_service.py` (Modified)
- `apps/api/app/tests/test_admin_api.py` (Modified)

#### Verification Strategy
- Command: `cd apps/api && .venv/bin/pytest app/tests/test_admin_api.py -v && cd ../.. && make lint-api && make typecheck-api`

#### Prepared Git Commit
```text
fix(admin): apply the same hierarchy rules to unban as to ban

- Extract _assert_can_moderate shared by ban_user and unban_user
- Regular admins can no longer unban admin or super_admin accounts
- Add regression test for unban hierarchy
- Verification: pytest test_admin_api.py, make lint-api,
  make typecheck-api passed
```
