# HealthCore — Progress

**Last updated:** 2026-08-27  
**Latest stamped plan:** [HC-MS4-PLAN-022](./plans/HC-MS4-PLAN-022-20260827-auth-demo-no-realtime-email.md) (`implemented`, MS4, implementation)  
**Prior completed stamp:** [HC-MS4-PLAN-021](./plans/HC-MS4-PLAN-021-20260827-auth-03-password-reset-implementation.md) (`implemented`, MS4, implementation)  
**Latest milestone eval:** [MS4_Project_Eval](./evaluations/MS4_Project_Eval.md) (`complete` — official rubric **8/8 Pass**)

## Rubric mapping (MS4)

- `uis/website` → **`uis/healthcore`**
- Milestone 2 in backoffice → **`src/utils`** TypeScript (denial / no-show / CME) visible on **`/ops`** and home panel  
  (hiring tracker is separate — not Milestone 2)

## Current state

| Area | Status |
|------|--------|
| Milestone 2 `src/utils/` | Present + **integrated into backoffice UI** |
| Public site `uis/healthcore` | Done (rubric “website”) |
| Backoffice | Done — welcome, `/ops`, `/hiring`, `/incidents`, **`/suppliers`** |
| MS4 evaluation | **complete PASS** |
| FastAPI architecture proposal | In review (PLAN-006–009) |
| Incident File Analyzer | **Domain fixed** (PLAN-012) |
| Supplier Directory | **Domain fixed** (PLAN-016) — `monthly_rate`, `USA`/`UK` + `USD`/`GBP`, 15 seeds (McKesson, Epic); structure from PLAN-015 kept; eval → [Results/SupplierDirectory-20260819.md](./evaluations/Results/SupplierDirectory-20260819.md) |
| Auth (AUTH-01/02/03) | **Implemented** (PLAN-019, PLAN-020, PLAN-021) — [auth_master_framework_Context.md](../docs/Project_Contexts/auth_master_framework_Context.md). API JWT, protected routes, backoffice auth flows, and password recovery/change are in place. |

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
# API (incidents + suppliers)
cd services/api && python -m pip install -r requirements.txt
python seed.py
python -m uvicorn app.main:app --reload --port 8001

# UIs
cd uis/healthcore && npm run dev    # http://localhost:3000
cd uis/backoffice && npm run dev    # http://localhost:3001  (/suppliers, /incidents → API :8001)
```
