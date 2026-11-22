### Task 04: Replace Cascading Eager Loads with Explicit Loading

- [x] Completed

**Lesson:** [03 — What your ORM does behind your back](../lessons/lesson-03-orm-loading-strategies.md)

#### Full Description
**HIGH.** `lazy="selectin"` on `UserModel.chat_sessions`, `UserModel.password_resets` (`app/models/user.py:43-56`) and `ChatSessionModel.messages` (`app/models/chat.py:29-35`) chains: `db.get(UserModel, id)` in `get_current_user` (`app/core/dependencies.py:60`) loads every session **and every message** the user owns, on every authenticated request. `ChatService.get_session`, `list_user_sessions` and admin `list_users` trigger the same cascade. It also makes the Redis history cache useless, because the ownership check already reads the whole history.

#### Technical Instructions
1. **Failing test first** in `app/tests/test_async_database.py`: create a user with 3 sessions × 5 messages; attach a `before_cursor_execute` listener to the test engine's sync engine; call `get_current_user` directly; assert exactly **1** statement was executed.
2. Set `lazy="raise"` on all three relationships. Keep `cascade="all, delete-orphan"` and `order_by`.
3. Add `passive_deletes=True` to `UserModel.chat_sessions` and `ChatSessionModel.messages` so deleting a session relies on `ON DELETE CASCADE` instead of loading children (FKs already have `ondelete="CASCADE"` in migrations `c1f4e5a9b8d2`). SQLite tests need `PRAGMA foreign_keys=ON`; add a `connect` event listener in `conftest.py`.
4. `app/services/chat_service.py`: add
   ```python
   async def get_session_with_messages(self, session_id, user_id):
       stmt = (
           select(ChatSessionModel)
           .options(selectinload(ChatSessionModel.messages))
           .where(ChatSessionModel.id == session_id, ChatSessionModel.user_id == user_id)
       )
   ```
   and use it only in `ChatController.get_session` (detail endpoint).
5. Run the full suite and fix every `sqlalchemy.exc.InvalidRequestError: 'X' is not available due to lazy='raise'` by adding an explicit `selectinload` at that query, not by relaxing the relationship. `verify_reset_token` already uses `selectinload(PasswordResetModel.user)`; that direction is unaffected.

#### Files Touched
- `apps/api/app/models/user.py` (Modified)
- `apps/api/app/models/chat.py` (Modified)
- `apps/api/app/services/chat_service.py` (Modified)
- `apps/api/app/controllers/chat_controller.py` (Modified)
- `apps/api/app/tests/conftest.py` (Modified — SQLite foreign keys)
- `apps/api/app/tests/test_async_database.py` (Modified)

#### Verification Strategy
- Command: `make test-api && make lint-api && make typecheck-api`
- New statement-count test passes; `GET /chats/{id}` still returns messages.

#### Prepared Git Commit
```text
perf(db): stop cascading eager loads of chat history

- Set lazy="raise" on User.chat_sessions, User.password_resets and
  ChatSession.messages; add passive_deletes for DB-level cascades
- Add ChatService.get_session_with_messages with explicit selectinload,
  used only by the session detail endpoint
- Enable SQLite foreign keys in tests to mirror Postgres cascades
- Add test asserting get_current_user issues a single SQL statement
- Verification: make test-api, make lint-api, make typecheck-api passed
```
