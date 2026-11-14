### Task 02: PasswordReset Database Model & Alembic Migration

- [ ] Pending

#### Full Description
Define the `PasswordResetModel` SQLAlchemy model representing password reset tokens, establish the relationship with `UserModel`, export it in models `__init__.py`, and create an Alembic migration script to generate the `password_resets` table with proper foreign keys and indexes.

#### Technical Instructions
1. Create `apps/api/app/models/password_reset.py` declaring `PasswordResetModel` with fields:
   - `id`: UUID primary key, default `uuid.uuid4`
   - `user_id`: UUID ForeignKey to `users.id` (ondelete="CASCADE", index=True)
   - `token_hash`: String(64) unique, index=True
   - `expires_at`: DateTime(timezone=True), index=True
   - `is_used`: Boolean, default=False, nullable=False
   - `used_at`: DateTime(timezone=True), nullable=True
   - `user`: Relationship to `UserModel`
2. Update `apps/api/app/models/user.py` to import `PasswordResetModel` (with `TYPE_CHECKING`) and define `password_resets` relationship with `cascade="all, delete-orphan"`.
3. Update `apps/api/app/models/__init__.py` to export `PasswordResetModel`.
4. Create Alembic migration script in `apps/api/alembic/versions/` creating `password_resets` table.

#### Files Touched
- `apps/api/app/models/password_reset.py` (Created)
- `apps/api/app/models/user.py` (Modified)
- `apps/api/app/models/__init__.py` (Modified)
- `apps/api/alembic/versions/<revision>_create_password_resets_table.py` (Created)

#### Verification Strategy
```bash
apps/api/.venv/bin/pytest apps/api/app/tests/test_auth_api.py -v
```

#### Prepared Git Commit
```text
feat(models): add PasswordResetModel and alembic migration

- Create PasswordResetModel with token_hash, expires_at, and is_used fields
- Add password_resets relationship to UserModel
- Export PasswordResetModel in app/models/__init__.py
- Add alembic migration for password_resets table
- Verification command passed: existing auth tests and model imports pass
```
