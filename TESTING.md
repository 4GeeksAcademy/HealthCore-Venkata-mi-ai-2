# HealthCore Digital — Unit Testing

Staff identity and ops APIs must be trustworthy for Monday-morning numbers (Tom Callahan, Marcus Reid, Diane Foster). These tests lock **business decisions**: who gets a session, who is rejected, and how supplier/incident data is accepted or refused. They do **not** assert FastAPI serialization, OpenAPI schema, CORS, or Next.js framework internals.

Synthetic identities only (`qa.staff@healthcore.example`). Never log passwords, reset tokens, or patient-adjacent text.

---

## How to run

HealthCore API install path is **pip** (`services/api/requirements.txt`). The assignment command `uv run pytest` is supported from the FastAPI project directory if `uv` is installed. Both entry points collect the same suite.

### FastAPI (pytest)

```bash
cd services/api
python -m pip install -r requirements.txt -r requirements-dev.txt

# All tests
python -m pytest

# Assignment-equivalent
uv run pytest

# Auth module coverage (target: ≥70%)
python -m pytest --cov=app.routers.auth --cov=app.routers.users --cov=app.deps.auth --cov=app.core.security --cov=app.stores.auth_store --cov=app.routers.profiles --cov-report=term-missing

# API-042 coverage (target: ≥50% on suppliers + incidents)
python -m pytest tests/test_suppliers.py tests/test_incidents.py --cov=app.routers.suppliers --cov=app.routers.incidents --cov=app.suppliers_store --cov=app.incident_analysis --cov=app.result_store --cov-report=term-missing
```

From the **repository root** (same suite):

```bash
python -m pytest
```

Tests use a temporary TinyDB. They never write `services/api/data/auth.json` or `services/api/data/suppliers.json`.

### TypeScript (Jest)

```bash
cd uis/backoffice
npm install
npm test
# Assignment-equivalent extra flag (npm requires `--` to forward args):
npm test -- --coverage
```

Root ops utilities remain on `node:test` (`npm run test:src` from the repo root). That suite is unchanged and is **not** a substitute for Jest.

---

## What each suite covers

| Suite | Path | Why it exists |
|---|---|---|
| Register | `services/api/tests/test_register.py` | `POST /users` creates staff + profile; duplicate email is refused |
| Login | `services/api/tests/test_login.py` | Only active staff with the correct password receive a JWT |
| Token / me | `services/api/tests/test_token.py` | Bearer JWT is required to identify the current staff member |
| Forgot password | `services/api/tests/test_forgot_password.py` | Same generic reply whether the email exists (no enumeration) |
| Reset password | `services/api/tests/test_reset_password.py` | Reset tokens are one-time and expire |
| Change password | `services/api/tests/test_change_password.py` | Authenticated staff must prove the current password |
| Security helpers | `services/api/tests/test_security.py` | Password hash/verify and JWT decode decisions |
| Suppliers (API-042) | `services/api/tests/test_suppliers.py` | Directory CRUD/filter rules after AUTH-01 protection |
| Incidents (API-042) | `services/api/tests/test_incidents.py` | CSV analyze/export accept/reject rules |
| Frontend utils (FE-019) | `uis/backoffice/__tests__/` | Hiring validators, safe error copy, token storage |

---

## Planned test cases

Written **before** implementation. HealthCore has no `/auth/register` or `/auth/token`. Assignment module names map as follows:

- `test_register.py` → `POST /users`
- `test_login.py` → `POST /auth/login`
- `test_token.py` → `GET /auth/me` (JWT session identity)

AUTH-03 routes are included so the auth module can meet the 70% coverage bar.

### `POST /users` — register

| Tier | Case | Business assertion |
|---|---|---|
| Happy | Valid email + password of at least 8 characters | Staff is created as role `user`, `is_active` true, a linked profile exists, password is not returned |
| Edge | Duplicate email (different case / surrounding space) | Refused as email already exists; second account is not created |
| Edge | Password exactly 8 characters | Accepted (minimum length boundary) |
| Failure | Password shorter than 8, or not an email | Request is rejected as invalid input |

### `POST /auth/login`

| Tier | Case | Business assertion |
|---|---|---|
| Happy | Active staff, correct password | Access token issued; token subject is that user id |
| Edge | Inactive staff, correct password | No token; treated as inactive (not a credential mismatch) |
| Failure | Wrong password or unknown email | No token; invalid credentials (no user leak) |

### `GET /auth/me` — token

| Tier | Case | Business assertion |
|---|---|---|
| Happy | Valid Bearer token | Returns id, email, role, active flag, and profile |
| Edge | Staff deleted after the token was issued | Credentials are no longer valid |
| Failure | Missing, garbage, or expired JWT | Access denied |

### `POST /auth/forgot-password`

| Tier | Case | Business assertion |
|---|---|---|
| Happy | Registered email | Generic 200 message; stored reset secret is a hash, not the raw token |
| Edge | Unknown email | **Same** generic 200 message — no “user not found” |
| Failure | Malformed email | Rejected as invalid input |

### `POST /auth/reset-password`

| Tier | Case | Business assertion |
|---|---|---|
| Happy | Valid unused token + new password ≥8 | Password is replaced; old password no longer logs in |
| Edge | Token reused after success | Rejected as invalid or expired |
| Failure | Unknown or expired token | Rejected as invalid or expired |

### `POST /auth/change-password`

| Tier | Case | Business assertion |
|---|---|---|
| Happy | Authenticated, correct current password | Subsequent login uses the new password |
| Edge | Authenticated, wrong current password | Refused; old password still works |
| Failure | No Bearer token | Access denied |

### API-042 — suppliers (`/suppliers`)

| Tier | Case | Business assertion |
|---|---|---|
| Happy | Authenticated create + list | New row uses `monthly_rate`, `USA`/`UK`, `USD`/`GBP` pairing |
| Edge | Filter by `country` and/or `category` | Only matching rows |
| Failure | Unknown id on get / patch / delete | Supplier not found |
| Failure | No token | Access denied |

### API-042 — incidents (`/api/incidents`)

| Tier | Case | Business assertion |
|---|---|---|
| Happy | Valid CSV upload | Analysis totals returned; export is then available |
| Edge | Header-only CSV / empty upload | Analysis refused with the safe empty/no-rows messages |
| Failure | Non-`.csv` or missing required columns | Format rejected |
| Failure | Export with no prior analyze | No results available |

### FE-019 — frontend utilities

| Function | Happy | Failure |
|---|---|---|
| `validateCandidateInput` | Complete hiring row produces no field errors | Missing name/email/position or invalid URL is rejected |
| `validateNoteContent` | Non-empty note is accepted | Blank / whitespace-only note is rejected |
| `sanitizeApiDetail` / `getUserFacingError` | Known API detail (e.g. invalid credentials) is shown | Unknown detail is replaced with safe status copy |
| `getAuthToken` / `setAuthToken` / `clearAuthToken` | Token round-trips through storage | Cleared storage returns no token |

---

## AI-assisted workflow

An agent read `app/routers/auth.py`, `app/routers/users.py`, and `app/deps/auth.py` and was asked for missed edge cases. Cases added from that review (not from a generic FastAPI template):

1. **Forgot-password enumeration** — unknown emails still return 200 with the same sentence. A suite that only registered a known user would miss this.
2. **Inactive staff** — login uses a different decision than bad passwords (`Inactive user` vs `Invalid credentials`).
3. **Register is `POST /users`**, not `/auth/register`. Generated tests aimed at the syllabus path would be false failures.
4. **Reset tokens are SHA-256 hashes and one-time** via `consume_reset_token`; reuse must fail even with the original raw token.

### Bugs found by generated tests

None in the current auth/supplier/incident handlers. If a later run exposes a product bug, fix it here and keep the failing test.

---

## Results

Recorded 2026-08-31. 36 pytest cases passed; 12 Jest cases passed. No product bugs were found.

### Auth module coverage (target ≥70%)

`python -m pytest --cov=app.routers.auth --cov=app.routers.users --cov=app.deps.auth --cov=app.core.security --cov=app.stores.auth_store --cov=app.routers.profiles --cov-report=term-missing`

| Module | Cover |
|---|---|
| `app/core/security.py` | 100% |
| `app/deps/auth.py` | 100% |
| `app/routers/auth.py` | 97% |
| `app/routers/profiles.py` | 89% |
| `app/routers/users.py` | 80% |
| `app/stores/auth_store.py` | 90% |
| **TOTAL** | **91%** |

Intentional gaps: TinyDB `StorageError` paths, `list_users` GET, and profile-missing 404s. Those are storage/admin edges, not the login/register/token decisions.

### API-042 coverage (target ≥50%)

`python -m pytest tests/test_suppliers.py tests/test_incidents.py --cov=app.routers.suppliers --cov=app.routers.incidents --cov=app.suppliers_store --cov=app.incident_analysis --cov=app.result_store --cov-report=term-missing`

| Module | Cover |
|---|---|
| `app/incident_analysis.py` | 85% |
| `app/result_store.py` | 93% |
| `app/routers/incidents.py` | 86% |
| `app/routers/suppliers.py` | 89% |
| `app/suppliers_store.py` | 70% |
| **TOTAL** | **81%** |

### Jest (FE-019)

`cd uis/backoffice && npm test` — 3 suites, 12 tests passed.

| File | Stmts |
|---|---|
| `lib/auth-storage.ts` | 76.92% |
| `lib/user-facing-error.ts` | 71.42% |
| `lib/validators.ts` | 90% |
| **All collected files** | **79.48%** |
