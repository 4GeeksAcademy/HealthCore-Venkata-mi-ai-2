---
stamp: HC-MS4-PLAN-010
sequence: 10
milestone: MS4
date: 20260805
title: Company Incident File Analyzer Context Document
status: implemented
phase: docs
summary: Authored docs/Project_Contexts/IncidentFileAnalyzer.md — assignment CONTEXT for incident CSV analysis (invalid-record rules, CSV contract, Phase 1 script, Phase 2 API/UI, evaluation checklist). Docs only; no analyzer code.
related_paths:
  - docs/Project_Contexts/IncidentFileAnalyzer.md
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Create docs/Plans/ for this work
  - Place IncidentFileAnalyzer.md directly under docs/
  - Treat this stamp as implemented analyze.py / API / frontend
  - Rewrite root CONTEXT.md for the incident analyzer assignment
---

# HC-MS4-PLAN-010 — Company Incident File Analyzer Context Document

## Decisions locked

- Context file path: `docs/Project_Contexts/IncidentFileAnalyzer.md` (not `docs/` root).
- Plan archive: `memory-bank/plans/` only — no `docs/Plans/`.
- Root `CONTEXT.md` / `CONTEXT_temp.md` unchanged.
- CSV contract locked in the CONTEXT: required fields, statuses `open`/`closed`/`discarded`, six HealthCore categories; expected numeric values left TBD until sample CSV exists.
- Docs only — no script, API, or UI implementation in this stamp.

## Agent instructions

1. Do not create `docs/Plans/`.
2. Do not place `IncidentFileAnalyzer.md` directly under `docs/`.
3. Do not treat this stamp as implemented analyzer code (`analyze.py`, `/api/incidents/*`, or frontend page).
4. Do not rewrite root `CONTEXT.md` for the incident analyzer; use `docs/Project_Contexts/IncidentFileAnalyzer.md`.
5. Append new stamps for implementation work; do not rewrite this stamp.
