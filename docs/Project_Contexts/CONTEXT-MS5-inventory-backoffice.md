# HealthCore Digital — Inventory Backoffice (MS5)

**Company:** HealthCore — Outpatient Healthcare Network  
**Unit:** HealthCore Digital  
**Document type:** Assignment CONTEXT (views, auth reuse, error handling, and evaluation)  
**Audience:** External implementing agent  
**Status:** Implemented in `uis/backoffice`. Consumes the live **Inventory ORM dual-database** API.  
**Prerequisite (must ship first):** [`CONTEXT-inventory-orm-dual-database.md`](./CONTEXT-inventory-orm-dual-database.md)  
**Milestone:** MS5

Canonical sequence for this repo:

1. **Inventory ORM dual-database** — TinyDB auth + SQLModel/Supabase inventory (`current_stock`, `user_uuid`, `/inventory/orders/*`).
2. **This file** — four authenticated backoffice views on that API.

Do **not** invent a TinyDB inventory store for the UI. Confirm paths in `http://localhost:8001/docs`.

This CONTEXT is the **single source of truth** for the Milestone 5 inventory section of `uis/backoffice`. Field names, routes, and payloads used by the UI must match the **live inventory API**. Identity, token storage, and route-guard behaviour must match [`auth_master_framework_Context.md`](./auth_master_framework_Context.md). Company framing comes from [`CONTEXT-healthcore-briefing.en.md`](./CONTEXT-healthcore-briefing.en.md). Existing backoffice API patterns come from [`SupplierDirectory_TinyDb_API.md`](./SupplierDirectory_TinyDb_API.md) and [`IncidentFileAnalyzer.md`](./IncidentFileAnalyzer.md).

Do **not** invent a parallel auth design. Do **not** treat root `CONTEXT.md` as the inventory or auth contract.

---

## External agent — start here

You are building an **internal operations tool** for HealthCore Digital staff, not a public page and not a 4Geeks template monorepo. The current `uis/backoffice` + `services/api` layout is the product.

### Before any code change

1. Read [`AGENTS.md`](../../AGENTS.md) (session workflow, protected zones, post-implementation stamp rules).
2. Read [`memory-bank/projectbrief.md`](../../memory-bank/projectbrief.md).
3. Read [`memory-bank/techContext.md`](../../memory-bank/techContext.md).
4. Read [`memory-bank/progress.md`](../../memory-bank/progress.md).
5. Read [`memory-bank/plans/INDEX.md`](../../memory-bank/plans/INDEX.md) and the latest stamp.
6. Read the four files in [`docs/Project_Contexts/`](./):
   - [`CONTEXT-healthcore-briefing.en.md`](./CONTEXT-healthcore-briefing.en.md) — company, departments, HIPAA / UK GDPR lens
   - [`auth_master_framework_Context.md`](./auth_master_framework_Context.md) — JWT Bearer, `localStorage`, client `AuthGuard`, 401 → `/login`
   - [`SupplierDirectory_TinyDb_API.md`](./SupplierDirectory_TinyDb_API.md) — backoffice FastAPI client pattern
   - [`IncidentFileAnalyzer.md`](./IncidentFileAnalyzer.md) — existing protected backoffice module on the same API
7. Confirm the live `/inventory` endpoints in the running API OpenAPI (`http://localhost:8001/docs`). The backend contract is [`CONTEXT-inventory-orm-dual-database.md`](./CONTEXT-inventory-orm-dual-database.md) — that API must exist before this UI.

### How to ship

| Step | Scope |
|------|--------|
| This file | UI contract — four views after the ORM API exists |
| Implementation | `uis/backoffice` inventory pages + `lib/inventory-api.ts` mapping ORM wire fields |

After implementation that ships files: lint/typecheck per `AGENTS.md`, append a new stamp under `memory-bank/plans/` (next sequence after the current INDEX maximum), update `INDEX.md` and `progress.md`. Do **not** rewrite this CONTEXT except with explicit human confirmation.

---

## Business framing

The backend team shipped the inventory API (**SQLModel / Supabase** products and orders; TinyDB JWT auth) — authenticated `/inventory` endpoints, documented, live. Operations staff who manage stock day to day still have no interface. Until one exists in the backoffice, the API is unusable without a REST client.

**From:** Operations Manager  
**To:** Technology Unit (James Osei, HealthCore Digital)

> The backend team shipped the inventory API last sprint. Now I need the interface. My team can't use Postman to log deliveries.

Primary consumers: clinic operations / stock staff (Marcus Reid’s Clinical Operations org). This is an internal tool. Clarity and speed matter more than marketing polish. An operations manager logging a delivery at 7am has zero patience for a broken form or a cryptic error message.

Project owner: **James Osei, CTO**. Compliance lens: Claire Whitfield (HIPAA / UK GDPR). Inventory records are operational stock metadata — **no PHI**. Never log patient names, member IDs, or clinical free text. Sample IDs (`HC-*`, …) stay synthetic.

Patients and the public use **`uis/healthcore`**. That site stays fully public. There is **no** inventory UI, **no** token check, and **no** shared layout on the public website.

---

## Locked contracts (do not invent)

### Identity — [`auth_master_framework_Context.md`](./auth_master_framework_Context.md)

Reuse the AUTH-02 backoffice pattern already in the repo. Do not add cookies, sessions, or Next.js middleware auth.

| Rule | Required behaviour |
|------|--------------------|
| Transport | `Authorization: Bearer <jwt>` on every inventory request |
| Storage | Token in `localStorage` via `uis/backoffice/lib/auth-storage.ts` |
| Fetch helper | `uis/backoffice/lib/authed-fetch.ts` (or a thin inventory wrapper that calls it) |
| Guard | Existing client `AuthGuard` in `uis/backoffice/components/auth/AuthGuard.tsx` |
| No token / invalid token | Redirect to `/login` (current session query is `/login?reason=session`) |
| Protected API **401** | Clear storage and redirect to `/login` |
| Public site | Do not import guards, login pages, or token storage into `uis/healthcore` |
| Hiring client | Do **not** hang inventory calls on `lib/api-client.ts` (4Geeks hiring playground) |

Inventory routes are protected the same way as `/`, `/ops`, `/hiring`, `/incidents`, and `/suppliers`. `AuthGuard` already wraps the backoffice shell; new inventory pages inherit that guard. Do not add a second auth system.

### Isolation

- Public app: `uis/healthcore`. Internal app: `uis/backoffice`.
- Do not share layouts or marketing chrome between them.
- Add inventory links to the **existing** backoffice top nav. Do not create a new shell.

### Error handling

Follow `.cursor/skills/error-handling-frontend/SKILL.md` and the existing `user-facing-error` / `AsyncState` helpers.

- Three-state UI on every inventory fetch: loading, success, error.
- Error states need a readable message plus a retry / home / support exit.
- **400 from the inventory API must show a readable message** extracted from the response body — never raw JSON and never a silent failure.
- Extend `uis/backoffice/lib/user-facing-error.ts` `SAFE_API_DETAILS` with known inventory messages instead of dumping the payload.
- Do not log secrets, tokens, or PHI.

---

## Setup (implementation, later stamp)

1. Work in **`uis/backoffice`**.
2. Create a feature branch from `main`.
3. Add the inventory API base URL to `.env.local` (for example `NEXT_PUBLIC_INVENTORY_API_URL`) pointing at the running backend. Default host/port matches suppliers and incidents: `http://localhost:8001`.
4. Confirm `/inventory` routes in API `/docs`.
5. Measure the frontend baseline with the evaluation script if one is provided for this assignment.

Never commit `.env` or `.env.local`.

---

## What to build

Four views, all authenticated, all talking to the live inventory API.

### API integration layer

- Centralize inventory calls in **one module** (for example `uis/backoffice/lib/inventory-api.ts`). Do not scatter `fetch` across pages.
- Send the JWT from `localStorage` on every request (`authedFetch`).
- Include `NEXT_PUBLIC_INVENTORY_API_URL` in the same base-URL fallback chain used by `authed-fetch.ts` / `auth-api.ts` if the inventory host is the HealthCore FastAPI (`:8001`).
- On **400**, extract a human-readable message and surface it in the form or page.

Use the sample paths and bodies in **Samples** below. Confirm against live OpenAPI. Map ORM wire fields to display fields in `inventory-api.ts` (`current_stock` → `stock`, TinyDB email `created_by` plus `user_uuid`). Do **not** drop evaluated display fields (`name`, `sku`, `stock`, `threshold`, `product_id`, `quantity`, `notes`, `type`, `product_name`, `created_at`, `created_by`).

### 1. Product / stock page

- List all products with **name, SKU, current stock, and threshold**.
- **Color-code stock:** below threshold = warning; at or above threshold = OK. Staff must see low stock at a glance.
- Empty state if there are no products.

Suggested route: `/inventory` (or `/inventory/products`). Keep it inside `uis/backoffice`.

### 2. Inbound order form

- Fields: **product, quantity, and notes**.
- On success: confirmation message, then **redirect to the product page**.
- On API error: show the server message. Do not stay on a silent failure.

Suggested route: `/inventory/inbound`.

### 3. Outbound order form

- Same fields as inbound (**product, quantity, notes**).
- **Must show available stock for the selected product before submit.**
- Update that stock figure when the product selection changes.
- If the API rejects the quantity (for example more than available), show a **clear, readable error** — typically a **400**.

Suggested route: `/inventory/outbound`.

### 4. Order history page (read-only)

- List **all orders**: product name, quantity, type (inbound / outbound), creation date, and who created each one.
- Empty state if there are no orders.
- No edit or delete in this assignment unless the live API and a later stamp require it.

Suggested route: `/inventory/orders`.

---

## Easy-to-miss requirements

1. Outbound form shows **current available stock** for the selected product **before** submit.
2. Any API **400** surfaces a **readable message** — not a raw JSON object and not a silent fail.
3. All four views require login; unauthenticated users go to the login page via the existing `AuthGuard`.
4. This is an **internal** tool. Do not add inventory to `uis/healthcore`.

---

## Samples

These samples lock the **UI display contract**. The live API is the ORM dual-database assignment. Confirm path names against OpenAPI (`http://localhost:8001/docs`). Map wire fields in `inventory-api.ts` — do **not** drop fields required by evaluation. Synthetic clinic-supply data only; no PHI.

Live API paths (ORM CONTEXT):

| Action | Method and path |
|--------|-----------------|
| List products | `GET /inventory/products` |
| Create inbound order | `POST /inventory/orders/inbound` |
| Create outbound order | `POST /inventory/orders/outbound` |
| List orders | `GET /inventory/orders` |

Do **not** call `/inventory/inbound` or `/inventory/outbound` (those were a stand-in TinyDB API). All of the above require `Authorization: Bearer <jwt>`. Missing or invalid token → **401**.

### Product (stock row)

Fields the product page must display: `name`, `sku`, **current stock**, and `threshold`.

The live JSON field is **`current_stock`** (computed inbound − outbound). The backoffice may map that onto a local `stock` property for rendering. Low stock = current stock **below** `threshold`. OK stock = **at or above** `threshold`.

Wire (`GET /inventory/products`):

```json
{
  "id": 1,
  "name": "Nitrile exam gloves (box of 100)",
  "sku": "HC-PPE-GLV-100",
  "threshold": 24,
  "current_stock": 12
}
```

```json
{
  "id": 2,
  "name": "Alcohol prep pads (box of 200)",
  "sku": "HC-CLN-PAD-200",
  "threshold": 30,
  "current_stock": 80
}
```

Product 1 is **low** (12 < 24). Product 2 is **OK** (80 ≥ 30).

### `GET /inventory/products` — 200 with items

```json
[
  {
    "id": 1,
    "name": "Nitrile exam gloves (box of 100)",
    "sku": "HC-PPE-GLV-100",
    "threshold": 24,
    "current_stock": 12
  },
  {
    "id": 2,
    "name": "Alcohol prep pads (box of 200)",
    "sku": "HC-CLN-PAD-200",
    "threshold": 30,
    "current_stock": 80
  }
]
```

### `GET /inventory/products` — 200 empty

```json
[]
```

Render an empty state. Do not crash or show a blank broken table.

### Valid inbound body — `POST /inventory/orders/inbound`

```json
{
  "product_id": 1,
  "quantity": 40,
  "notes": "McKesson delivery — Austin clinic restock"
}
```

### Inbound success — 201

`user_uuid` is stored on the SQLModel row. `created_by` is the TinyDB staff email resolved at read time (not a Postgres column).

```json
{
  "id": 101,
  "product_id": 1,
  "product_name": "Nitrile exam gloves (box of 100)",
  "quantity": 40,
  "notes": "McKesson delivery — Austin clinic restock",
  "created_at": "2026-09-09T12:05:00+00:00",
  "user_uuid": "1",
  "created_by": "ops.manager@healthcore.example"
}
```

UI: show a confirmation message, then redirect to the product page. Stock for SKU `HC-PPE-GLV-100` becomes `52` (12 + 40). The client may add `type: "inbound"` for the history model.

### Valid outbound body — `POST /inventory/orders/outbound`

Before submit, the form must already show available stock for the selected product (here: **12** for product `1`).

```json
{
  "product_id": 1,
  "quantity": 6,
  "notes": "Manchester clinic weekly consumption"
}
```

### Outbound success — 201

```json
{
  "id": 102,
  "product_id": 1,
  "product_name": "Nitrile exam gloves (box of 100)",
  "quantity": 6,
  "notes": "Manchester clinic weekly consumption",
  "created_at": "2026-09-09T12:20:00+00:00",
  "user_uuid": "1",
  "created_by": "ops.manager@healthcore.example"
}
```

Stock for SKU `HC-PPE-GLV-100` becomes `6` (12 − 6).

### Outbound rejected — 400 insufficient stock

Request (quantity greater than available 12):

```json
{
  "product_id": 1,
  "quantity": 20,
  "notes": "Attempted over-issue"
}
```

Response:

```json
{
  "detail": "Insufficient stock. Available: 12. Requested: 20."
}
```

UI must show a **readable** message such as `Insufficient stock. Available: 12. Requested: 20.` — never the raw JSON object and never a silent failure. Add that `detail` string to `SAFE_API_DETAILS` (or an inventory allowlist) so `user-facing-error` can pass it through.

### `GET /inventory/orders` — 200 with items

Each row must show product name, type (`inbound` / `outbound`), quantity, date, and who created it.

```json
[
  {
    "id": 101,
    "product_id": 1,
    "product_name": "Nitrile exam gloves (box of 100)",
    "quantity": 40,
    "type": "inbound",
    "notes": "McKesson delivery — Austin clinic restock",
    "created_at": "2026-09-09T12:05:00+00:00",
    "user_uuid": "1",
    "created_by": "ops.manager@healthcore.example"
  },
  {
    "id": 102,
    "product_id": 1,
    "product_name": "Nitrile exam gloves (box of 100)",
    "quantity": 6,
    "type": "outbound",
    "notes": "Manchester clinic weekly consumption",
    "created_at": "2026-09-09T12:20:00+00:00",
    "user_uuid": "1",
    "created_by": "ops.manager@healthcore.example"
  }
]
```

### `GET /inventory/orders` — 200 empty

```json
[]
```

Render an empty state. Do not crash.

### Unauthenticated request — 401

Any `/inventory/*` call without a valid Bearer token:

```json
{
  "detail": "Could not validate credentials"
}
```

Backoffice: clear storage and redirect to `/login`.

---

## What We Will Evaluate

Official assignment rubric. A generic UI that misses any item below will not be accepted.

- A centralized API integration module — not fetch calls scattered across components.
- The product page shows current stock with visual distinction for low stock.
- The inbound order form submits to the API and displays a confirmation or error message — no silent failures.
- The outbound order form shows available stock before the user enters a quantity. This is a specific requirement — do not skip it.
- If the API rejects an outbound order (insufficient stock), a readable error message appears in the UI.
- The order history page shows all orders with product name, type (inbound/outbound), quantity, date, and who created it.
- Empty arrays from the API result in an empty state, not a broken page.
- All four pages require authentication. Unauthenticated access redirects to `/login`.

### HealthCore cross-cutting (same repo)

- [ ] Inventory requests send `Authorization: Bearer <token>` via `authedFetch`
- [ ] Protected inventory API **401** clears the session and redirects to `/login`
- [ ] `uis/healthcore` has no inventory page and no auth check
- [ ] Loading / success / error states on list and form requests
- [ ] **400** shows an extracted readable message, never raw JSON
- [ ] One inventory API module; no use of `lib/api-client.ts`
- [ ] Existing `/suppliers`, `/incidents`, `/hiring`, `/ops`, and auth flows still work
- [ ] Backoffice nav can reach the inventory section
- [ ] No shared layout with the public site
- [ ] PHI-safe copy and commit messages

---

## Explicit non-goals

- Do not re-implement AUTH-01 / AUTH-02 / AUTH-03.
- Do not add inventory auth to `uis/healthcore`.
- Do not share layouts between public and backoffice.
- Do not rewrite [`auth_master_framework_Context.md`](./auth_master_framework_Context.md), [`SupplierDirectory_TinyDb_API.md`](./SupplierDirectory_TinyDb_API.md), or [`IncidentFileAnalyzer.md`](./IncidentFileAnalyzer.md).
- Do not modify root [`CONTEXT.md`](../../CONTEXT.md), [`CONTEXT_temp.md`](../../CONTEXT_temp.md), [`memory-bank/projectbrief.md`](../../memory-bank/projectbrief.md), or [`memory-bank/techContext.md`](../../memory-bank/techContext.md).
- Do not rewrite prior `memory-bank/plans/HC-*.md` stamps or milestone evals.
- Do not invent product/order field names that contradict the live inventory OpenAPI (`current_stock`, `user_uuid`, `/inventory/orders/*`).
- Do not commit `.env`, `.env.local`, API keys, or real PHI.
- Do not restore TinyDB `inventory_store.py` as the live inventory API.

---

## Agent instructions

1. Read [`CONTEXT-inventory-orm-dual-database.md`](./CONTEXT-inventory-orm-dual-database.md) first, then this CONTEXT and the four sibling files in `docs/Project_Contexts/` before writing inventory UI.
2. Confirm live `/inventory` paths in FastAPI `/docs`. Use ORM paths (`/inventory/orders/inbound`, `/inventory/orders/outbound`). Display `current_stock` as stock; show TinyDB email as creator via `created_by` while keeping `user_uuid` on the wire.
3. Build only in `uis/backoffice`. Reuse `AuthGuard`, `auth-storage`, `authed-fetch`, and `user-facing-error`.
4. Centralize inventory HTTP in one module. Send Bearer tokens. Surface 400 messages as readable text.
5. Outbound form must display available stock for the selected product before submit.
6. Leave `uis/healthcore` unchanged.
7. After shipping UI files, append a new plan stamp; do not rewrite prior stamps.
8. PHI-safe commit messages: no patient names, member IDs, clinical free text, passwords, or tokens.

---

## How to run

Start the API first, then the backoffice. Inventory pages call `http://localhost:8001`. Sign in on `/login` before opening inventory — unauthenticated visits redirect to login.

Never commit `.env`, `.env.local`, or generated TinyDB files (`services/api/data/auth.json`, `suppliers.json`). Live inventory is SQLModel/Supabase (`DATABASE_URL`), not `inventory.json`.

### 1. Seed and start the API (port `8001`)

Put secrets **only** in `services/api/.env` (JWT keys plus `DATABASE_URL` Transaction pooler URI). Do not put key values in markdown, scripts, PowerShell history notes, or git. Do not commit or push `.env`.

Windows PowerShell:

```powershell
cd services/api
Copy-Item .env.example .env
# Edit .env and set JWT_SECRET_KEY there. Do not paste the value into other files.
python -m pip install -r requirements.txt
python seed.py
python -m uvicorn app.main:app --reload --port 8001
```

bash / macOS / Linux:

```bash
cd services/api
cp .env.example .env
# Edit .env and set JWT_SECRET_KEY there. Do not paste the value into other files.
python -m pip install -r requirements.txt
python seed.py
python -m uvicorn app.main:app --reload --port 8001
```

Seed console (fresh databases):

```text
Inserted 15 supplier(s).
Inserted 2 inventory product(s).
```

Re-running the seeder does not duplicate products (match on `sku`) or suppliers (match on name + country).

Checks:

- Health: http://localhost:8001/health
- OpenAPI (confirm `/inventory` routes): http://localhost:8001/docs

| Method | Path |
|--------|------|
| `GET` | `/inventory/products` |
| `POST` | `/inventory/orders/inbound` |
| `POST` | `/inventory/orders/outbound` |
| `GET` | `/inventory/orders` |

All four require `Authorization: Bearer <jwt>`. No token → **401**.

### 2. Start the backoffice (port `3001`)

```powershell
cd uis/backoffice
npm install
npm run dev
```

Open:

| Page | URL |
|------|-----|
| Stock | http://localhost:3001/inventory |
| Inbound delivery | http://localhost:3001/inventory/inbound |
| Outbound exit | http://localhost:3001/inventory/outbound |
| Order history | http://localhost:3001/inventory/orders |
| Login | http://localhost:3001/login |

Register a staff account on `/register` (or log in if one already exists), then use Inventory in the top nav.

Optional API base override (same host/port as suppliers and incidents):

```powershell
$env:NEXT_PUBLIC_INVENTORY_API_URL="http://localhost:8001"
npm run dev
```

### 3. Tests

```powershell
# API (from repo root)
python -m pytest

# Backoffice
cd uis/backoffice
npm run lint
npx tsc --noEmit
npm test
```

See [`TESTING.md`](../../TESTING.md) for the inventory case table.

### 4. Public site (must stay unauthenticated)

```powershell
cd uis/healthcore
npm run dev
```

http://localhost:3000 — no inventory UI and no login redirect.
