# Lesson 04: Object-Level Authorization

**Pattern:** Authentication answers "who are you?". Object-level authorization answers "may *you* touch *this specific object*?". Every ID that arrives from a client is a **claim**, not a permission. The ownership check has to apply to the exact object you are about to read or modify. Checking a related object isn't enough. This bug class is called IDOR, or BOLA in the OWASP API Top 10, and it ranks #1 there.

**Applies to:** Task 05 (tool approval), Task 07 (PDF downloads), Task 12 (unban)

---

## 1. The bug in this repo

```python
# apps/api/app/services/chat_stream_service.py — stream_tool_approval
session = await chat_service.get_session(session_id, user_id)   # ✔ caller owns session_id
...
if message_id:
    target_msg = await db.get(ChatMessageModel, message_id)     # ✘ any message, any user
```

The code checks ownership of `session_id`, then modifies `message_id`. Nothing connects the two. An attacker who knows another user's `message_id` and `tool_call_id` passes their *own* `session_id` and acts on the other user's message.

## 2. Mental model: scope every lookup by the principal
The safest form makes it impossible to fetch an unowned object at all:

```python
# ✘ fetch-then-check (easy to forget the check, easy to check the wrong thing)
msg = await db.get(ChatMessageModel, message_id)

# ✔ scoped query: ownership is part of the identity of the row
stmt = (
    select(ChatMessageModel)
    .join(ChatSessionModel)
    .where(
        ChatMessageModel.id == message_id,
        ChatMessageModel.session_id == session_id,
        ChatSessionModel.user_id == user_id,
    )
)
```

`ChatService.get_session` already does this right (`where(id == session_id, user_id == user_id)`). `AGENT.md` invariant 2 states the rule. The bug is a *consistency* failure, not a knowledge failure. Those are the hardest to catch in review, because the code looks like it checks ownership.

## 3. "But the IDs are UUIDs"
Unguessable IDs reduce exploitability. They are **not** authorization:
- IDs leak through logs, analytics, browser history, shared screenshots, support tickets and error messages.
- IDs appear in API responses. Here, `message_id` is returned to the frontend in the `done` event.
- Defense in depth: when the ID leaks, the authorization check is all that's left.

Rate this kind of bug "HIGH, hard to exploit", never "fine because UUIDs".

## 4. Variants in this repo

| Endpoint | Object from client | Ownership check today | Task |
|---|---|---|---|
| `POST /chats/{id}/tool-calls/approval` | `message_id` | ✘ checks a different object | 05 |
| `GET /chats/files/pdf/{filename}` | `filename` | ✘ any authenticated user | 07 |
| `POST /admin/users/{id}/unban` | `user_id` | ✘ no hierarchy check (ban has one) | 12 |
| `GET /chats/{id}`, `DELETE /chats/{id}` | `session_id` | ✔ scoped query | — |
| `GET /admin/users/{id}` | `user_id` | ✔ role-gated, admins may see all | — |

### Symmetric permissions
Ban has a hierarchy rule; unban doesn't. **An action and its inverse need the same authorization**: ban/unban, grant/revoke, lock/unlock, archive/restore. Otherwise a lower-privileged actor can undo a higher-privileged decision. Put the rule in one shared function (`_assert_can_moderate`) so the two can't drift apart.

### Files are objects too
A file served by name from a shared directory is a table with no `owner_id` column. Either store files under per-tenant prefixes, or check ownership in the database before serving (Task 07).

## 5. How to test it
Every authorization rule deserves a **two-user test**:
```python
token_a, token_b = await make_user(...), await make_user(...)
# A creates an object; B tries to read, modify, delete and approve it → 404
```
Return `404`, not `403`, for objects the caller doesn't own, so you don't confirm that the object exists.

---

## Exercises
1. Write the exact steps an attacker would follow to exploit the tool-approval IDOR, assuming they have obtained the victim's IDs. What can they achieve?
2. Search the backend for `db.get(`. For each call, decide whether the ID came from the client and whether ownership is enforced.
3. Why is `404` better than `403` for an unowned chat session? When is `403` the right answer?
4. Ban says "super_admin accounts cannot be banned". Should unban have an equivalent rule? Reason it through.
5. The PDF fix (Task 07) checks ownership by searching message tool results for the filename. What are the weaknesses of that approach compared to a `generated_files(user_id, filename)` table?

---

## Mentor Notes
1. Attacker B calls `POST /chats/{B_session}/tool-calls/approval` with `{"message_id": A_msg, "tool_call_id": A_call, "approved": true}`. B's session passes the ownership check. A's message is loaded, the tool runs with A's stored arguments, the result and follow-up text are **written into A's message**, and the SSE stream returns the tool result and the arguments (`was approved and executed with arguments {...}`) to B. So B gets both a data leak and an integrity violation, and the stray content shows up in A's history.
2. Expected results: `dependencies.py` (`UserModel`, id from the verified JWT, fine); `admin_service.py` ×4 (`UserModel`, admin-gated, fine apart from the unban hierarchy); `chat_stream_service.py:253` (**vulnerable**); `chat_stream_service.py:400` (`target_msg.id` from the already-loaded object, fine *after* the Task 05 fix).
3. `404` doesn't reveal that the object exists, and from the caller's point of view it doesn't: it isn't in *their* collection. Use `403` when the caller can legitimately know the object exists but lacks the privilege, as with admin endpoints where a regular user is told "admin only".
4. Unbanning a super_admin can't happen, since they can't be banned. The real symmetric rule is the hierarchy: *who* may reverse a moderation action. Regular admins shouldn't reverse actions on admins. Think in terms of "who may change this state", not "who may call this endpoint".
5. Weaknesses: a `LIKE '%name%'` scan over message text (no index, so it slows down as messages grow); it relies on the filename being unique and unguessable (Task 06 ensures that); it breaks if message content is edited or deleted; and it couples file authorization to the chat data format. A table gives an indexed lookup, explicit lifecycle (deleting the files when a user is deleted), and an audit trail. The spec chose the no-migration option for scope reasons. That's a reasonable trade-off, and you should write it down as tech debt.

## Review Checklist
- [ ] For every client-supplied ID, is ownership enforced *on that object*, in the same query?
- [ ] Do action/inverse pairs share one authorization function?
- [ ] Are files authorized like rows?
- [ ] Is there a two-user test for every object type?
- [ ] Do unowned objects return `404`?
