# HealthCore — Progress

**Last updated:** 2026-08-05  
**Latest stamped plan:** [HC-MS4-PLAN-011](./plans/HC-MS4-PLAN-011-20260805-incident-analyzer-impl.md) (`implemented`, MS4, implementation)  
**Prior completed stamp:** [HC-MS4-PLAN-010](./plans/HC-MS4-PLAN-010-20260805-incident-analyzer-context.md) (`implemented`, MS4, docs)  
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
| Incident File Analyzer | **Implemented** (PLAN-011) — CLI + `services/api` + backoffice UI; eval **14/14 Pass** → [Results/IncidentFileAnalyzer.md](./evaluations/Results/IncidentFileAnalyzer.md) |

## Today’s update (2026-08-05)

**Incident File Analyzer (PLAN-011):** Shared Python analysis in `services/api/app/incident_analysis.py`; CLI `scripts/analyze.py`; FastAPI `POST /api/incidents/analyze` + `GET /api/incidents/results/export`; backoffice `/incidents` upload UI. Sample + expected values in [`IncidentFileAnalyzer.md`](../docs/Project_Contexts/IncidentFileAnalyzer.md).

### Prior (same day)

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
