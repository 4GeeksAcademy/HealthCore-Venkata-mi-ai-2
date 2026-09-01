---
stamp: HC-MS4-PLAN-027
sequence: 27
milestone: MS4
date: 20260831
title: Unit Testing Auth Pytest Jest and Backlog Suites
status: implemented
phase: implementation
summary: Added TESTING.md, FastAPI pytest (happy/edge/failure for auth plus API-042 suppliers and incidents), and Jest tests for backoffice utilities (FE-019). Auth module coverage 91%; API-042 81%; Jest 12 passing tests.
related_paths:
  - TESTING.md
  - pytest.ini
  - .gitignore
  - services/api/pytest.ini
  - services/api/requirements-dev.txt
  - services/api/tests/conftest.py
  - services/api/tests/test_register.py
  - services/api/tests/test_login.py
  - services/api/tests/test_token.py
  - services/api/tests/test_forgot_password.py
  - services/api/tests/test_reset_password.py
  - services/api/tests/test_change_password.py
  - services/api/tests/test_security.py
  - services/api/tests/test_users.py
  - services/api/tests/test_profiles.py
  - services/api/tests/test_suppliers.py
  - services/api/tests/test_incidents.py
  - uis/backoffice/jest.config.js
  - uis/backoffice/package.json
  - uis/backoffice/__tests__/validators.test.ts
  - uis/backoffice/__tests__/user-facing-error.test.ts
  - uis/backoffice/__tests__/auth-storage.test.ts
  - memory-bank/plans/INDEX.md
  - memory-bank/progress.md
do_not_repeat:
  - Point pytest at live services/api/data/auth.json or suppliers.json
  - Assert FastAPI/Pydantic error-array shape instead of business decisions
  - Add auth Jest tests under uis/healthcore
  - Rewrite prior plan stamps or CONTEXT.md for this testing work
---

# HC-MS4-PLAN-027 — Unit Testing Auth Pytest Jest and Backlog Suites

## Decisions locked

- Test plan lives in root `TESTING.md` (planned cases written before code).
- FastAPI tests live in `services/api/tests/` with isolated temp TinyDB.
- Register is tested as `POST /users`; session identity as `GET /auth/me`.
- Jest covers backoffice helpers only (`validators`, `user-facing-error`, `auth-storage`). Root `src/utils` stays on `node:test`.
- Coverage targets met: auth module 91% (≥70%), API-042 81% (≥50%).

## Agent instructions

1. Keep pytest fixtures on temporary TinyDB paths; never write live `data/auth.json` or `data/suppliers.json`.
2. Assert staff identity and ops decisions (who gets a token, duplicate email, generic forgot-password copy), not framework serialization.
3. Do not add login/token Jest tests to `uis/healthcore`.
4. When adding endpoints, extend the matching test module with happy / edge / failure cases and update `TESTING.md` results.
