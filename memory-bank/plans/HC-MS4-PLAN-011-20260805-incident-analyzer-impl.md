---
stamp: HC-MS4-PLAN-011
sequence: 11
milestone: MS4
date: 20260805
title: Incident File Analyzer Implementation
status: implemented
phase: implementation
summary: Implemented shared Python incident analysis, scripts/analyze.py CLI, FastAPI services/api (POST analyze + GET export), and backoffice /incidents UI. Sample CSV + expected values filled in IncidentFileAnalyzer.md.
related_paths:
  - services/api/app/incident_analysis.py
  - services/api/app/main.py
  - services/api/app/routers/incidents.py
  - scripts/analyze.py
  - scripts/samples/incidents-healthcore.csv
  - uis/backoffice/app/incidents/page.tsx
  - uis/backoffice/components/incidents/IncidentAnalyzerPanel.tsx
  - docs/Project_Contexts/IncidentFileAnalyzer.md
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Duplicate validation/metrics logic between CLI and API
  - Place IncidentFileAnalyzer.md under docs/ root
  - Create docs/Plans/
  - Scaffold full ARCHITECTURE_PROPOSAL backend/ instead of services/api for this feature
---

# HC-MS4-PLAN-011 — Incident File Analyzer Implementation

## Decisions locked

- Shared core: `services/api/app/incident_analysis.py` (stdlib csv); CLI imports via `sys.path`.
- API: FastAPI under `services/api` — `POST /api/incidents/analyze`, `GET /api/incidents/results/export`, CORS for `:3001`.
- UI: `uis/backoffice` `/incidents` (assignment `/src/web` mapped to backoffice).
- Sample: `scripts/samples/incidents-healthcore.csv`; expected values documented in CONTEXT (20/16/4, avg 3.75).

## Agent instructions

1. Keep CLI and API on the shared `incident_analysis` module; do not fork logic.
2. Do not move the CONTEXT file out of `docs/Project_Contexts/`.
3. Do not create `docs/Plans/`.
4. Further backend domains may follow ARCHITECTURE_PROPOSAL `backend/`; this feature stays under `services/api` unless a human requests migration.
5. Append new stamps; do not rewrite this stamp.
