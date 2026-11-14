# Centralized Incident Manager — Evaluation

**Date:** 2026-11-13  
**Rubric:** Centralized Incident Manager — "What We Will Evaluate"  
**Implementation as of:** [HC-MS5-PLAN-123](../../plans/HC-MS5-PLAN-123-20261113-centralized-incident-manager-impl.md)  
**Plan:** [HC-MS5-PLAN-122](../../plans/HC-MS5-PLAN-122-20261113-centralized-incident-manager-plan.md)  
**Overall: 22/22 Pass.** This file does not close MS5.

| Doc | Path |
|-----|------|
| Challenge | [`docs/Project_Contexts/CentralizedIncidentManager.md`](../../../docs/Project_Contexts/CentralizedIncidentManager.md) |
| Company briefing | [`docs/Project_Contexts/healthcore-incident-manager-BRIEFING.md`](../../../docs/Project_Contexts/healthcore-incident-manager-BRIEFING.md) |
| Shared package | [`packages/shared/healthcore_incidents/`](../../../packages/shared/healthcore_incidents/) |
| Seed | [`scripts/seed_incidents.py`](../../../scripts/seed_incidents.py) |
| Sample CSV | [`scripts/samples/incidents-healthcore.csv`](../../../scripts/samples/incidents-healthcore.csv) |
| API | [`services/api/app/routers/incidents.py`](../../../services/api/app/routers/incidents.py), [`incidents_store.py`](../../../services/api/app/incidents_store.py) |
| Backoffice | [`uis/backoffice/app/(internal)/incidents/`](../../../uis/backoffice/app/(internal)/incidents/) |

Saved after human approval on 2026-11-13. Same-day re-evals overwrite this file only. Does not replace [IncidentFileAnalyzer-20260807](./IncidentFileAnalyzer-20260807.md).

## Method

- Official syllabus CSV replaced the divergent PLAN-012 sample so seed totals match the BRIEFING.
- Shared CSV validation + CSV→manager transforms live in `packages/shared/healthcore_incidents/` and are reused by seed, analyzer wrapper, and API.
- Manager writes: seed script + registration form only. `POST /analyze` is metrics-only (no manager upsert).
- Seed ×2: 94 inserted, then 94 skipped. Summary: open 28 / resolved 52 / discarded 14; patient_experience 61 / billing_error 20 / other 13; branch rollups match BRIEFING.
- `python -m pytest services/api/tests/test_incidents.py`: **9 passed**.
- `python -m pytest services/api/tests/test_agent_tools_live_api.py`: **3 passed**.
- `python -m pytest tests/pipelines/test_agent_tools.py`: **45 passed** (schema adapted).
- Backoffice lint/tsc were not run in-session (`node_modules` missing; npm install did not complete). UI criteria judged from implemented code paths.
- `.env` was not part of the evidence. The human commits.

## Rubric

### Model and seed

| # | Criterion | Result | Evidence |
|---|-----------|--------|----------|
| 1 | Model includes all required fields with integrity constraints | Pass | `IncidentRecord` / `IncidentCreate`: id, title, description, category, status, origin, branch, created_at, updated_at; enums from BRIEFING. |
| 2 | Seed loads historical incidents with `origin: "customer"` | Pass | Transform always sets `origin=customer`; summary `by_origin.customer == 94`. |
| 3 | Seed applies CSV → model transforms (status, category, title, dates, branch) | Pass | `packages/shared/healthcore_incidents/transform.py` maps OPEN→open, CLOSED→resolved, categories, title from description[:120], date→UTC midnight, clinic_id→branch. |
| 4 | Invalid CSV records not inserted; reported to console | Pass | Seed reports 6 rejected with rule codes and incident ids; no `patient_id` values printed. |
| 5 | Script is idempotent | Pass | Second run: Inserted 0, Skipped 94. |
| 6 | After seeding, `/summary` status and category match BRIEFING | Pass | open 28, resolved 52, discarded 14; patient_experience 61, billing_error 20, other 13. |

### Backend

| # | Criterion | Result | Evidence |
|---|-----------|--------|----------|
| 7 | Endpoints respond with correct HTTP codes | Pass | Create 201; missing 404; bad transition/validation 400; auth 401; covered in `test_incidents.py`. |
| 8 | Validation errors identify the problematic field | Pass | `detail: {field, message}` on create/status validation failures. |
| 9 | No endpoint exposes a stack trace | Pass | Generic 500 messages; structured handlers; no traceback in client bodies. |
| 10 | Invalid status transitions rejected with 400 | Pass | open→resolved rejected; resolved/discarded final. |
| 11 | `/summary` correct with no incidents | Pass | Empty store returns zeros and `total: 0`. |

### Frontend

| # | Criterion | Result | Evidence |
|---|-----------|--------|----------|
| 12 | Form validates required fields on the client before submit | Pass | `IncidentRegisterForm` client checks title/description/category/origin/branch. |
| 13 | When origin is `branch`, branch field highlighted; BRIEFING labels | Pass | Highlight styles when `origin==="branch"`; `INCIDENT_BRANCHES` display names. |
| 14 | Loading states visible; submit disabled during request | Pass | `submitting` disables controls; button shows “Saving…”. |
| 15 | API errors shown in plain language, never raw technical text | Pass | Field-level / form errors via `getUserFacingError` + API field messages. |
| 16 | List handles loading, empty, with data | Pass | `IncidentListPanel` three states + retry/home on error. |
| 17 | Status updates revert visually if the request fails | Pass | Optimistic update then restore previous status on failure. |
| 18 | Summary panel does not break the page if its request fails | Pass | Independent panel with retry; list remains usable. |

### Cross-cutting

| # | Criterion | Result | Evidence |
|---|-----------|--------|----------|
| 19 | Validation extracted to `packages/shared/` and reused by script and API | Pass | `healthcore_incidents` imported by seed, `incident_analysis` wrapper, store lifecycle helpers. |
| 20 | Code organised per monorepo (`scripts/`, `services/`, `uis/`, `packages/shared/`) | Pass | Matches challenge layout. |
| 21 | Prominent PHI warning on registration form | Pass | High-contrast warning above description (BRIEFING compliance). |
| 22 | Manager never stores `patient_id` | Pass | Transform omits it; create body has no patient fields; responses omit it. |

## Noted limits (accepted in this save)

1. Backoffice `npm run lint` / `tsc` were not executed in-session because `uis/backoffice/node_modules` was missing.
2. PR screenshot artifacts (form validation, list, summary) were not captured in-session; implementer should attach them when opening the PR.
3. MCP package tests were not run here (`mcp` module not installed in the root environment); MCP tool schemas were updated to the new manager contract.

## Agent instructions

1. Canonical eval: this file. Official rubric score: **22/22 Pass**.
2. Same-day re-evals overwrite this file only. Do not append a second `CentralizedIncidentManager-20261113` file.
3. Do not treat this as an MS5 milestone close.
4. Do not rewrite PLAN-122 or PLAN-123.
5. The human commits. Do not commit on their behalf. Do not commit `.env`.
