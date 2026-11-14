### Task 02: UserModel Profile Fields & Alembic Migration

- [ ] Pending

#### Full Description
Add `full_name`, `avatar_url`, and `bio` columns to `UserModel` in `apps/api/app/models/user.py` and create an Alembic migration script to apply the changes to the PostgreSQL `users` table.

#### Technical Instructions
1. In `apps/api/app/models/user.py`, add the following mapped columns to `UserModel`:
   - `full_name: Mapped[str | None] = mapped_column(String(100), nullable=True)`
   - `avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)`
   - `bio: Mapped[str | None] = mapped_column(String(500), nullable=True)`
2. Generate or craft an Alembic migration in `apps/api/alembic/versions/` with revision ID, adding columns `full_name`, `avatar_url`, and `bio` to `users`.
3. Provide downgrade operations to drop these columns cleanly.

#### Files Touched
- `apps/api/app/models/user.py` (Modified)
- `apps/api/alembic/versions/<hash>_add_profile_fields_to_users.py` (Created)

#### Verification Strategy
```bash
apps/api/.venv/bin/python -c "from app.models.user import UserModel; assert hasattr(UserModel, 'full_name'); assert hasattr(UserModel, 'avatar_url'); assert hasattr(UserModel, 'bio'); print('UserModel profile attributes verified')"
```

#### Prepared Git Commit
```text
feat(database): add profile columns to user model and alembic migration

- Add full_name, avatar_url, and bio to UserModel in app/models/user.py
- Create alembic migration script to add profile columns to users table
- Include upgrade and downgrade schema directives
- Verification command passed: model attribute reflection test
```
