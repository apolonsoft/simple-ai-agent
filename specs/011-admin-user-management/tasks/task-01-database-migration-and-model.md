### Task 01: Database Migration & User Model Updates

- [x] Completed

#### Full Description
Add dedicated administrative ban attributes (`is_banned`, `banned_at`, `ban_reason`) to `UserModel` and create an Alembic database migration to update the `users` table without impacting existing user data.

#### Technical Instructions
1. Update `apps/api/app/models/user.py`:
   - Import `DateTime` from `sqlalchemy`.
   - Add `is_banned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)`.
   - Add `banned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)`.
   - Add `ban_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)`.
   - Update comment on `role` to reflect `"user" | "admin" | "super_admin"`.
2. Create an Alembic migration in `apps/api/alembic/versions/` (e.g. `b1c2d3e4f5a6_add_ban_fields_to_users.py`):
   - Add down-revision pointing to current head (`a1b2c3d4e5f6`).
   - `upgrade()`:
     - `op.add_column("users", sa.Column("is_banned", sa.Boolean(), server_default=sa.text("false"), nullable=False))`
     - `op.add_column("users", sa.Column("banned_at", sa.DateTime(timezone=True), nullable=True))`
     - `op.add_column("users", sa.Column("ban_reason", sa.String(length=500), nullable=True))`
   - `downgrade()`:
     - `op.drop_column("users", "ban_reason")`
     - `op.drop_column("users", "banned_at")`
     - `op.drop_column("users", "is_banned")`
3. Apply migration using `make migrate`.

#### Files Touched
- `apps/api/app/models/user.py` (Modified)
- `apps/api/alembic/versions/b1c2d3e4f5a6_add_ban_fields_to_users.py` (Created)

#### Verification Strategy
- Command: `make migrate && make lint`
- Verify columns exist and all tests pass with zero regression.

#### Prepared Git Commit
```text
feat(api): add ban fields and super_admin role to UserModel and migration

- Add is_banned, banned_at, and ban_reason columns to UserModel
- Create Alembic migration b1c2d3e4f5a6_add_ban_fields_to_users
- Document super_admin in role column domain
- Verification: make migrate passed, make lint passed
```
