# Lesson 01: Never Trust the Request Body

**Pattern:** Everything that crosses a trust boundary is attacker-controlled until you prove otherwise. That covers request bodies, headers, filenames, content types, and search terms. The most dangerous version is *mass assignment*: a request field flows straight into a privileged database column.

**Applies to:** Task 02 (role), Task 17 (avatar), Task 20 (message size), Task 21 (search wildcards)

---

## 1. The bug in this repo

```python
# apps/api/app/schemas/user.py
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str = "user"
```

```python
# apps/api/app/services/auth_service.py — register_user
user = UserModel(
    email=user_in.email, hashed_password=hashed_pw, role=user_in.role
)
```

The Angular register form never sends `role`, so it *looks* safe in the browser. But the API is the trust boundary, not the UI. `curl` doesn't run your form validators.

## 2. Mental model: the trust boundary
Draw a line around the code you control. Everything entering through that line is **untrusted input**:

| Input | Example in this repo | What can go wrong |
|---|---|---|
| JSON body fields | `UserCreate.role` | Privilege escalation |
| Field sizes | `ChatMessageCreate.content` (no max) | Storage, cache, and LLM-cost exhaustion |
| Uploaded file bytes | `await file.read()` | Memory exhaustion |
| `Content-Type` header | Avatar upload | A mismatched type gets stored |
| Filenames | Avatar extension from `file.filename` | Wrong extension or MIME on the stored object |
| Search terms | `ilike(f"%{term}%")` | `%` and `_` act as wildcards |
| LLM tool arguments | `inspect_pdf(file_path=...)` | Covered in Lesson 08 |

**Rule:** Input DTOs should describe *exactly* what a client is allowed to influence, with sizes. Server-owned fields such as `role`, `is_banned`, `owner_id` and `status` never appear in a create/update DTO for a normal user.

## 3. Why tests didn't catch it
Look at `apps/api/app/tests/test_admin_api.py`:

```python
json={"email": email, "password": password, "role": role},
```

The test suite *uses the vulnerability as a feature* to create admins quickly. This is common: when a test helper needs a privileged user, the easiest path is often the insecure one, and the bug gets cemented. Privileged fixtures should go through the database or an admin-only path (Task 02 adds `make_user`).

## 4. Defense in depth
Fix it in **two** places:
1. **Schema**: remove `role`, so the field cannot even be parsed.
2. **Service**: hard-code `role="user"`, so a future refactor that re-adds a field, or a caller that builds `UserCreate` by hand, still can't escalate.

Then add a **test that sends the forbidden field** and asserts it was ignored. That test is the executable record of the security requirement.

### `extra="ignore"` vs `extra="forbid"`
Pydantic ignores unknown fields by default. `forbid` gives a loud `422`, which helps during development, but it breaks older clients that still send the field. For a public API, `ignore` plus a test is usually the right call. For internal or admin APIs, `forbid` catches client bugs early.

## 5. Bounds are part of validation
"Valid" means type *and* size. Add `max_length` to every free-text field, and read uploads with `read(limit + 1)`. Unbounded input is how a valid request becomes a denial of service.

---

## Exercises
Answer before reading the mentor notes.

1. Write the exact `curl` command that creates a `super_admin` on the current code.
2. `ToolApprovalRequest` in `apps/api/app/schemas/chat.py` has `tool_name` and `arguments` fields. Are they used today? What would happen if a future developer started using them?
3. Find one more place where a client-controlled value decides something the server should decide.
4. Why is `UserProfileUpdate` safe while `UserCreate` wasn't? What property makes the difference?
5. Should `LIKE` wildcard escaping be considered a security fix or a correctness fix? Defend your answer.

---

## Mentor Notes

1. ```bash
   curl -X POST localhost:8000/api/v1/auth/register \
     -H 'Content-Type: application/json' \
     -d '{"email":"x@evil.com","password":"password123","role":"super_admin"}'
   ```
   Then log in normally; `require_super_admin_role` reads `role` from the database and lets you in.
2. They are **not used**: `stream_tool_approval` reads the tool name and arguments from the stored message. That's correct, because the approval should cover *what the model proposed*. If someone "simplified" the code to use `approval_in.arguments`, a user could approve a harmless proposal and run it with different arguments, which defeats human-in-the-loop entirely. Unused privileged-looking fields in a DTO are a trap; delete them, or document why they are ignored.
3. Candidates: `X-Forwarded-For` choosing the rate-limit identity (Lesson 09); the avatar extension taken from `file.filename`; `message_id` choosing which message is modified (Lesson 04); LLM-generated `file_path` (Lesson 08).
4. `UserProfileUpdate` is an **allowlist** of fields the user owns (`full_name`, `bio`), each with a `max_length`, and the service copies them one at a time. `UserCreate` mixed user-owned and server-owned fields. The test to apply: "would I be fine with *any* value in this field?"
5. Both. Using it, a non-admin can't access more data, because admin search is already admin-only, so it's mostly correctness. But in a user-facing search, wildcard injection can turn a cheap indexed prefix query into a full scan (`%%%%`), which makes it a DoS vector. Severity depends on who can reach it, which is why it's LOW here.

## Review Checklist
- [ ] Does any request DTO contain a server-owned field (`role`, `status`, `owner_id`, `is_*`)?
- [ ] Does every free-text field have `max_length`? Every list a `max_length`?
- [ ] Are uploads read with a bound?
- [ ] Is there a test that sends a forbidden field and asserts it was ignored?
- [ ] Do test fixtures create privileged users through a privileged path?
