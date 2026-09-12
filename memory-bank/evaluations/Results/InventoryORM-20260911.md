# Inventory ORM Dual Database Evaluation

**Date:** 2026-09-11  
**Rubric:** [`CONTEXT-inventory-orm-dual-database.md`](../../../docs/Project_Contexts/CONTEXT-inventory-orm-dual-database.md) “What We Will Evaluate”  
**Code as of:** [HC-MS5-PLAN-034](../../plans/HC-MS5-PLAN-034-20260911-inventory-orm-dual-db-impl.md), [PLAN-035](../../plans/HC-MS5-PLAN-035-20260911-inventory-table-editor-labels.md), [PLAN-036](../../plans/HC-MS5-PLAN-036-20260911-backoffice-login-suspense-order-keys.md), [PLAN-037](../../plans/HC-MS5-PLAN-037-20260911-orm-first-backoffice-alignment.md)  
**Overall: PASS (12/12)**

This is a **task-level** evaluation for the dual-store inventory API. It does **not** rewrite [MS5_Project_Eval.md](../MS5_Project_Eval.md) (backoffice UI 8/8).

---

## Objectives

Keep TinyDB for staff auth. Persist clinic medical supplies and orders in SQLModel (Supabase in demo, isolated SQLite in pytest). Stock is computed as inbound − outbound. Every order stores TinyDB `user_uuid`. All inventory routes sit under `/inventory` and require JWT.

## Delivered

| Item | Path |
|------|------|
| Dual connections | `app/database.py` (`get_db()`, `init_dual_stores()`) |
| ORM | `app/inventory/models.py` — `MedicalSupply`, `InboundOrder`, `OutboundOrder` |
| Pydantic schemas | `app/inventory/schemas.py` |
| Router | `app/routers/inventory.py` prefix `/inventory` |
| Seed | `seed.py` + `app/inventory/service.py` |
| Pytest | `tests/test_inventory.py` (10 cases) |
| Backoffice client map | `uis/backoffice/lib/inventory-api.ts` (`current_stock` → `stock`, new order paths) |

## Verification

- `python -m pytest` from repo root: **46 passed** (was 43 TinyDB inventory; + inventory ORM cases).
- `python -m pytest tests/test_inventory.py` from `services/api`: **10 passed**.
- `uis/backoffice` `npm run lint` / `npx tsc --noEmit`: pass (coverage report warning only).
- `uis/backoffice` `npm test`: **15 passed**.
- Pytest uses isolated SQLite (`DATABASE_URL=sqlite://`) and isolated TinyDB. It does not write live `data/` files or require a live Supabase password.

Live Supabase demo needs `DATABASE_URL` in local `.env` (not committed). Tables are created with `SQLModel.metadata.create_all(engine)` on API startup.

## Live re-run (2026-09-11 late evening)

Re-ran after PLAN-035 (readable Postgres names / product labels) and PLAN-036 (login Suspense + order-history keys). API on `:8001`, backoffice on `:3001`.

| Check | Result |
|-------|--------|
| Pytest (repo root) | **46 passed** |
| Inventory pytest | **10 passed** |
| Jest (`uis/backoffice`) | **15 passed** |
| Backoffice lint / `tsc --noEmit` | pass (coverage warning only) |
| `GET /health` | **200** `{"status":"ok"}` |
| `GET /inventory/products` no token | **401** `Not authenticated` |
| `GET /inventory/products` with JWT | **200** — gloves `current_stock` **12**, pads **80**; no `stock` field |
| `GET /inventory/products/{id}` gloves | **200** `current_stock` 12 |
| `GET /inventory/products/99999` | **404** Product not found. |
| `POST /inventory/orders/outbound` qty 9999 | **400** `Insufficient stock. Available: 12. Requested: 9999.` |
| Gloves stock after rejected outbound | still **12** (no write) |
| `GET /inventory/orders` | **200**, 3 rows, `user_uuid` + `product_name`, not `created_by`; types inbound + outbound |
| `http://localhost:3001/inventory` | **200** |
| `http://localhost:3001/login` | **200** |
| `http://localhost:3001/inventory/orders` | **200** |

**Overall after this re-run: still PASS (12/12).** Dual store confirmed: login is TinyDB JWT; product stock came from SQLModel/Supabase order history (`inbound_order` / `outbound_order`).

## Live re-run (2026-09-11 ORM-first alignment)

After PLAN-037: HTTP order payloads still include `user_uuid` (SQLModel). `created_by` is TinyDB email for the MS5 history page — not stored in Postgres. Pytest **46**, inventory **10**. Jest **18**. Scorecard **12/12 Pass**.

## Live re-run (2026-09-11 evening)

API: `python -m uvicorn app.main:app --reload --port 8001` after `python seed.py` (2 inventory products). Backoffice already listening on `:3001`.

| Check | Result |
|-------|--------|
| Pytest (repo root) | **45 passed** |
| Jest (`uis/backoffice`) | **15 passed** |
| `GET /health` | **200** `{"status":"ok"}` |
| `GET /inventory/products` no token | **401** |
| `GET /inventory/products` with JWT | **200** — gloves `current_stock` **12**, pads **80**; no `stock` field |
| `GET /inventory/products/{id}` gloves | **200** `current_stock` 12 |
| `GET /inventory/products/99999` | **404** Product not found |
| `POST /inventory/orders/outbound` qty 9999 | **400** `Insufficient stock. Available: 12. Requested: 9999.` |
| `GET /inventory/orders` | **200**, rows include `user_uuid` and `product_name`, not `created_by` |
| `http://localhost:3001/inventory` | **200** (existing backoffice server) |

**Overall after live re-run: still PASS (12/12).** Dual store is confirmed: login is TinyDB JWT; product stock came from seeded SQLModel/Supabase order history.

## Scorecard

| # | Criterion | Result | Evidence |
|---|-----------|--------|----------|
| 1 | TinyDB for auth; SQLModel for inventory writes | **Pass** | `get_current_user` → TinyDB; inventory handlers use `Depends(get_db)` SQLModel `Session` |
| 2 | All inventory endpoints under `/inventory` | **Pass** | `APIRouter(prefix="/inventory")` in `routers/inventory.py`, included from `main.py` |
| 3 | FK to CONTEXT entity, not generic `Product` | **Pass** | `MedicalSupply`; `product_id` FK `medical_supply.id` on inbound/outbound |
| 4 | `current_stock` computed; no stock mutation endpoint | **Pass** | No stock column; `POST /products` returns `current_stock: 0`; no PATCH stock |
| 5 | Stock scope global (no warehouse in CONTEXT) | **Pass** | `SUM(inbound) − SUM(outbound)` per `product_id` |
| 6 | Outbound over available stock → 400 before write | **Pass** | `Insufficient stock. Available: 12. Requested: 20.`; history has no over-issue row |
| 7 | Orders store TinyDB `user_uuid` | **Pass** | `user_uuid == str(user["id"])` on SQLModel row; HTTP may also include TinyDB `created_by` email (not a Postgres column) |
| 8 | Separate ORM vs Pydantic files; no raw ORM return | **Pass** | `inventory/models.py` vs `inventory/schemas.py`; responses are Pydantic models |
| 9 | Session per request via `Depends`; no global Session | **Pass** | `get_db()` yields/closes a `Session`; engine cache only |
| 10 | Connection params in `.env` | **Pass** | `Settings.database_url`; documented in CONTEXT; `.env` not committed |
| 11 | Both connections init at startup | **Pass** | `lifespan` → `init_dual_stores()` (TinyDB touch + `create_all`) |
| 12 | Seed net stock on `GET /inventory/products` | **Pass** | Gloves **12**, pads **80** from inbound 40−28 and inbound 80 |

## Gaps / deferred

- Missing Bearer header returns FastAPI’s `Not authenticated` (401). A bad/expired token returns `Could not validate credentials`. Both are 401.
- `POST /inventory/products` and `GET /inventory/products/{id}` remain API-only (no create-product form in MS5 UI).
- `.env.example` is gitignored in this repo; `DATABASE_URL` is documented in the CONTEXT runbook and required by `Settings`.

## Agent instructions

1. Treat this Results file as the ORM dual-database assignment eval (12/12 Pass). Do not rewrite the original MS5 UI 8/8 body; append re-runs only.
2. Keep inventory writes on SQLModel/`get_db()`. Do not restore TinyDB `inventory_store.py`.
3. Do not add a writable stock column or a users table in Supabase. HTTP `created_by` email is TinyDB lookup only.
4. Isolate pytest with `DATABASE_URL=sqlite://`; never point tests at live Supabase.
5. Do not commit `.env`.
