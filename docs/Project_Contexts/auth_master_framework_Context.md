# HealthCore Digital — Authentication Master Framework

**Company:** HealthCore — Outpatient Healthcare Network  
**Unit:** HealthCore Digital  
**Document type:** Assignment CONTEXT (identity contract, routes, UI surfaces, evaluation, and agent instructions)  
**Audience:** External implementing agent  
**Status:** CONTEXT only — **do not treat this file as implemented auth code**

This CONTEXT is the **single source of truth** for combining three 4Geeks AUTH tickets into one HealthCore identity system. Field names, route prefixes, HTTP status codes, storage rules, and public-vs-internal boundaries used by the API and backoffice must match this document exactly.

Syllabus sources (requirements only — ignore their “company monorepo / fork” framing):

- [AUTH-01 — API](https://github.com/4GeeksAcademy/ai-engineering-syllabus/blob/main/content/projects/ai-eng-user-authentication-api/README.md)
- [AUTH-02 — Frontend flows](https://github.com/4GeeksAcademy/ai-engineering-syllabus/blob/main/content/projects/ai-eng-user-authentication-flows/README.md)
- [AUTH-03 — Password restore](https://github.com/4GeeksAcademy/ai-engineering-syllabus/blob/main/content/projects/ai-eng-user-authentication-restore/README.md)

---

## External agent — start here

You are implementing staff authentication for **HealthCore Digital**, not scaffolding a 4Geeks template monorepo. The current `uis/` + `services/api` layout is the product. Do not restructure the repository to match syllabus monorepo language.

### Before any code change

1. Read [`AGENTS.md`](../../AGENTS.md) (session workflow, protected zones, post-implementation stamp rules).
2. Read [`memory-bank/projectbrief.md`](../../memory-bank/projectbrief.md).
3. Read [`memory-bank/techContext.md`](../../memory-bank/techContext.md).
4. Read [`memory-bank/progress.md`](../../memory-bank/progress.md).
5. Read [`memory-bank/plans/INDEX.md`](../../memory-bank/plans/INDEX.md) and the latest stamp.
6. Treat **this file** as the AUTH assignment CONTEXT. Do not invent a parallel auth design.

### How to ship

Implement **three sequential, individually graded tasks**. Do not collapse them into one commit or one PR.

| Task | Branch | Scope |
|------|--------|--------|
| AUTH-01 | `feature/auth-api` | FastAPI identity + JWT + protect existing sensitive routes |
| AUTH-02 | `feature/auth-frontend` | Backoffice login/register/profile + client route guard + Bearer on API calls |
| AUTH-03 | `feature/password-reset` | Forgot/reset/change-password API + UI + Resend (or SendGrid) |

Do not start AUTH-02 until AUTH-01 is demonstrable in FastAPI `/docs`.  
Do not start AUTH-03 until login, register, profile, logout, and 401-redirect work end-to-end.

After **each** task that ships files: lint/typecheck per `AGENTS.md`, append a new stamp under `memory-bank/plans/` (next sequence after the current INDEX maximum), update `INDEX.md` and `progress.md`. Do **not** rewrite prior stamps. Do **not** rewrite this CONTEXT except with explicit human confirmation.

This CONTEXT document itself is **docs only**. Auth code does not exist until AUTH-01+ land.

---

## Business framing

HealthCore Digital staff (James Osei’s unit, Diane Foster’s people team, Tom Callahan’s billing ops, Marcus Reid’s clinical ops) use **`uis/backoffice`** for internal tools: ops metrics, hiring, incident analysis, supplier directory.

Today those APIs are **open**. Anyone who knows a URL can read or change supplier records and upload incident CSVs. Before the next operational phase, **no route that modifies or exposes sensitive operational data may be reachable without a valid session.**

Patients and the public use **`uis/healthcore`**. That site stays fully public. There is **no** patient login, **no** public auth API, and **no** token check on the public website.

Project owner: **James Osei, CTO**. Compliance lens: Claire Whitfield (HIPAA / UK GDPR) — credentials and contact data are staff identity, not clinical notes, but still treat them as sensitive. Never log passwords, reset tokens, or real PHI. Sample IDs (`HC-*`, `CLM-*`, …) stay synthetic.

---

## Locked identity contract (all three tasks)

These rules override any conflicting note in [`docs/ARCHITECTURE_PROPOSAL.md`](../ARCHITECTURE_PROPOSAL.md) (that document locked cookie/session auth). The AUTH assignments require **stateless JWT only**.

1. **Transport:** `Authorization: Bearer <jwt>`. No session cookies. No Next.js middleware auth unless a cookie also exists (it must not).
2. **User vs Profile:** credentials on `User`; display name and contact on `Profile` (one-to-one via `user_id`). Never store `name`, `phone`, or `address` on `User`.
3. **Persistence:** `User`, `Profile`, and password-reset token rows live in **TinyDB only**. Do not create user/profile tables in PostgreSQL, SQLModel, or Supabase now or later. Other modules may store the TinyDB user `id` as `user_uuid` if needed.
4. **Route prefixes (exact):** `/auth`, `/users`, `/profiles`. Do **not** nest them under `/api/v1`.
5. **Passwords:** hash with `libpass[bcrypt]`. Import remains `from passlib.hash import bcrypt`. Never store or compare plaintext. Install `libpass[bcrypt]` — not unmaintained `passlib`.
6. **JWT library:** `python-jose[cryptography]`. Access-token claims must include the TinyDB user `id` (`sub`) and `exp`.
7. **Roles:** `admin` | `manager` | `user` only (Enum or field validator). `POST /users` defaults `role` to `user`. Full per-route RBAC is **not** required.
8. **Public vs internal:** all auth UI lives in `uis/backoffice`. `uis/healthcore` must not import auth guards, login pages, or token storage.
9. **CORS:** keep API CORS allowlist on backoffice origins only (`http://localhost:3001` and `http://127.0.0.1:3001`). Do not open CORS to the public site for auth.
10. **Package install path:** HealthCore API uses `services/api/requirements.txt` + pip. Add AUTH packages there. Do **not** migrate the API to `uv` as part of this work (syllabus mentions `uv add`; HealthCore runbooks use pip).

---

## Current codebase (pre-AUTH)

Implementing agents must extend these surfaces, not replace them.

**API** — [`services/api`](../../services/api)

- [`app/main.py`](../../services/api/app/main.py) — FastAPI app, CORS for `:3001`, routers for incidents + suppliers, public `GET /health`.
- [`app/routers/suppliers.py`](../../services/api/app/routers/suppliers.py) — prefix `/suppliers` (create, list, get, patch rate, patch status, delete). Unauthenticated today.
- [`app/routers/incidents.py`](../../services/api/app/routers/incidents.py) — prefix `/api/incidents` (`POST /analyze`, `GET /results/export`). Unauthenticated today.
- TinyDB suppliers file: `services/api/data/suppliers.json` — **do not merge auth tables into this file**.
- [`requirements.txt`](../../services/api/requirements.txt) — FastAPI, uvicorn, python-multipart, tinydb. No JWT/hasher yet.

**Backoffice** — [`uis/backoffice`](../../uis/backoffice)

- Pages: `/`, `/ops`, `/hiring`, `/hiring/candidates/[id]`, `/incidents`, `/suppliers`. No login.
- [`app/layout.tsx`](../../uis/backoffice/app/layout.tsx) — internal nav, no auth guard.
- [`lib/suppliers-api.ts`](../../uis/backoffice/lib/suppliers-api.ts) and incident fetch in [`components/incidents/IncidentAnalyzerPanel.tsx`](../../uis/backoffice/components/incidents/IncidentAnalyzerPanel.tsx) call `http://localhost:8001` with **no** `Authorization` header.
- [`lib/api-client.ts`](../../uis/backoffice/lib/api-client.ts) talks to the 4Geeks hiring playground by default. **Do not** hang HealthCore JWT auth on that client unless hiring is switched onto this FastAPI (it is not).

**Public site** — [`uis/healthcore`](../../uis/healthcore)

- Fully public. Do not add auth.

**Do not change** supplier/incident domain fields, seed suppliers, or prior CONTEXTs:

- [`docs/Project_Contexts/SupplierDirectory_TinyDb_API.md`](./SupplierDirectory_TinyDb_API.md)
- [`docs/Project_Contexts/IncidentFileAnalyzer.md`](./IncidentFileAnalyzer.md)

---

## Data model contract

### TinyDB file

- Path: **`services/api/data/auth.json`** (separate from `suppliers.json`).
- Tables (TinyDB collections): `users`, `profiles`, `reset_tokens` (`reset_tokens` required for AUTH-03; may be created empty in AUTH-01).
- Gitignore the generated JSON in the AUTH-01 implementation stamp (same pattern as suppliers).

### `User` (collection `users`)

| Field | Type | Notes |
|-------|------|--------|
| `id` | integer | TinyDB document id; JWT `sub` is this id as a string |
| `email` | string | Unique, case-insensitive match on login |
| `hashed_password` | string | bcrypt hash only |
| `is_active` | boolean | Default `true` on register |
| `role` | string | `admin` \| `manager` \| `user` |
| `created_at` | string | ISO 8601, server-generated |

Never persist `name`, `phone`, or `address` on `User`.  
Never return `hashed_password` in any JSON response.

### `Profile` (collection `profiles`)

| Field | Type | Notes |
|-------|------|--------|
| `id` | integer | TinyDB document id |
| `user_id` | integer | Unique; matches `User.id` |
| `name` | string | Display name; empty string allowed if omitted at register |
| `phone` | string | Optional contact |
| `address` | string | Optional contact |

### `reset_tokens` (AUTH-03)

Do **not** rely on JWT `exp` alone. A used reset token must fail with **400**.

Locked approach: store a **SHA-256 hash** of a random URL-safe token (never store the plaintext token).

| Field | Type | Notes |
|-------|------|--------|
| `id` | integer | TinyDB document id |
| `user_id` | integer | Owner |
| `token_hash` | string | SHA-256 hex of the plaintext token |
| `expires_at` | string | ISO 8601; 15–60 minutes from issue (use `RESET_TOKEN_EXPIRE_MINUTES`, default **30**) |
| `used_at` | string or null | Set on successful reset; null means unused |

### Access JWT (AUTH-01)

- Algorithm: `HS256`.
- Claims: `sub` = user id string; `exp`; optional `role`.
- Expiry: `ACCESS_TOKEN_EXPIRE_MINUTES` (default **30**).
- Secret: `JWT_SECRET_KEY` from environment — never hardcode.

### Environment variables

Document names in `services/api/.env.example` (AUTH-01 for JWT; AUTH-03 adds email). Never commit `.env` or live keys.

| Variable | Task | Purpose |
|----------|------|---------|
| `JWT_SECRET_KEY` | AUTH-01 | HMAC signing secret |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | AUTH-01 | Access token lifetime (default 30) |
| `RESET_TOKEN_EXPIRE_MINUTES` | AUTH-03 | Reset token lifetime (default 30) |
| `BACKOFFICE_PUBLIC_URL` | AUTH-03 | Origin for reset links, e.g. `http://localhost:3001` |
| `RESEND_API_KEY` | AUTH-03 | If Resend is chosen (recommended) |
| `RESEND_FROM_EMAIL` | AUTH-03 | From address allowed by the provider |
| `SENDGRID_API_KEY` | AUTH-03 | Only if SendGrid is chosen instead of Resend |

Recommend **Resend** (no custom domain required for student/dev sending). Choose one provider, not both.

---

## Suggested module layout (new files only)

Do not rewrite incident/supplier domain modules. Add:

```
services/api/app/
  core/config.py          # pydantic-settings from env
  core/security.py        # hash/verify password, create/decode access JWT
  deps/auth.py            # get_current_user (OAuth2PasswordBearer)
  models/users.py
  models/profiles.py
  stores/auth_store.py    # TinyDB users + profiles (+ reset_tokens in AUTH-03)
  routers/auth.py
  routers/users.py
  routers/profiles.py
```

Backoffice (AUTH-02+):

```
uis/backoffice/
  lib/auth-storage.ts
  lib/auth-api.ts
  lib/authed-fetch.ts
  components/auth/AuthGuard.tsx
  app/(public)/login/page.tsx
  app/(public)/register/page.tsx
  app/(app)/account/profile/page.tsx
  # AUTH-03:
  app/(public)/forgot-password/page.tsx
  app/(public)/reset-password/page.tsx
  app/(app)/account/change-password/page.tsx
```

Use a **client** AuthGuard (or equivalent hook) around `(app)`. Next.js middleware must **not** be used for localStorage JWT checks.

---

## AUTH-01 — Securing the API

**Intent:** security layer. After this task, unauthenticated supplier/incident calls return **401**. Temporary backoffice breakage is expected until AUTH-02.

### Packages

Add to `services/api/requirements.txt`:

- `python-jose[cryptography]`
- `libpass[bcrypt]`
- `pydantic-settings` (if not already present)

### Service layer

Functions: create user, get by id, get by email, update user, delete user (delete must also remove the linked profile).

### HTTP API

#### `POST /users` — public (register)

- Body: `email`, `password`, optional `name`, `phone`, `address`.
- Hash password before insert. Default `role=user`, `is_active=true`.
- Create linked `Profile` in the same operation (empty strings if optional fields omitted).
- Duplicate email → **409**.
- Response: public user + profile fields as needed, **never** `hashed_password`. Status **201**.

#### Protected user routes (`Depends(get_current_user)`)

- `GET /users` — list (no password hashes).
- `GET /users/{id}` — single user.
- `PUT /users/{id}` — update credential fields such as `email`. Caller must be the same user **or** `admin`. `role` may change only when the caller is `admin`. Other-user access without admin → **403**.
- `DELETE /users/{id}` — delete user + profile. Same ownership/admin rule; otherwise **403**.

#### Profiles

- `GET /profiles/me` — authenticated user’s profile.
- `PUT /profiles/me` — update `name`, `phone`, `address`. Owner only.

#### Auth

- `POST /auth/login` — JSON `{ "email", "password" }`. Invalid credentials → **401**. Success:

  ```json
  { "access_token": "<jwt>", "token_type": "bearer" }
  ```

- `GET /auth/me` — email, role, linked profile (`name`, `phone`, `address`).

#### `get_current_user`

- Use `OAuth2PasswordBearer` (token URL `/auth/login`).
- Extract Bearer token, decode/validate JWT, load user from TinyDB.
- Missing, malformed, expired, or unknown user → **401**.
- Inactive user → **401**.

### Route protection (existing API)

Apply `get_current_user` to **all eight** existing sensitive routes (exceeds the syllabus minimum of five). Keep `GET /health` public.

Must require a valid token:

1. `POST /suppliers`
2. `GET /suppliers`
3. `GET /suppliers/{id}`
4. `PATCH /suppliers/{id}/rate`
5. `PATCH /suppliers/{id}/status`
6. `DELETE /suppliers/{id}`
7. `POST /api/incidents/analyze`
8. `GET /api/incidents/results/export`

Unauthenticated or bad token → **401**. Do not change supplier/incident payloads, validation, or TinyDB path.

### AUTH-01 out of scope

- Any Next.js pages or guards.
- Password forgot/reset/change.
- Per-role checks on supplier/incident routes.
- Cookie/session auth.
- User seeder (not required; registration creates users).

### AUTH-01 verification

Manual via `http://localhost:8001/docs`:

1. `POST /users` → `POST /auth/login` → Authorize with the token → call a supplier or incident route successfully.
2. Same protected route without token → **401**.
3. Expired or malformed token → **401**.
4. User A updating User B’s profile/credentials (non-admin) → **403**.

PR description must list the eight protected routes and how they were verified.

---

## AUTH-02 — Frontend authentication flows

**Intent:** close the loop. Token is stored, sent, and required for backoffice views. Public website stays unaffected.

### Views (backoffice only)

| Path | Auth | Behavior |
|------|------|----------|
| `/login` | public | Email + password → `POST /auth/login` → store token in `localStorage` → redirect to `/`. Show a clear error on failure. |
| `/register` | public | `POST /users` (optional profile fields) then `POST /auth/login` with the same credentials → store token → redirect. Field-level errors. |
| `/account/profile` | protected | `GET /auth/me` shows email + profile; edit via `PUT /profiles/me`. |
| `/`, `/ops`, `/hiring`, `/hiring/candidates/[id]`, `/incidents`, `/suppliers` | protected | Client guard: no/invalid token → `/login`. |

Logout control (nav or account): remove token, redirect to `/login`.

### Token lifecycle

1. Store token in `localStorage` after login/register.
2. Every protected HealthCore API call (suppliers + incidents **and** `/auth/me`, `/profiles/me`, `/users` as used) must send `Authorization: Bearer <token>`.
3. Logout: clear storage, redirect `/login`.
4. Any protected API **401**: clear storage, redirect `/login`.

### Guard implementation

Client layout guard or hook reading `localStorage`. **Do not** use Next.js middleware for this check.

Do **not** add any of this to `uis/healthcore`.

### AUTH-02 out of scope

- Forgot/reset/change password.
- Email provider.
- Role-based UI.
- Changes to public site copy, layout, or routing.

### AUTH-02 verification

- Login and register persist a token and reach a protected view.
- Visiting `/suppliers` (etc.) logged out redirects to `/login`.
- Public site (`uis/healthcore`, typically `:3000`) has no token check and no redirect to login.
- Profile displays User email + Profile contact fields and updates via `PUT /profiles/me`.
- Logout and API 401 both clear the session and land on `/login`.
- Supplier list/create/patch and incident upload/export work again **with** the token.

PR description must list protected views and confirm the public website was not affected.

---

## AUTH-03 — Password recovery and change

**Intent:** forgot-password (unauthenticated + email) and change-password (authenticated).

### Backend

- `POST /auth/forgot-password` `{ "email" }`
  - Always **200**, same body whether or not the email exists (anti-enumeration).
  - If the user exists: create unused reset-token row, email a link:
    `{BACKOFFICE_PUBLIC_URL}/reset-password?token={plaintext_token}`
  - Email must be readable on mobile.
- `POST /auth/reset-password` `{ "token", "new_password" }`
  - Validate hash match, `expires_at` in the future, `used_at` is null.
  - Success: hash new password, update user, set `used_at`. Token cannot be reused.
  - Invalid, expired, or already-used → **400**.
- `POST /auth/change-password` `{ "current_password", "new_password" }`
  - Requires valid access JWT.
  - Wrong current password → **400**.
  - Hash and store the new password on success.

### Frontend (backoffice)

- `/forgot-password` — always show: “If that address is registered, you'll receive a link shortly.” Disable the form after submit.
- `/reset-password` — read `token` from the query string; confirm new password; on success redirect to `/login` with a success message; on failure show a clear error and a link to `/forgot-password`.
- `/account/change-password` — current + new + confirmation; client-side match check before `POST /auth/change-password`.
- `/login` — visible “Forgot your password?” link to `/forgot-password`.

### AUTH-03 out of scope (optional extras)

HTML email template, rate limiting, audit log — allowed but not evaluated.

### AUTH-03 verification

- Registered email receives a real message containing the reset link.
- Unknown email still returns **200** and the UI still shows the generic confirmation.
- Expired or reused token → **400** and the reset page shows an error + link back to forgot.
- Change-password rejects wrong current password with **400**.
- No API keys in the repo.

PR description must name the email service, the env var(s) required, and confirm an end-to-end test.

---

## HTTP status cheat sheet

| Situation | Status |
|-----------|--------|
| Missing / invalid / expired access token | 401 |
| Valid token, not owner (and not admin where required) | 403 |
| Duplicate email on register | 409 |
| Validation errors (bad role, empty password, etc.) | 422 |
| Invalid/expired/used reset token | 400 |
| Wrong current password on change | 400 |
| Forgot-password always (found or not) | 200 |
| User/supplier/incident missing | 404 (existing behavior for suppliers/incidents) |

---

## Evaluation checklists (copy into each PR)

### AUTH-01

- [ ] User CRUD reachable via the API
- [ ] Each User has a linked Profile; name/phone/address on Profile only
- [ ] Role accepts only `admin` / `manager` / `user`; register defaults `user`
- [ ] Passwords hashed; never stored or compared in plaintext
- [ ] Login returns a signed JWT
- [ ] `get_current_user` identifies the caller
- [ ] Protected routes return 401 without a valid token
- [ ] Cross-user profile/credential access returns 403
- [ ] JWT secret and expiry from environment
- [ ] Routes under `/auth`, `/users`, `/profiles`
- [ ] All eight existing supplier + incident routes require a token
- [ ] User/Profile remain in TinyDB only
- [ ] Protected routes still succeed with a valid token (no supplier/incident regressions)

### AUTH-02

- [ ] Login and registration store the token
- [ ] Protected views redirect to `/login` without a token
- [ ] Public website has no auth check
- [ ] Profile shows email + Profile fields; updates via `PUT /profiles/me`
- [ ] Logout clears token and redirects
- [ ] API 401 clears session and redirects to `/login`

### AUTH-03

- [ ] Forgot-password sends a real email when the address exists
- [ ] Forgot-password returns 200 for unknown addresses
- [ ] Reset token expires and cannot be reused
- [ ] Reset-password updates the hash and invalidates the token
- [ ] Reset-password returns 400 for expired or used tokens
- [ ] Forgot UI always shows the generic confirmation
- [ ] Reset UI reads query `token`, redirects to login on success
- [ ] Invalid reset shows error + link to forgot-password
- [ ] Login has “Forgot your password?”
- [ ] Change-password validates confirmation, calls API, shows feedback
- [ ] Change-password rejects wrong current password with 400
- [ ] No hardcoded API keys

---

## Explicit non-goals

- Do not restructure the repo into a 4Geeks “company monorepo.”
- Do not implement cookie/session auth from `docs/ARCHITECTURE_PROPOSAL.md`.
- Do not add User/Profile SQL tables.
- Do not share layouts between `uis/healthcore` and `uis/backoffice`.
- Do not implement full role RBAC on every supplier/incident route (optional extra only).
- Do not modify root [`CONTEXT.md`](../../CONTEXT.md), [`CONTEXT_temp.md`](../../CONTEXT_temp.md), [`memory-bank/projectbrief.md`](../../memory-bank/projectbrief.md), [`memory-bank/techContext.md`](../../memory-bank/techContext.md).
- Do not rewrite prior `memory-bank/plans/HC-*.md` stamps or milestone evals.
- Do not change supplier field names (`monthly_rate`, `USA`/`UK`, `USD`/`GBP`) or incident analyzer domain rules.
- Do not commit `.env`, API keys, or real PHI.

---

## Agent instructions

1. Read this CONTEXT before writing auth code. Match field names, prefixes, status codes, and TinyDB path exactly.
2. Implement AUTH-01, then AUTH-02, then AUTH-03 as separate branches/PRs.
3. Keep `GET /health` public. Protect all eight supplier + incident routes in AUTH-01.
4. Store User/Profile/reset tokens in `services/api/data/auth.json` only — never in `suppliers.json`.
5. Use JWT Bearer + `localStorage` in backoffice. Never cookies. Never Next middleware for this token.
6. Leave `uis/healthcore` unchanged.
7. Add Python deps to `requirements.txt`; do not migrate the API to uv for this work.
8. Prefer Resend for AUTH-03; document env vars in `.env.example` only.
9. Invalidate reset tokens with TinyDB `used_at` (plus expiry). JWT `exp` alone is not enough.
10. After each shipping task, append a new plan stamp; do not rewrite this CONTEXT or prior stamps.
11. PHI-safe commit messages: no patient names, member IDs, or clinical free text; no passwords or tokens in git.

---

## Run (after implementation)

```bash
# API
cd services/api
python -m pip install -r requirements.txt
python seed.py
python -m uvicorn app.main:app --reload --port 8001
# http://localhost:8001/docs  http://localhost:8001/health

# Backoffice (auth UI)
cd uis/backoffice
npm run dev
# http://localhost:3001

# Public site (must remain unauthenticated)
cd uis/healthcore
npm run dev
# http://localhost:3000
```

Copy `services/api/.env.example` to `.env` locally. Never commit `.env`.
