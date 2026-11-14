---
stamp: HC-MS5-PLAN-122
sequence: 122
milestone: MS5
date: 2026-11-13
title: Centralized Incident Manager Plan
status: planned
phase: planning
summary: >
  Plan for the Centralized Incident Manager challenge. Official syllabus CSV
  and healthcore-incident-manager BRIEFING drive the model, seed transforms,
  lifecycle API, and backoffice register/list/summary UI. Shared validation
  moves to packages/shared. Downstream MCP and agent ticket contracts adapt.
  Does not close MS5. Eval Results wait for human approval. The human commits.
related_paths:
  - docs/Project_Contexts/CentralizedIncidentManager.md
  - docs/Project_Contexts/healthcore-incident-manager-BRIEFING.md
  - packages/shared/healthcore_incidents/
  - scripts/seed_incidents.py
  - scripts/samples/incidents-healthcore.csv
  - services/api/app/models/incidents.py
  - services/api/app/incidents_store.py
  - services/api/app/routers/incidents.py
  - uis/backoffice/app/(internal)/incidents/
do_not_repeat:
  - Invent a second incidents schema beside the BRIEFING manager model
  - Keep PLAN-012 custom CSV columns as the seed source
  - Store patient_id in the manager database
  - Upsert analyzer CSV rows into the manager store without transforms
  - Save memory-bank/evaluations/Results/CentralizedIncidentManager-*.md before human approval
  - Close MS5
  - Commit on the human's behalf
  - Edit CONTEXT.md, projectbrief, techContext, data/, .env, or root lockfiles
  - Rewrite prior stamps
---

# HC-MS5-PLAN-122 — Centralized Incident Manager plan

Brief: [`docs/Project_Contexts/CentralizedIncidentManager.md`](../../docs/Project_Contexts/CentralizedIncidentManager.md).  
Company rules: [`docs/Project_Contexts/healthcore-incident-manager-BRIEFING.md`](../../docs/Project_Contexts/healthcore-incident-manager-BRIEFING.md).

## Locked decisions

| Decision | Choice |
|----------|--------|
| Milestone | MS5 platform catch-up. Does not close MS5. |
| BRIEFING | Archived locally; values must match exactly. |
| Seed CSV | Official syllabus `incidents-healthcore.csv` (94 valid). |
| Shared logic | `packages/shared/healthcore_incidents/` for validation + transforms. |
| Manager writes | Seed script + registration form only. Analyze is metrics-only. |
| Persistence | TinyDB `incidents.json` with new document shape + `source_key`. |
| Downstream | MCP + knowledge-agent ticket contracts updated to new fields. |
| Eval | Rubric in chat first; Results file only after human approval. |

## Agent instructions

1. Implement under PLAN-123. Do not reopen this decision table.
2. Do not write the CentralizedIncidentManager Results file until the human approves the rubric in chat.
3. Do not close MS5.
4. Do not commit.
5. Never store `patient_id` in the manager store or return it from manager endpoints.
