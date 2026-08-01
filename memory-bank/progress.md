# HealthCore — Progress

**Last updated:** 2026-07-31  
**Latest stamped plan:** [HC-MS4-PLAN-008](./plans/HC-MS4-PLAN-008-20260731-architecture-proposal-project-cleanup.md) (`implemented`, MS4, docs)  
**Prior completed stamp:** [HC-MS4-PLAN-005](./plans/HC-MS4-PLAN-005-20260722-ms2-ops-in-backoffice.md) (`implemented`, MS4)  
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
| Backoffice | Done — welcome, `/ops` MS2 metrics, `/hiring` |
| MS4 evaluation | **complete PASS** |
| FastAPI architecture proposal | See **Today’s update** below (in review until human sign-off) |

## Today’s update (2026-07-31) — single entry

**FastAPI architecture proposal** — [`docs/ARCHITECTURE_PROPOSAL.md`](../docs/ARCHITECTURE_PROPOSAL.md)

- Doc-only proposal for a HealthCore Digital FastAPI backend under `backend/` (no backend scaffolded).
- Recommends **Layered / Clean Architecture** after comparing Layered/Clean, MVC, Microservices, and Serverless.
- Grounded in project surfaces: `src/utils`, `uis/healthcore` (`:3000`), `uis/backoffice` (`:3001` `/ops` + `/hiring`); backoffice is the API client; public site does not consume ops/hiring APIs.
- Latest pass: project cleanup (removed non-project fluff; locked session/cookie staff auth; shortened summary). Status: **In review**.
- Same-day stamps (history): PLAN-006 → PLAN-007 → **PLAN-008** (latest).

## Run

```bash
cd uis/healthcore && npm run dev    # http://localhost:3000
cd uis/backoffice && npm run dev    # http://localhost:3001  (/ and /ops show MS2 output)
```
