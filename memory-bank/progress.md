# HealthCore — Progress

**Last updated:** 2026-09-16  
**Latest stamped plan:** [HC-MS5-PLAN-047](./plans/HC-MS5-PLAN-047-20260916-ops-label-operations.md) (`implemented`, MS5, implementation)  
**Prior completed stamp:** [HC-MS5-PLAN-046](./plans/HC-MS5-PLAN-046-20260916-ops-dashboard-perf.md) (`implemented`, MS5, implementation)  
**Latest milestone eval:** [MS5_Project_Eval](./evaluations/MS5_Project_Eval.md) (`complete` — official rubric **8/8 Pass**, re-run 2026-09-11 ORM-first)

## Rubric mapping (MS4)

- `uis/website` → **`uis/healthcore`**
- Milestone 2 in backoffice → **`src/utils`** TypeScript (denial / no-show / CME) visible on **`/ops`** and home panel  
  (hiring tracker is separate — not Milestone 2)

## Current state

| Area | Status |
|------|--------|
| Milestone 2 `src/utils/` | Present + **integrated into backoffice UI** |
| Public site `uis/healthcore` | Done (rubric “website”) |
| MS5 containerization (`#infra-40`) | **Implemented** (PLAN-041) — Compose verified on host; browse runbook in CONTEXT (PLAN-042) |
| Backoffice | Done — welcome, `/ops`, `/hiring`, `/incidents`, `/suppliers`, **`/inventory`** |
| MS5 inventory backoffice | **Implemented** (PLAN-030, aligned PLAN-037) — consumes ORM API; eval → [MS5_Project_Eval](./evaluations/MS5_Project_Eval.md) (**8/8 Pass**) |
| Inventory ORM + dual DB | **Implemented first** (PLAN-034–037) — SQLModel/Supabase inventory, TinyDB auth; eval → [Results/InventoryORM-20260911.md](./evaluations/Results/InventoryORM-20260911.md) (**12/12 Pass**) |
| MS4 evaluation | **complete PASS** |
| FastAPI architecture proposal | In review (PLAN-006–009) |
| Incident File Analyzer | **Domain fixed** (PLAN-012) |
| Supplier Directory | **Domain fixed** (PLAN-016) — `monthly_rate`, `USA`/`UK` + `USD`/`GBP`, 15 seeds (McKesson, Epic); structure from PLAN-015 kept; eval → [Results/SupplierDirectory-20260819.md](./evaluations/Results/SupplierDirectory-20260819.md) |
| Auth (AUTH-01/02/03) | **Implemented** (PLAN-019, PLAN-020, PLAN-021) — [auth_master_framework_Context.md](../docs/Project_Contexts/auth_master_framework_Context.md). API JWT, protected routes, backoffice auth flows, and password recovery/change are in place. |
| Error handling skills | **Docs** (PLAN-023) — Cursor skills under `.cursor/skills/error-handling-*` |
| Error handling implementation | **Implemented** (PLAN-024–026) — eval → [Results/ErrorHandling-20260828.md](./evaluations/Results/ErrorHandling-20260828.md) |
| Unit testing | **Implemented** (PLAN-027) — [`TESTING.md`](../TESTING.md). Eval → [Results/UnitTesting-20260831.md](./evaluations/Results/UnitTesting-20260831.md) (**8/8 Pass**) |

## Today’s update (2026-09-16)

**Operations label (PLAN-047):** User-facing “Milestone 2 ops” copy is now **Operations** (nav, `/ops` heading, home CTAs). URL remains `/ops`.

**Ops dashboard performance (PLAN-046):** `/ops` uses a server internal layout (nav not a client shell). Headline denial / no-show / CME numbers stay visible; long lists are in `<details>`. Re-run Lighthouse on http://localhost:3001/ops after a hard refresh.

**Backoffice home JS (PLAN-045):** Welcome page server-renders a slim Monday ops snapshot (same `src/utils` numbers) instead of client-loading the full ops panel. Geist webfont removed. `/ops` still has the full panel. Re-run Lighthouse on http://localhost:3001/ after a hard refresh.

**Backoffice home performance (PLAN-044):** Authenticated `/` no longer waits on “Loading session” to paint. `fetchAuthMe` still runs. Home defers Milestone 2 ops JS (`dynamic`, `ssr: false`); `/ops` still has the full panel. Nav prefetch off. Re-run Lighthouse on http://localhost:3001/ after login.

**Backoffice login performance (PLAN-043):** Public auth routes no longer wait on “Loading session”. Login heading is server-rendered; unused Geist Mono removed; chrome omitted on `/login`. Protected routes still use JWT + `/auth/me`. Re-run Lighthouse on http://localhost:3001/login after Next is Ready.

**Container browse runbook (PLAN-042):** Docs-only. [`CONTEXT-MS5-container.md`](../docs/Project_Contexts/CONTEXT-MS5-container.md) How to run now states: after containers are up, use a host browser on localhost 3000/3001/8001; Docker Desktop is not the website; `/health` JSON may look blank; troubleshooting for virtualization and `docker` not on PATH.

## Today’s update (2026-09-14)

**Development Compose implementation (PLAN-041):** Ticket `#infra-40` files shipped — `uis/Dockerfile` + `start.sh`, `services/Dockerfile` (`uv pip install --system "-r"` + uvicorn `--reload`), both `.dockerignore` files, root `docker-compose.yml` (`ui`/`api`, network `healthcore`), backoffice `/hc-api` rewrite to `http://api:8001`, gitignored root `.env`. Docker CLI was not installed here, so `docker compose up` was not run. Follow the runbook in [`CONTEXT-MS5-container.md`](../docs/Project_Contexts/CONTEXT-MS5-container.md).

**Container CONTEXT audit (PLAN-040):** Docs-only. Re-read `#infra-40` against [`CONTEXT-MS5-container.md`](../docs/Project_Contexts/CONTEXT-MS5-container.md). Tightened in/out of scope (no seed-on-boot, no extra Compose services, no new error UI). Replaced Alpine `wget` samples with `node fetch`. Added post-implementation runbook: Docker Desktop download → engine check → root `.env` → `docker compose up --build`. Docker files still not implemented.

**Development containerization CONTEXT (PLAN-039):** Docs-only. Implementing agents must follow [`docs/Project_Contexts/CONTEXT-MS5-container.md`](../docs/Project_Contexts/CONTEXT-MS5-container.md) for ticket `#infra-40`. One UI container (`uis/healthcore` on 3000 + `uis/backoffice` on 3001), FastAPI `--reload` as Compose service `api` on 8001, named network `healthcore`, root `.env`, `/hc-api` rewrite to `http://api:8001`. No Dockerfiles or `docker-compose.yml` in that stamp.

## Today’s update (2026-09-11)

**Runtime overlay (PLAN-038):** Root layout wraps AuthGuard in Suspense. Turbopack root pinned to the monorepo so `@hc` ops imports resolve. Pytest 46, Jest 18, `next build` pass.

**ORM-first alignment (PLAN-037):** Canonical order is dual-database API, then MS5 backoffice. Orders keep `user_uuid` in SQLModel; HTTP adds TinyDB `created_by` email for history. Both evals re-run: ORM **12/12**, MS5 UI **8/8**. Pytest 46, Jest 18.

**Inventory ORM eval re-run:** Rubric 12/12 Pass. Pytest 46, inventory 10, Jest 15. Live API: gloves/pads stock 12/80, outbound 9999 → 400 with no stock change, orders have `user_uuid` and `product_name`. Write-up: [Results/InventoryORM-20260911.md](./evaluations/Results/InventoryORM-20260911.md).

**Backoffice Issue overlay (PLAN-036):** Login and reset-password now wrap `useSearchParams` in `Suspense`. Order history rows use `${type}-${id}` so inbound and outbound ids do not collide. Lint/tsc pass.

**Inventory Table Editor labels (PLAN-035):** Postgres tables renamed to `medical_supply`, `inbound_order`, `outbound_order`. Orders store `product_name` and `sku`. Combined view `inventory_order`. Startup migration keeps seed rows if SQLModel had already created empty snake_case tables. Pytest 46.

**Inventory ORM dual-database implementation (PLAN-034):** TinyDB remains auth-only. Inventory uses SQLModel (`MedicalSupply`, inbound/outbound orders), computed `current_stock`, TinyDB `user_uuid`, routes under `/inventory/orders/*`. Pytest 45, Jest 15, lint/tsc pass. Eval 12/12 Pass — [Results/InventoryORM-20260911.md](./evaluations/Results/InventoryORM-20260911.md).

**Inventory ORM dual-database CONTEXT (PLAN-033):** Docs-only. Implementing agents must follow [`docs/Project_Contexts/CONTEXT-inventory-orm-dual-database.md`](../docs/Project_Contexts/CONTEXT-inventory-orm-dual-database.md). TinyDB stays for auth; Supabase/SQLModel for inventory; `current_stock` computed; `user_uuid` from TinyDB; routes under `/inventory/orders/*`.

## Today’s update (2026-09-09)

**Env ignore note + MS5 re-run (PLAN-032):** Project-level “never commit `.env` files” added to [`README.md`](../README.md) and [`AGENTS.md`](../AGENTS.md). Re-ran MS5: pytest 43, Jest 15, lint/tsc pass, live API and backoffice 200. Eval still **8/8 Pass**.

**MS5 inventory CONTEXT how to run (PLAN-031):** Docs-only. Expanded runbook in [`CONTEXT-MS5-inventory-backoffice.md`](../docs/Project_Contexts/CONTEXT-MS5-inventory-backoffice.md) (API seed + JWT, backoffice inventory URLs, tests, public site isolation).

**MS5 inventory implementation (PLAN-030):** TinyDB `/inventory` API plus four authenticated backoffice views. Central `inventory-api.ts`, outbound available-stock display, readable 400s. Pytest 43 passed; Jest 15 passed. Eval 8/8 Pass — [MS5_Project_Eval](./evaluations/MS5_Project_Eval.md).

**MS5 inventory CONTEXT eval + samples (PLAN-029):** Docs-only. Official eight-item rubric and sample JSON (products, inbound/outbound, 400 insufficient stock, empty arrays, 401) added to [`CONTEXT-MS5-inventory-backoffice.md`](../docs/Project_Contexts/CONTEXT-MS5-inventory-backoffice.md). No inventory UI code.

**MS5 inventory backoffice CONTEXT (PLAN-028):** Docs-only. Implementing agents must follow [`docs/Project_Contexts/CONTEXT-MS5-inventory-backoffice.md`](../docs/Project_Contexts/CONTEXT-MS5-inventory-backoffice.md). Four authenticated views (stock, inbound, outbound with available stock before submit, order history) reuse AUTH-02 JWT + `AuthGuard` from [`auth_master_framework_Context.md`](../docs/Project_Contexts/auth_master_framework_Context.md). No inventory UI or API code in this stamp.

## Today’s update (2026-08-31)

**Unit testing (PLAN-027):** Root `TESTING.md` with planned happy/edge/failure cases, FastAPI pytest in `services/api/tests/` (isolated TinyDB), Jest in `uis/backoffice/__tests__/`. Auth module 91% (≥70%), suppliers+incidents 81% (≥50%). No product bugs found.

**Unit testing evaluation:** Rubric 8/8 Pass — [Results/UnitTesting-20260831.md](./evaluations/Results/UnitTesting-20260831.md). `python -m uv run pytest` from repo root: 36 passed.

## Today’s update (2026-08-28)

**Error handling skills and context (PLAN-023):** Split ErrorHandling Requirement.txt into audit / frontend / backend / scripts Cursor skills plus shared policy and findings-taxonomy context. HealthCore repo notes kept (UI isolation, FastAPI paths, PHI-safe reporting, demo auth). No UI or API code changes.

**Error handling audit and plan (PLAN-024):** Full-repo audit against the eight taxonomy categories; sequenced implementation plan (API → UI → scripts).

**Error handling implementation (PLAN-025):** FastAPI structured handlers, sanitized backoffice three-state UI with retry/home/support, script `sys.exit(1)` on I/O failure. Evaluation 8/8 Pass (patterns). Lint/tsc skipped (`node_modules` missing).

**Error handling polish (PLAN-026):** Session-expired login banner, wrapped public auth fetch, hiring form CTAs/`finally`, mapped analysis errors, quieter API logs, CLI file-not-found without paths. Demo reset-link logs kept per PLAN-022.

## Today’s update (2026-08-26)

**Auth master framework CONTEXT (PLAN-017):** Docs-only. External implementing agents must follow [`docs/Project_Contexts/auth_master_framework_Context.md`](../docs/Project_Contexts/auth_master_framework_Context.md). Three sequential tasks (API, frontend flows, password restore) on one JWT + TinyDB identity contract. No auth code in this stamp.

## Today’s update (2026-08-27)

**Auth implementation task board (PLAN-018):** Added a planned implementation stamp covering AUTH-01, AUTH-02, and AUTH-03 sequencing, acceptance checklist, and guardrails from the locked auth context. This planning stamp was followed by AUTH-01 implementation in PLAN-019.

**AUTH-01 API implementation (PLAN-019):** Implemented JWT bearer auth in FastAPI with TinyDB users/profiles in `services/api/data/auth.json`, new `/auth`, `/users`, `/profiles` routers, owner/admin checks for user mutation, and token protection on all six supplier routes plus both incident routes. `GET /health` remains public.

**AUTH-02 frontend implementation (PLAN-020):** Added backoffice `/login`, `/register`, and `/account/profile` flows with localStorage token storage, client auth guard, bearer headers on supplier/incident requests, centralized 401 logout redirect, and navigation logout control.

**AUTH-03 password implementation (PLAN-021):** Added `/auth/forgot-password`, `/auth/reset-password`, and `/auth/change-password` plus backoffice `/forgot-password`, `/reset-password`, and `/account/change-password` pages. Reset tokens are hashed in TinyDB and invalidated via expiry + one-time use.

**Auth demo mode no realtime email (PLAN-022):** Disabled outbound provider communication for forgot-password in demo runs and removed provider keys from `.env.example`. Reset links are now logged locally for demo verification while keeping generic 200 responses.

### Prior (2026-08-19)

**Supplier Directory domain fix (PLAN-016):** Teacher rejected custom `contract_rate` / `US` / six synthetic vendors. API + backoffice now use official `monthly_rate`, currency pairing, `USA`/`UK`, and 15 seeded suppliers. Routes, filters, and patches unchanged. Prior eval [SupplierDirectory-20260810.md](./evaluations/Results/SupplierDirectory-20260810.md) not rewritten.

### Prior (2026-08-10)

**Supplier Directory implementation (PLAN-015):** FastAPI TinyDB suppliers CRUD/patches, `seed.py`, backoffice `/suppliers`. Structure kept.

### Prior (2026-08-07)

**Incident File Analyzer domain fix (PLAN-012):** HealthCore schema + sample metrics. Eval → [Results/IncidentFileAnalyzer-20260807.md](./evaluations/Results/IncidentFileAnalyzer-20260807.md).

## Run

```bash
# API (incidents + suppliers + inventory)
cd services/api && python -m pip install -r requirements.txt
# Set DATABASE_URL (Supabase pooler) and JWT_SECRET_KEY in .env — do not commit
python seed.py
python -m uvicorn app.main:app --reload --port 8001

# UIs
cd uis/healthcore && npm run dev    # http://localhost:3000
cd uis/backoffice && npm run dev    # http://localhost:3001  (/suppliers, /incidents, /inventory → API :8001)

# Tests — see TESTING.md
cd services/api && python -m pip install -r requirements-dev.txt && python -m pytest
cd uis/backoffice && npm test
```
