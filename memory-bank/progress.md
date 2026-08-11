# HealthCore — Progress

**Last updated:** 2026-08-10  
**Latest stamped plan:** [HC-MS4-PLAN-015](./plans/HC-MS4-PLAN-015-20260810-supplier-directory-impl.md) (`implemented`, MS4, implementation)  
**Prior completed stamp:** [HC-MS4-PLAN-014](./plans/HC-MS4-PLAN-014-20260810-supplier-directory-context-tighten.md) (`implemented`, MS4, docs)  
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
| Supplier Directory | **Implemented** (PLAN-015) — TinyDB + `/suppliers` API + backoffice UI; eval → [Results/SupplierDirectory-20260810.md](./evaluations/Results/SupplierDirectory-20260810.md) |

## Today’s update (2026-08-10)

**Supplier Directory implementation (PLAN-015):** FastAPI TinyDB suppliers CRUD/patches, `seed.py`, backoffice `/suppliers` (filters, create, rate, status badges). CONTEXT remains [`docs/Project_Contexts/SupplierDirectory_TinyDb_API.md`](../docs/Project_Contexts/SupplierDirectory_TinyDb_API.md). Process to Run saved on the cursor supplier-directory plan.

**Prior today — CONTEXT tighten (PLAN-014) / CONTEXT author (PLAN-013):** Docs-only field contract and evaluation gaps.

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
