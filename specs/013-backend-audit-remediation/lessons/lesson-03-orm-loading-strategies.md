# Lesson 03: What Your ORM Does Behind Your Back

**Pattern:** An ORM relationship setting is a *global* decision about every query that touches that model. Loading behavior belongs at the query site, where you know what the caller needs, not on the model, where you don't.

**Applies to:** Task 04 (cascading `selectin`), Task 16 (unbounded queries)

---

## 1. The bug in this repo

```python
# apps/api/app/models/user.py
chat_sessions: Mapped[list["ChatSessionModel"]] = relationship(..., lazy="selectin")
password_resets: Mapped[list["PasswordResetModel"]] = relationship(..., lazy="selectin")

# apps/api/app/models/chat.py
messages: Mapped[list["ChatMessageModel"]] = relationship(..., lazy="selectin")
```

```python
# apps/api/app/core/dependencies.py — runs on EVERY authenticated request
user = await db.get(UserModel, user_id)
```

What actually executes:
```sql
SELECT * FROM users WHERE id = :id;
SELECT * FROM chat_sessions   WHERE user_id IN (:id);
SELECT * FROM password_resets WHERE user_id IN (:id);
SELECT * FROM chat_messages   WHERE session_id IN (:s1, :s2, ... :s500);   -- every message, ever
```
A heavy user with 500 sessions × 50 messages makes every request, including rate-limited cheap ones, load 25,000 rows into Python objects. It gets worse linearly with usage, and nothing in the code you look at day to day hints at it.

## 2. Mental model: loading strategies

| `lazy=` | When it loads | Cost profile | Use for |
|---|---|---|---|
| `"select"` (default) | On first attribute access, one query per parent | **N+1** in loops; in async it raises `MissingGreenlet` | Sync code, rarely-accessed relations |
| `"selectin"` | Immediately, one `IN (...)` query per relationship | Always pays, even when unused; **cascades** | Small, always-needed child sets |
| `"joined"` | Immediately, via `LEFT JOIN` | Row multiplication with collections | Many-to-one (`message.session`) |
| `"raise"` | Never; raises on access | Zero; forces an explicit choice | **Default for collections** |
| `"noload"` | Never; returns empty | Silent wrong answers | Almost never |

### Why people end up with `selectin` everywhere in async code
Async SQLAlchemy cannot lazy-load on attribute access, because that would need hidden I/O. Developers hit `MissingGreenlet`, search, and find "use `lazy='selectin'`". The error goes away, and so does any visibility into the cost.

### The cascade
Eager options *chain*: loading `User` eagerly loads `chat_sessions`, and each loaded `ChatSession` eagerly loads `messages`. One innocent `db.get` fans out through the entire object graph.

## 3. The fix pattern
1. **Models:** `lazy="raise"` on collections. Accessing an unloaded relationship becomes a loud error in tests instead of a silent cost in production.
2. **Queries:** ask for exactly what this endpoint needs.
   ```python
   select(ChatSessionModel)
       .options(selectinload(ChatSessionModel.messages))   # only the detail endpoint
       .where(ChatSessionModel.id == session_id, ChatSessionModel.user_id == user_id)
   ```
3. **Deletes:** with collections unloaded, `passive_deletes=True` lets Postgres `ON DELETE CASCADE` do the work instead of SQLAlchemy loading every child just to delete it.

## 4. Unbounded queries (Task 16)
`list_user_sessions` and `get_messages` have no `LIMIT`. "Users don't have that many" is true until a power user, a script, or an attacker shows up.

- **Offset pagination** (`OFFSET 10000 LIMIT 20`) still scans 10,020 rows and shifts when rows are inserted.
- **Keyset/cursor pagination** (`WHERE created_at < :before ORDER BY created_at DESC LIMIT 20`) uses the index directly and is stable. The repo already has `ix_chat_messages_session_created (session_id, created_at)`, which is exactly the index this needs.
- **Fetch what you use:** LLM context uses 10 messages, so query 10 (`ORDER BY created_at DESC LIMIT 10`, then reverse), not all of them.

## 5. Make query counts testable
```python
from sqlalchemy import event

statements: list[str] = []

@event.listens_for(test_engine.sync_engine, "before_cursor_execute")
def _count(conn, cursor, statement, *args):
    statements.append(statement)

await get_current_user(header_token=token, db=session)
assert len(statements) == 1, statements
```
A query-count assertion turns a performance property into a regression test.

---

## Exercises
1. On the current code, how many SQL statements does `GET /api/v1/chats` execute for a user with 3 sessions? List them.
2. The Redis chat cache exists to avoid reading history from Postgres. Explain why it currently saves nothing.
3. After setting `lazy="raise"`, which existing endpoint will break first, and what's the right fix: change the model back, or change the query?
4. Why is `lazy="joined"` a bad choice for `ChatSessionModel.messages` specifically?
5. Design the query for "load the last 10 messages of a session in chronological order" that uses the existing index.

---

## Mentor Notes
1. `get_current_user`: users, chat_sessions, password_resets, chat_messages (4). Then `list_user_sessions`: chat_sessions, plus a selectin for chat_messages again (2). That's about **6 statements**, and two of them load every message the user has. The endpoint needed only one: the session list.
2. `stream_chat` checks ownership with `chat_service.get_session(...)`, which eagerly loads `messages` through `selectin`. The full history is read from Postgres *before* the cache is consulted, and `get_current_user` already read it once. The cache only skips a third read. **Always measure whether an optimization actually removes work.**
3. `GET /chats/{session_id}`: `ChatSessionDetailResponse.model_validate(session)` reads `session.messages`. The right fix is a query with `selectinload` for that endpoint (`get_session_with_messages`). Relaxing the model would bring the cost back everywhere.
4. A `JOIN` with a one-to-many collection repeats the parent row once per child. With `LIMIT` on the parent query, SQLAlchemy has to wrap it in a subquery to paginate correctly. `selectin` per query is cleaner for collections; `joined` is for many-to-one.
5. ```python
   stmt = (
       select(ChatMessageModel)
       .where(ChatMessageModel.session_id == session_id)
       .order_by(ChatMessageModel.created_at.desc())
       .limit(10)
   )
   rows = list((await db.scalars(stmt)).all())
   rows.reverse()
   ```
   Postgres walks `ix_chat_messages_session_created` backwards and stops after 10 rows.

## Review Checklist
- [ ] Any `lazy="selectin"` or `lazy="joined"` on a *collection* in a model? Why?
- [ ] Does every list query have a `LIMIT`?
- [ ] Is pagination keyset-based where the data grows?
- [ ] For hot paths (auth, rate-limited endpoints), is there a statement-count test?
- [ ] Does each `ORDER BY ... LIMIT` have a matching composite index?
