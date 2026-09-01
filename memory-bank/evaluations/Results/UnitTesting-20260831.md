# Unit Testing Evaluation

**Date:** 2026-08-31  
**Rubric:** “What We Will Evaluate” (eight unit-testing checks)  
**Code as of:** [HC-MS4-PLAN-027](../../plans/HC-MS4-PLAN-027-20260831-unit-testing.md)  
**Overall: PASS (8/8)**

Note: The evaluation does not require 100% coverage. Quality and intent of the cases matter more than the coverage number. A well-reasoned 70% is worth more than a mechanical 95%.

This evaluation does **not** close or reopen MS4.

---

## Objectives

Lock HealthCore staff identity and ops API decisions with unit tests: every auth endpoint has happy / edge / failure cases, auth-module coverage ≥70%, Jest for TypeScript helpers, and a `TESTING.md` that records the plan, how to run, coverage, and AI-assisted findings.

## Delivered

| Item | Path |
|---|---|
| Plan, runbook, results | [`TESTING.md`](../../../TESTING.md) |
| FastAPI tests | `services/api/tests/` (36 cases) |
| Jest tests | `uis/backoffice/__tests__/` (12 cases) |
| Pytest entry from repo root | `pytest.ini` |
| Stamp | [HC-MS4-PLAN-027](../../plans/HC-MS4-PLAN-027-20260831-unit-testing.md) |

Auth endpoints mapped (this API has no `/auth/register` or `/auth/token`):

| Module | Endpoint |
|---|---|
| `test_register.py` | `POST /users` |
| `test_login.py` | `POST /auth/login` |
| `test_token.py` | `GET /auth/me` |
| `test_forgot_password.py` | `POST /auth/forgot-password` |
| `test_reset_password.py` | `POST /auth/reset-password` |
| `test_change_password.py` | `POST /auth/change-password` |

## Verification

- `python -m uv run pytest` from **repository root**: **36 passed** (1 Starlette TestClient deprecation warning).
- `python -m uv run pytest --cov` from repository root: suite total **92%**; auth application modules all ≥80% (`security` 100%, `deps.auth` 100%, `routers.auth` 97%, `stores.auth_store` 90%, `routers.users` 80%, `routers.profiles` 89%). Targeted auth-module run in `TESTING.md`: **91%**.
- `cd uis/backoffice && npm test`: **3 suites, 12 tests passed**; collected helpers **79.48%** statements.
- `cd uis/backoffice && npm run lint` and `npx tsc --noEmit`: pass (recorded at PLAN-027).
- This Windows shell did not have `uv` on `PATH`; `python -m uv` (uv 0.12.8) was used as the equivalent of `uv run pytest`.

## Scorecard

| # | Criterion | Result | Evidence |
|---|-----------|--------|----------|
| 1 | `TESTING.md` documents the test plan, how to run tests, and coverage results | **Pass** | Root `TESTING.md` has planned happy/edge/failure tables (written before code), pip/`uv`/Jest run commands, auth 91%, API-042 81%, Jest 79.48%, and AI findings. |
| 2 | `uv run pytest` from the project root runs without errors; all tests pass | **Pass** | Root `pytest.ini` sets `testpaths = services/api/tests`. `python -m uv run pytest` from repo root: 36 passed. Equivalent `python -m pytest` also passes. |
| 3 | Happy-path, edge-case, and failure-mode tests for every authentication endpoint | **Pass** | Register: create / duplicate+min-length / short password. Login: token issued / inactive staff / wrong or unknown credentials. Token/`me`: valid session / deleted staff / missing-garbage-expired + missing `sub`. Forgot: hashed token / unknown email same copy / malformed email. Reset: password replaced / reuse / unknown or expired. Change: new password logs in / wrong current still works / no Bearer. |
| 4 | Authentication module coverage ≥70%, verified with `pytest --cov` | **Pass** | Targeted auth modules **91%**. Bare `--cov` from root **92%** overall; every auth application file ≥80%. Intentional gaps (TinyDB `StorageError`, `GET /users` list, profile-missing 404) are documented in `TESTING.md` rather than padded. |
| 5 | Assertions focus on business logic, not HTTP serialization or framework internals | **Pass** | Cases assert who gets a token, role `user`, duplicate email, inactive vs invalid credentials, generic forgot-password copy, hashed one-time reset, `monthly_rate`/`USA`/`UK`. No OpenAPI/schema/CORS assertions. Status codes are used only as the delivery of those decisions. 422 bodies assert the app’s sanitized invalid-input message, not Pydantic error arrays. |
| 6 | Jest tests present and passing for TypeScript utility functions | **Pass** | `uis/backoffice/jest.config.js` + `__tests__/` for `validateCandidateInput`, `validateNoteContent`, `sanitizeApiDetail` / `getUserFacingError`, and auth token storage. `npm test` 12/12 pass. |
| 7 | AI-assisted workflow documented in `TESTING.md` (at least one AI-identified case or bug) | **Pass** | `TESTING.md` records four agent-identified cases: forgot-password enumeration, inactive vs invalid credentials, register is `POST /users` not `/auth/register`, reset tokens hashed and one-time. No product bugs were found; the rubric accepts an identified case. |
| 8 | Tests are clean: clear names, consistent structure, brief comments for non-obvious assertions | **Pass** | Names state the decision (`test_login_rejects_inactive_staff_with_correct_password`). Modules share `conftest` isolation. Comments only where needed (JWT `role` claim vs store row in `test_users.py`; expiry isolated from password change in `test_reset_password.py`). |

## Gaps / deferred

- `uv` is not on `PATH` in this shell; evaluators with `uv` installed can run `uv run pytest` from the repo root. HealthCore API install path remains pip (`requirements.txt`); AUTH CONTEXT forbids migrating the API to uv.
- Root `src/utils` still uses `node:test` (`npm run test:src`). Jest was added for backoffice helpers (auth-related + FE-019), which satisfies the TypeScript rubric item.
- Bare `pytest --cov` from the repo root also measures test files and non-auth routers; use the `--cov=app.routers.auth …` command in `TESTING.md` when reporting the **auth module** figure.
- Starlette warns that TestClient should use `httpx2`; tests still pass.

## Verdict

The unit-testing assignment is **complete**. Auth endpoints have three-tier cases, coverage is above 70% with documented intent, Jest utilities pass, and `TESTING.md` holds the plan, run instructions, results, and AI-assisted evidence.

## Agent instructions

1. Treat PLAN-027 unit tests as shipped. Do not re-scaffold `services/api/tests/` or `uis/backoffice/__tests__/`.
2. Keep pytest on temporary TinyDB; never point fixtures at live `data/auth.json` or `data/suppliers.json`.
3. When adding an auth or protected ops route, add happy / edge / failure cases and update `TESTING.md` results.
4. Do not add auth Jest tests under `uis/healthcore`.
5. Do not rewrite this eval or prior stamps without explicit human confirmation.
