# HealthCore — Progress

**Last updated:** 2026-08-19  
**Latest stamped plan:** [HC-MS4-PLAN-016](./plans/HC-MS4-PLAN-016-20260819-supplier-directory-domain-fix.md) (`implemented`, MS4, implementation)  
**Prior completed stamp:** [HC-MS4-PLAN-015](./plans/HC-MS4-PLAN-015-20260810-supplier-directory-impl.md) (`implemented`, MS4, implementation)  
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

## Today’s update (2026-08-19)

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
