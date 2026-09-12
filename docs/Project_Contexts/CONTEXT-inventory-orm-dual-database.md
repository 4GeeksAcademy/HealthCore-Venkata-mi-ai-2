# Backend: Inventory Management with ORM & Dual Database

**Company:** HealthCore — Outpatient Healthcare Network  
**Unit:** HealthCore Digital  
**Document type:** Assignment CONTEXT (SQLModel + TinyDB auth + Supabase inventory)  
**Audience:** Implementing agent  
**Status:** Implemented in `services/api` (PLAN-034+). This file remains the assignment contract.  
**Scope:** Extend the existing FastAPI app under `services/`. Do not create a new service.  
**Next assignment:** [`CONTEXT-MS5-inventory-backoffice.md`](./CONTEXT-MS5-inventory-backoffice.md) — four backoffice views **after** this API exists.

Canonical sequence:

1. **This file** — TinyDB auth + SQLModel inventory (`current_stock`, `user_uuid`, `/inventory/orders/*`).
2. **MS5 inventory backoffice** — consume that live API; do not invent a TinyDB inventory store.

You are building on **this HealthCore monorepo** — not a new repository. Syllabus placeholders (`CONTEXT.md`, `CONTEXT-company.md`) resolve to the files listed in [Company CONTEXT in this HealthCore monorepo](#company-context-in-this-healthcore-monorepo).

---

## Your challenge

You've already built — or are expected to have — the API and the authentication layer under `services/`. If FastAPI + TinyDB auth (`User` / `get_current_user`) is not in the monorepo yet, complete the auth projects (or scaffold that layer) before starting this milestone — **you extend that service; you do not create a new one from scratch.**

Now the operations team has submitted an RFP to the technology unit: the company needs a centralised inventory management system, and it must be live before the next operational review.

Your tech lead has translated that RFP into an architectural decision that shapes everything you build here: **authentication stays in TinyDB** (fast, local, document-based lookups), and **all business data** — products, inbound orders, and outbound orders — **moves to Supabase** (a hosted PostgreSQL database). Your FastAPI application will maintain **two simultaneous database connections** and must use each one deliberately: every request reaches the right store.

This is not just a persistence exercise. The operations team embedded a non-negotiable constraint in the brief:

> Stock levels cannot be modified directly. The only way to change inventory is by registering an order — either an inbound order that adds stock, or an outbound order that removes it. Every order must be traceable to the user who created it.

Your job is to enforce that rule at the **API and model** level, using an ORM to translate Python classes into relational tables in Supabase. All inventory endpoints must be grouped under the `/inventory` router prefix.

### What is an ORM — and why does it matter here?

An ORM (Object-Relational Mapper) is a translation layer: a Python class becomes a table, an instance becomes a row, and an attribute becomes a column. It does not replace knowing SQL — understanding what the ORM generates under the hood is what lets you use it correctly and debug it when something breaks. In this milestone you will use **SQLModel**, which combines SQLAlchemy's ORM engine with Pydantic's type system. **Do not use raw SQLAlchemy directly.**

One pattern you must be aware of before writing any query: the **N+1 problem**. If you load a list of orders and then access each order's product data inside a loop, you generate one additional query per element — degrading performance silently. Structure your queries to load related data **up front**, not on access.

---

## Brief from your tech lead

From: Tech Lead  
Subject: Milestone — dual database architecture + inventory ORM

The PRD is ready. Here is what the system must do:

1. The FastAPI app connects to **two databases simultaneously**: TinyDB (existing, for users and auth) and Supabase (new, for inventory and orders).
2. Products and stock quantities live in Supabase. Stock must **not** be a directly editable column — it is always derived from the order history.
3. **Inbound** orders increase stock; **outbound** orders decrease it. Both are stored in Supabase and reference the **user UUID from TinyDB** — **no user table is replicated in Supabase**.
4. ORM models use **SQLModel**. Pydantic schemas for request and response are in a **separate file** from ORM models — **never return a raw ORM object** from an endpoint.
5. All inventory routes must be registered under the `/inventory` prefix using a dedicated `APIRouter`.
6. Check your **CONTEXT.md** — entity names, field constraints, and business rules are **company-specific**.

**Acceptance criteria:** all endpoints functional under `/inventory`; FK relationships enforced at database level; no direct stock mutation; both DB connections active and correctly used.

---

## How to Start the Project

This milestone extends the FastAPI service in your monorepo. You will not create a new service — you add the inventory layer to it.

1. Open this existing repository. You will not create a new service.
2. Navigate to `services/` — your FastAPI application with TinyDB auth should already live here. If it does not, stop and scaffold / finish auth first. (This repo: `services/api`.)
3. Install new dependencies:

   ```bash
   uv add sqlmodel psycopg2-binary
   ```

   This HealthCore API has historically been installed with `services/api/requirements.txt` + pip. Still add `sqlmodel` and `psycopg2-binary`. Do not skip them.

4. Add your Supabase connection string to `.env`. Leave the existing TinyDB auth config untouched — do not change it.
5. Read your **company CONTEXT** before defining any model — entity names and field constraints are specified there.

### Supabase connection settings

In the Supabase dashboard (**Connect → Direct**):

| Setting | Value |
|---------|--------|
| Connection method | **Transaction pooler** |
| Type | **URI** |
| Copy into `.env` as | `DATABASE_URL` |

Use **your** project's Transaction pooler URI (pooler host, port **6543**). Never hardcode credentials. Never commit `.env`.

Example `.env` shape (placeholder only — use your own project ref and password):

```env
# Existing TinyDB / JWT auth — do not change these keys
JWT_SECRET_KEY=replace-me
ACCESS_TOKEN_EXPIRE_MINUTES=30
RESET_TOKEN_EXPIRE_MINUTES=30
BACKOFFICE_PUBLIC_URL=http://localhost:3001

# New — Supabase Transaction pooler URI
DATABASE_URL=postgresql://postgres.PROJECT_REF:YOUR_PASSWORD@aws-1-us-east-2.pooler.supabase.com:6543/postgres
```

List `DATABASE_URL` in `.env.example` as well (no real password). HealthCore does not commit `.env` or `.env.example` to git; keep secrets in the local ignored files.

---

## What You Need to Do

### Database configuration

- Add the Supabase PostgreSQL connection string to `.env`. Never hardcode credentials.
- In **`database.py`** (or equivalent), initialise **both** database connections: existing TinyDB client and a new SQLModel engine pointing to Supabase.
- Create a **`get_db()`** dependency that yields a SQLModel session per request via `Depends()`. **No global session variable.**

### ORM models — `models.py`

Syllabus illustrations (do **not** copy these names unless the company CONTEXT uses them): `Ingredient` / `SKU` / `Asset` / `MedicalSupply`; inbound `IngredientEntry` / `StockEntry`; outbound `IngredientExit` / `StockExit`; FK `ingredient_id` / `sku_id`.

HealthCore names are locked in [Company-specific entities](#company-specific-entities).

- Define the **product-equivalent** entity using SQLModel, `table=True`, with at minimum `id`, `name`, `sku`, and any company-specific fields from CONTEXT.
- Define the **inbound-equivalent** model with: `id`; a **foreign key** to the product-equivalent entity (name the FK as in CONTEXT); `quantity`; `created_at`; **`user_uuid` string** — references the TinyDB user; **no FK to a user table, no user table replication**; plus any other CONTEXT-required fields.
- Define the **outbound-equivalent** model with the same FK pattern, plus `quantity`, `created_at`, `user_uuid`, and CONTEXT-required fields.
- Call **`SQLModel.metadata.create_all(engine)`** on application startup to initialise the schema in Supabase.

### Pydantic schemas — `schemas.py`

- Request and response schemas for the product-, inbound-, and outbound-equivalent entities as standalone Pydantic models — **separate from the ORM models**. Use the names from CONTEXT.
- The product-equivalent **response** schema must include a **`current_stock`** field (**computed, not stored**).
- ORM models and Pydantic schemas must live in **separate files**. They are different classes, even if some fields overlap.

### Inventory router — `routers/inventory.py`

Create a dedicated `APIRouter` with `prefix="/inventory"` and register it in the main FastAPI app.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/inventory/products` | List all products with computed `current_stock` |
| `POST` | `/inventory/products` | Create a product (requires auth) |
| `GET` | `/inventory/products/{id}` | Get a single product with its current stock |
| `POST` | `/inventory/orders/inbound` | Register an inbound order (requires auth) |
| `POST` | `/inventory/orders/outbound` | Register an outbound order (requires auth) |
| `GET` | `/inventory/orders` | List all orders with product data and `user_uuid` |

**Auth on GET:** order and product **writes** always require auth. Whether **GET** routes are public or authenticated follows CONTEXT (e.g. **HealthCore requires authenticated access on inventory routes**).

### Business rules

- **`current_stock`** is always computed as **`SUM(inbound quantities) − SUM(outbound quantities)`** for each product-equivalent entity, scoped by any partition key CONTEXT defines (e.g. warehouse). It is **never stored as a column that can be set directly**.
- A product-equivalent entity starts with **zero stock** at creation and can only accumulate stock through inbound records.
- Every order creation endpoint requires authentication. The authenticated user's UUID (from TinyDB) must be stored in the order's **`user_uuid`** field.
- An outbound record that would result in **negative stock** (within the CONTEXT-defined scope) must be rejected **before the record is persisted**, returning **HTTP 400** with a descriptive error message.

**IMPORTANT:** Entity names, field names, and domain-specific values must match CONTEXT. A generic implementation that ignores the contract will not be accepted.

### Seed data

Seed the inventory tables with the minimum records listed in CONTEXT (product-equivalents, inbound, outbound) before the demo. **Seeded stock must match net inbound − outbound.**

---

## What We Will Evaluate

- Two database connections are demonstrably present and used correctly: **TinyDB** for auth and user lookups; **Supabase (SQLModel)** for all inventory writes.
- All inventory endpoints are grouped under `/inventory` via a dedicated `APIRouter`.
- SQLModel ORM models correctly declare **FK relationships**: inbound/outbound models reference the **product-equivalent entity named in CONTEXT** (not a generic `Product` unless CONTEXT says so).
- **`current_stock` is computed from orders** — no endpoint allows direct modification of a stock field on the product-equivalent entity.
- Stock calculation respects CONTEXT scoping (global vs per-partition / per-warehouse when required).
- An outbound record that exceeds available stock (within that scope) is rejected with **HTTP 400 before any write occurs**.
- Every order stores the **`user_uuid`** of the authenticated creator (sourced from TinyDB).
- ORM models (`models.py`) and Pydantic schemas (`schemas.py`) are in **separate files** and are structurally different — no endpoint returns a raw SQLModel object.
- The SQLModel session is injected per request via **`Depends()`** — **no global session** exists in the codebase.
- All connection parameters live in **`.env`** and are listed in **`.env.example`**.
- Entity names and field names match the student's CONTEXT specification.
- Seed data from CONTEXT is present; **`GET /inventory/products` reflects net stock from those seeds**.

---

## Company CONTEXT in this HealthCore monorepo

| Assignment pointer | File in this repo |
|--------------------|-------------------|
| Company briefing | [`CONTEXT-healthcore-briefing.en.md`](./CONTEXT-healthcore-briefing.en.md) |
| TinyDB `User` / `get_current_user` / no user table in Supabase | [`auth_master_framework_Context.md`](./auth_master_framework_Context.md) |
| Inventory extra fields, GET auth, clinic-supply seed rows, **UI after this API** | [`CONTEXT-MS5-inventory-backoffice.md`](./CONTEXT-MS5-inventory-backoffice.md) |

Root [`CONTEXT.md`](../../CONTEXT.md) is Milestone 2 (claims, no-shows, CME). It does **not** define inventory entities. Do not rewrite it.

Existing app path: `services/api`. JWT + TinyDB auth already exists. Inventory persistence is **SQLModel** (`app/inventory/models.py`) via `DATABASE_URL`. TinyDB `inventory_store.py` was removed.

**Auth:** HealthCore requires **Bearer JWT on every inventory route**, including GET. Missing or invalid token → **401**.

**Stock scope:** MS5 inventory CONTEXT defines **no warehouse / partition key**. Compute `current_stock` **globally per product**.

**Path note:** this milestone uses `/inventory/orders/inbound` and `/inventory/orders/outbound`. The MS5 backoffice must call **these** paths (not `/inventory/inbound`).

**Creator field:** persist **`user_uuid`** on the SQLModel row (TinyDB user `id` as a string; JWT `sub`). Do not replicate users in Supabase. HTTP responses may also include **`created_by`** as the TinyDB staff email resolved at read time so the backoffice history page is readable. That email is **not** a Postgres column and must not replace `user_uuid` on the ORM.

---

## Company-specific entities

HealthCore clinic-supply inventory (not a generic `Ingredient` bakery model). ORM class names must match this CONTEXT:

| Role | HealthCore SQLModel name | Table FK / keys |
|------|--------------------------|-----------------|
| Product-equivalent | `MedicalSupply` | Postgres table `medical_supply` — `id`, `name`, `sku` (unique), `threshold` |
| Inbound-equivalent | `InboundOrder` | Postgres table `inbound_order` — `id`, `product_id` → `medical_supply.id`, `product_name`, `sku`, `quantity`, `notes`, `created_at`, `user_uuid` |
| Outbound-equivalent | `OutboundOrder` | Postgres table `outbound_order` — same columns as inbound |

Open **Table Editor** on `inbound_order` / `outbound_order` (not mashed `inboundorder`). Those rows copy `product_name` and `sku` so you can read the supply without joining. Combined history is view `inventory_order` (`type` = `inbound` or `outbound`). Ignore leftover EduTrack tables (`students`, `courses`, `enrollments`) if they appear in the same project. `product_name` / `sku` on orders are labels only — **stock is still computed**, never a writable column.

`MedicalSupply` is the HealthCore product-equivalent (clinic medical supplies). Do not name the ORM class generic `Product` unless you also keep these HealthCore fields and this CONTEXT's table mapping.

Pydantic schema names (separate file): e.g. `MedicalSupplyCreate`, `MedicalSupplyResponse` (must include computed `current_stock`), `InboundOrderCreate`, `InboundOrderResponse`, `OutboundOrderCreate`, `OutboundOrderResponse`. List endpoints may return a combined order response that includes product data + `user_uuid`.

`threshold` is company-specific (low-stock warning for the backoffice). It is **not** stock and must not be used as a writable stock column.

`user_uuid` example: TinyDB user `id` `1` is stored as `"1"` (string). It must exist in TinyDB. There is **no** Postgres FK to users.

---

## Examples

Synthetic clinic-supply data only. No PHI. Paths and field names below are the contract for this milestone.

### Formula

```text
current_stock(product) = SUM(inbound.quantity) − SUM(outbound.quantity)
```

New `MedicalSupply` → `current_stock == 0` until an inbound row exists.

### Minimum seed (net stock must match)

| SKU | Name | threshold | Inbound qty | Outbound qty | `current_stock` |
|-----|------|-----------|-------------|--------------|-----------------|
| `HC-PPE-GLV-100` | Nitrile exam gloves (box of 100) | 24 | 40 | 28 | **12** (low: 12 < 24) |
| `HC-CLN-PAD-200` | Alcohol prep pads (box of 200) | 30 | 80 | 0 | **80** (OK: 80 ≥ 30) |

`GET /inventory/products` after seed must show `current_stock` **12** and **80** from those orders — not from writing a stock column.

### `POST /inventory/products` — create (auth required)

Stock starts at zero. Do not send `current_stock` or `stock`.

Request:

```json
{
  "name": "Nitrile exam gloves (box of 100)",
  "sku": "HC-PPE-GLV-100",
  "threshold": 24
}
```

Response `201`:

```json
{
  "id": 1,
  "name": "Nitrile exam gloves (box of 100)",
  "sku": "HC-PPE-GLV-100",
  "threshold": 24,
  "current_stock": 0
}
```

### `GET /inventory/products` — 200 after seed

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

Empty list: `[]`.

### `GET /inventory/products/{id}` — 200

```json
{
  "id": 1,
  "name": "Nitrile exam gloves (box of 100)",
  "sku": "HC-PPE-GLV-100",
  "threshold": 24,
  "current_stock": 12
}
```

Unknown id → **404**.

### `POST /inventory/orders/inbound` — 201 (auth required)

Request:

```json
{
  "product_id": 1,
  "quantity": 40,
  "notes": "McKesson delivery — Austin clinic restock"
}
```

Response:

```json
{
  "id": 101,
  "product_id": 1,
  "product_name": "Nitrile exam gloves (box of 100)",
  "quantity": 40,
  "notes": "McKesson delivery — Austin clinic restock",
  "created_at": "2026-09-11T12:05:00+00:00",
  "user_uuid": "1",
  "created_by": "ops.manager@healthcore.example"
}
```

`user_uuid` is the authenticated TinyDB user id (string), not a client-supplied field. `created_by` is the matching TinyDB email for UI/reporting only.

### `POST /inventory/orders/outbound` — 201 (auth required)

Request (available `current_stock` for product `1` is **12**):

```json
{
  "product_id": 1,
  "quantity": 6,
  "notes": "Manchester clinic weekly consumption"
}
```

Response:

```json
{
  "id": 102,
  "product_id": 1,
  "product_name": "Nitrile exam gloves (box of 100)",
  "quantity": 6,
  "notes": "Manchester clinic weekly consumption",
  "created_at": "2026-09-11T12:20:00+00:00",
  "user_uuid": "1",
  "created_by": "ops.manager@healthcore.example"
}
```

After this call, gloves `current_stock` = 12 − 6 = **6**.

### Outbound rejected — HTTP 400 (before persist)

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

No outbound row is written.

### `GET /inventory/orders` — 200

Load product data **with** the orders (no N+1). Include `user_uuid`. Include `created_by` as TinyDB email for the backoffice.

```json
[
  {
    "id": 101,
    "product_id": 1,
    "product_name": "Nitrile exam gloves (box of 100)",
    "quantity": 40,
    "type": "inbound",
    "notes": "McKesson delivery — Austin clinic restock",
    "created_at": "2026-09-11T12:05:00+00:00",
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
    "created_at": "2026-09-11T12:20:00+00:00",
    "user_uuid": "1",
    "created_by": "ops.manager@healthcore.example"
  }
]
```

Empty list: `[]`.

### Unauthenticated — 401

Any HealthCore `/inventory/*` call without a valid Bearer token:

```json
{
  "detail": "Could not validate credentials"
}
```

### File layout (under `services/api`)

```text
app/
  database.py                 # TinyDB auth ping + SQLModel engine + get_db()
  inventory/models.py         # MedicalSupply, InboundOrder, OutboundOrder (table=True)
  inventory/schemas.py        # Pydantic request/response only — not ORM classes
  routers/inventory.py        # APIRouter(prefix="/inventory")
```

`app/models/` is an existing Pydantic package (users, suppliers). Inventory ORM lives in `app/inventory/models.py` so it does not collide with that package. Evaluation still has separate `models.py` and `schemas.py` files.

---

## How to run (step by step)

Do **not** commit `.env`. Use your own Supabase Transaction pooler URI.

### 1. Python packages

From PowerShell, in the API directory:

```powershell
cd services/api
python -m pip install -r requirements.txt -r requirements-dev.txt
```

(The assignment also lists `uv add sqlmodel psycopg2-binary`. This repo installs those from `requirements.txt`.)

### 2. Environment

```powershell
cd services/api
Copy-Item .env.example .env -ErrorAction SilentlyContinue
# Edit .env in an editor. Keep existing JWT keys. Add:
# DATABASE_URL=postgresql://postgres.PROJECT_REF:YOUR_PASSWORD@aws-1-us-east-2.pooler.supabase.com:6543/postgres
```

Minimum keys:

- `JWT_SECRET_KEY` (already required for auth)
- `DATABASE_URL` (Supabase Transaction pooler URI, port **6543**)
- `ACCESS_TOKEN_EXPIRE_MINUTES` (default 30)
- `BACKOFFICE_PUBLIC_URL` (default `http://localhost:3001`)

List `DATABASE_URL=` in local `.env.example` with an empty or placeholder password. Do not git-add `.env` or `.env.example`.

### 3. Create tables and seed

```powershell
cd services/api
python seed.py
```

Expected console (fresh inventory tables):

```text
Inserted 15 supplier(s).
Inserted 2 inventory product(s) (stock from inbound − outbound).
```

Re-runs skip existing SKUs. Seeded `current_stock` is **12** (gloves) and **80** (pads).

### 4. Start the API

```powershell
cd services/api
python -m uvicorn app.main:app --reload --port 8001
```

Checks:

- http://localhost:8001/health → `{"status":"ok"}`
- http://localhost:8001/docs → OpenAPI (`/inventory/products`, `/inventory/orders/inbound`, …)

### 5. Call inventory (JWT required)

Register + login (new terminal, still from `services/api` or any folder):

```powershell
# Register (skip if the user already exists)
Invoke-RestMethod -Method Post -Uri http://localhost:8001/users -ContentType "application/json" -Body '{"email":"ops.manager@healthcore.example","password":"StaffPass9","name":"Ops Manager","phone":"","address":""}'

# Login — copy access_token from the response
$login = Invoke-RestMethod -Method Post -Uri http://localhost:8001/auth/login -ContentType "application/json" -Body '{"email":"ops.manager@healthcore.example","password":"StaffPass9"}'
$token = $login.access_token
$auth = @{ Authorization = "Bearer $token" }

# List products with computed current_stock
Invoke-RestMethod -Headers $auth -Uri http://localhost:8001/inventory/products

# Unauthenticated must be 401
try { Invoke-WebRequest -Uri http://localhost:8001/inventory/products } catch { $_.Exception.Response.StatusCode.value__ }
```

bash equivalent:

```bash
cd services/api
python -m pip install -r requirements.txt -r requirements-dev.txt
python seed.py
python -m uvicorn app.main:app --reload --port 8001
```

```bash
TOKEN=$(curl -s -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"ops.manager@healthcore.example","password":"StaffPass9"}' \
  | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8001/inventory/products
curl -s http://localhost:8001/inventory/products   # 401
```

### 6. Tests (isolated SQLite — does not use live Supabase)

```powershell
cd services/api
python -m pytest tests/test_inventory.py
```

From the repository root (full API suite):

```powershell
python -m pytest
```

Backoffice mapping tests:

```powershell
cd uis/backoffice
npm test
```

### 7. Backoffice (optional)

```powershell
cd uis/backoffice
npm run dev
```

Open http://localhost:3001/inventory after login. The client maps `current_stock` → displayed stock. Order history shows TinyDB `created_by` email; `user_uuid` stays on the JSON.

---

## Explicit non-goals

- Do not create a new FastAPI service.
- Do not put users/profiles in Supabase.
- Do not add inventory or auth to `uis/healthcore`.
- Do not rewrite root `CONTEXT.md` or `CONTEXT-MS5-inventory-backoffice.md` unless a human explicitly asks.
- Do not expose a PATCH/PUT that sets stock or `current_stock`.
- Do not use a global SQLModel session.
- Do not commit `.env` or real `DATABASE_URL` passwords.
