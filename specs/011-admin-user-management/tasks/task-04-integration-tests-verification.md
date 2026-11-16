### Task 04: Integration Tests & Monorepo Verification

- [ ] Pending

#### Full Description
Write comprehensive pytest integration tests in `apps/api/app/tests/test_admin_api.py` validating all permissions, role hierarchy restrictions, self-action guardrails, search/filter queries, Redis session invalidation on ban, and unban restoration.

#### Technical Instructions
1. Create `apps/api/app/tests/test_admin_api.py`:
   - Helper fixtures for creating `user`, `admin`, and `super_admin` accounts with tokens.
   - `test_admin_endpoints_unauthorized_and_forbidden_for_regular_user`: Verifies 401 without token and 403 for `user` role.
   - `test_admin_list_users_pagination_search_and_filters`: Verifies pagination, search by email/full_name, and role/status filtering.
   - `test_admin_get_user_detail`: Verifies fetching user details and session counter.
   - `test_admin_ban_user_success_and_immediate_token_revocation`: Verifies user is banned, reason stored, and their active token is immediately rejected with 403 in `get_current_user`.
   - `test_admin_unban_user_success`: Verifies unbanning allows the user to access protected endpoints again.
   - `test_admin_self_ban_guardrail`: Verifies `400 Bad Request` when admin tries to ban themselves.
   - `test_admin_cannot_ban_other_admin_or_super_admin`: Verifies `403 Forbidden` when regular admin attempts to ban admin or super_admin.
   - `test_super_admin_can_ban_regular_admin`: Verifies `super_admin` can ban regular admin, but cannot ban themselves.
   - `test_super_admin_update_role_success`: Verifies promoting user to admin and demoting admin to user.
   - `test_regular_admin_cannot_update_roles`: Verifies `403 Forbidden` when regular admin tries `PATCH /{id}/role`.
   - `test_super_admin_cannot_demote_self`: Verifies `400 Bad Request` when super_admin attempts to alter their own role.
2. Run full monorepo checks:
   - `make lint`
   - `make test-api`
   - `make test-web`

#### Files Touched
- `apps/api/app/tests/test_admin_api.py` (Created)

#### Verification Strategy
- Command: `make test-api && make lint`
- All tests passing with 100% success rate.

#### Prepared Git Commit
```text
test(api): add integration tests for admin user management and ban API

- Add comprehensive test_admin_api suite with 11+ test scenarios
- Test RBAC hierarchy (super_admin vs admin vs user)
- Test Redis session revocation and immediate token rejection upon ban
- Test self-action and superadmin guardrails
- Verification: make test-api passed, make lint passed
```
