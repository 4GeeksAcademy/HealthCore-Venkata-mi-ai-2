# HealthCore — Progress

**Last updated:** 2026-08-07  
**Latest stamped plan:** [HC-MS4-PLAN-012](./plans/HC-MS4-PLAN-012-20260807-incident-analyzer-domain-fix.md) (`implemented`, MS4, implementation)  
**Prior completed stamp:** [HC-MS4-PLAN-011](./plans/HC-MS4-PLAN-011-20260805-incident-analyzer-impl.md) (`implemented`, MS4, implementation)  
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
| Backoffice | Done — welcome, `/ops`, `/hiring`, **`/incidents`** |
| MS4 evaluation | **complete PASS** |
| FastAPI architecture proposal | In review (PLAN-006–009) |
| Incident File Analyzer | **Domain fixed** (PLAN-012) — HealthCore schema (`clinic_id`/`country`/`patient_id`, uppercase categories); sample **100 / 94 / 6 / avg 3.58** → [Results/IncidentFileAnalyzer-20260807.md](./evaluations/Results/IncidentFileAnalyzer-20260807.md) |

## Today’s update (2026-08-07)

**Incident File Analyzer domain fix (PLAN-012):** Teacher feedback — generic `reported_date`/`location_id` and lowercase categories blocked HealthCore validation. Rebuilt [`scripts/samples/incidents-healthcore.csv`](../scripts/samples/incidents-healthcore.csv), updated shared [`incident_analysis.py`](../services/api/app/incident_analysis.py) and [`IncidentFileAnalyzer.md`](../docs/Project_Contexts/IncidentFileAnalyzer.md). CLI/API/UI wiring unchanged. Eval → [Results/IncidentFileAnalyzer-20260807.md](./evaluations/Results/IncidentFileAnalyzer-20260807.md).

### Prior (2026-08-05)

**Incident File Analyzer (PLAN-011):** Shared Python analysis; CLI; FastAPI; backoffice `/incidents`. (Superseded domain contract by PLAN-012.)

**CONTEXT doc (PLAN-010):** [`docs/Project_Contexts/IncidentFileAnalyzer.md`](../docs/Project_Contexts/IncidentFileAnalyzer.md).

### Prior docs note (2026-07-31)

[`docs/ARCHITECTURE_PROPOSAL.md`](../docs/ARCHITECTURE_PROPOSAL.md) — FastAPI proposal remains **In review** (PLAN-006–009).

## Run

```bash
# Incident API
cd services/api && python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8001

# CLI
python scripts/analyze.py scripts/samples/incidents-healthcore.csv

# UIs
cd uis/healthcore && npm run dev    # http://localhost:3000
cd uis/backoffice && npm run dev    # http://localhost:3001  (/incidents → API :8001)
```
