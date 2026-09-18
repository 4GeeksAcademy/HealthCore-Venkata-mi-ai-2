# CONTEXT: Backend Serialization Audit (HealthCore Digital)

**Audience:** AI coding agents implementing this assignment in the HealthCore Digital monorepo.  
**Parent:** [CONTEXT.md](../../CONTEXT.md) (canonical product).  
**Related:** [CONTEXT-MS4](./CONTEXT-MS4.md), [CONTEXT-MS5-container](./CONTEXT-MS5-container.md), [serialization-audit.md](../serialization-audit.md).  
**Last updated:** 2026-09-18

---

## 1. Goal

Audit every FastAPI route in `services/api` and confirm responses are **explicit Pydantic models**, not raw ORM objects or untyped `dict`s. After the audit, close gaps so OpenAPI (`/docs`) matches what clients receive.

This is a **serialization contract** assignment, not a new product surface. Do not add public/backoffice pages, Docker changes, or shared layouts.

---

## 2. Why this exists at HealthCore

Monday-morning staff tools (Diane, Tom, Marcus) call this API. A raw TinyDB row or SQLModel instance can leak `hashed_password`, extra store keys, or fields that were never intended for the browser. Explicit `response_model` / `response_class` is how we keep identity, inventory, and ops JSON **predictable and PHI-safe**.

---

## 3. Current HealthCore API map (do not invent routes)

| Area | Prefix / paths | Persistence | Notes |
|------|----------------|-------------|--------|
| Health | `GET /health` | none | Liveness for Compose / CI |
| Auth | `/auth/login`, `/auth/password-reset`, `/auth/password-reset/confirm`, `/auth/me` | TinyDB `auth.json` | JWT staff session |
| Users | `POST /users` (**this is register**), `GET/PUT/DELETE /users`, `GET /users/{id}` | TinyDB | There is **no** `/auth/register` |
| Profiles | `/profiles/me` | TinyDB | Authenticated profile |
| Inventory | `/inventory/products`, `/inventory/orders`, inbound/outbound | SQLModel + SQLite/Postgres | `created_by` is staff **email** (backoffice history) |
| Suppliers | `/api/suppliers` | TinyDB `suppliers.json` | CRUD + `DeleteAck` |
| Incidents | `/api/incidents/analyze`, `/api/incidents/results/export` | in-memory result store | Analyze → JSON; export → **CSV file**, not JSON |

Routers live in `services/api/app/routers/`. Schemas live in `app/models/` and `app/inventory/schemas.py`. Auth users are **TinyDB documents**, not SQLAlchemy/SQLModel ORM rows. Inventory products/orders **are** SQLModel.

---

## 4. Assignment requirements (must all be true)

1. **Every endpoint** that returns JSON uses `response_model=<Pydantic model>` (or an equivalent `response_class` for non-JSON).
2. **Input and output schemas are separate.** Create/update request bodies must not be reused as response bodies.
3. **Auth responses** (login, register, password reset, failed login) do **not** echo password. Unauthenticated auth flows do **not** echo email. `GET /auth/me` **may** return email (session identity).
4. **Register** is `POST /users` in this repo. The nested `user` object must **not** include `email`.
5. **User list / get / put** JSON should **limit email** (omit it). Email stays on `GET /auth/me` and on inventory `created_by` (ops attribution, not an auth echo).
6. **CSV export** is a documented exception: `FileResponse` / `text/csv`, **no** JSON `response_model`.
7. Write `docs/serialization-audit.md` (endpoint, method, current return, target schema, status).
8. Verify with FastAPI `/docs` (or the same OpenAPI schemas via TestClient) for **at least three** endpoints: login, register (`POST /users`), and one other (health or incidents analyze).
9. Unit tests that asserted `user.email` on **register** must be updated. Inventory tests that compared `created_by` to `registered_user["user"]["email"]` must use the known staff email constant instead.
10. Do **not** drop inventory `created_by` — backoffice order history displays it.

---

## 5. Known gaps to close (Phase 2)

These are the project-specific holes vs a generic “add response_model everywhere” prompt:

| Gap | Why it fails the rubric |
|-----|-------------------------|
| `GET /health` has no `response_model` | Raw dict `{"status": "ok"}` |
| `POST /api/incidents/analyze` has no `response_model` | Returns `dict` from `AnalysisResult` |
| `DELETE /users/{user_id}` returns a raw `{"ok": True}` dict | Needs a Pydantic ack model |
| `POST /users` `UserResponse` includes `email` | Register must not return email |
| `GET /users` and `GET/PUT /users/{id}` include `email` | Limit email on user list/detail |
| `docs/serialization-audit.md` missing | Required deliverable |
| `test_register.py` asserts `user["email"]` | Will fail after email is stripped |
| `test_inventory.py` uses `registered_user["user"]["email"]` | Register body will no longer have email |
| CSV export | Must stay file download; document exception |

Already in good shape (do not regress): login `AccessTokenResponse`, password-reset `MessageResponse`, `/auth/me` `AuthMeResponse` (email allowed), inventory Create vs Response split, suppliers CRUD + `DeleteAck`, profiles `ProfileResponse`.

---

## 6. Implementation rules

- FastAPI only in `services/api`. Do not share layouts between `uis/healthcore` and `uis/backoffice`.
- No committed `.env` / secrets. Synthetic emails only (`qa.staff@healthcore.example`).
- Do not rewrite `CONTEXT.md` or prior plan stamps.
- After shipping files: append a plan stamp + `INDEX.md` + `progress.md`.
- **Do not save an evaluation markdown file** until a human confirms a Pass. Show the evaluation in chat first.

---

## 7. Evaluation (show in chat; save only after confirmation)

Score each item Pass / Fail. Overall **Pass** only if every item is Pass.

1. All JSON endpoints use explicit `response_model` (CSV export excepted and documented).
2. No raw ORM / TinyDB document returned as the HTTP body.
3. Input schemas ≠ output schemas.
4. Unauthenticated auth responses do not include email or password; register `user` has no email; `/auth/me` may include email.
5. `docs/serialization-audit.md` exists and lists every route with original vs target status.
6. At least three endpoints verified against OpenAPI (`/docs` or TestClient schema).
7. pytest suite green after schema + test updates.

---

## 8. Out of scope

Docker/Compose, Lighthouse, public marketing pages, hiring UI, changing `/ops` path, dropping `created_by`, adding `/auth/register`.
