# HealthCore — Progress

**Last updated:** 2026-07-31  
**Latest stamped plan:** [HC-MS4-PLAN-009](./plans/HC-MS4-PLAN-009-20260731-architecture-proposal-sources.md) (`implemented`, MS4, docs)  
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

## Today’s update (2026-07-31)

**Artifact:** [`docs/ARCHITECTURE_PROPOSAL.md`](../docs/ARCHITECTURE_PROPOSAL.md) — doc-only FastAPI proposal (no backend scaffolded). Status: **In review**.

### History (same day)

1. **[HC-MS4-PLAN-006](./plans/HC-MS4-PLAN-006-20260731-fastapi-architecture-proposal.md)** — Initial proposal: Layered/Clean recommendation, HealthCore company context, backend folder layout, domain routers, FastAPI standards, FE/BE separation, risks.
2. **[HC-MS4-PLAN-007](./plans/HC-MS4-PLAN-007-20260731-architecture-pattern-comparison.md)** — Expanded Section 2: pros/cons for Layered/Clean, MVC, Microservices, Serverless + comparative table and strong recommendation.
3. **[HC-MS4-PLAN-008](./plans/HC-MS4-PLAN-008-20260731-architecture-proposal-project-cleanup.md)** — Project cleanup: linked `src/utils` and ports `:3000`/`:3001`; locked session/cookie staff auth; public site does not consume ops/hiring APIs; removed non-project fluff.
4. **[HC-MS4-PLAN-009](./plans/HC-MS4-PLAN-009-20260731-architecture-proposal-sources.md)** — **Latest:** Section 5 cites official FastAPI sources (Bigger Applications, Dependencies, CORS, Settings, Body) for the conventions rubric.

### Current snapshot (latest)

- Recommends **Layered / Clean Architecture** after comparing four patterns.
- Grounded in `src/utils`, `uis/healthcore` (`:3000`), `uis/backoffice` (`:3001` `/ops` + `/hiring`).
- Explicit FastAPI documentation sources in Section 5.

## Run

```bash
cd uis/healthcore && npm run dev    # http://localhost:3000
cd uis/backoffice && npm run dev    # http://localhost:3001  (/ and /ops show MS2 output)
```
