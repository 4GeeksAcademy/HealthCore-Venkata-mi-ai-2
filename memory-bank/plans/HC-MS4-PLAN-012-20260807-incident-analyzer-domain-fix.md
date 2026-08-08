---
stamp: HC-MS4-PLAN-012
sequence: 12
milestone: MS4
date: 20260807
title: Incident File Analyzer HealthCore Domain Fix
status: implemented
phase: implementation
summary: Rebuilt Incident File Analyzer domain per teacher feedback — HealthCore CSV columns (clinic_id, country, patient_id), uppercase categories (APPOINTMENT/BILLING/…), sample + expected values 100/94/6/avg 3.58; shared analysis + CONTEXT updated; CLI/API wiring unchanged.
related_paths:
  - services/api/app/incident_analysis.py
  - scripts/samples/incidents-healthcore.csv
  - docs/Project_Contexts/IncidentFileAnalyzer.md
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
  - memory-bank/evaluations/Results/IncidentFileAnalyzer-20260807.md
  - memory-bank/evaluations/INDEX.md
do_not_repeat:
  - Restore generic reported_date / location_id schema for HealthCore incidents
  - Use lowercase categories (clinical_safety, billing_access, …) for this analyzer
  - Duplicate validation/metrics logic between CLI and API
  - Rewrite prior plan stamps PLAN-010 / PLAN-011
---

# HC-MS4-PLAN-012 — Incident File Analyzer HealthCore Domain Fix

## Decisions locked

- Required columns: `incident_id`, `clinic_id`, `country`, `patient_id`, `category`, `status` (+ optional `satisfaction_score`).
- Categories: `APPOINTMENT`, `BILLING`, `CLINICAL`, `FACILITIES`, `IT`, `WORKFORCE` (uppercase).
- Statuses remain `open` / `closed` / `discarded`.
- Sample path unchanged: `scripts/samples/incidents-healthcore.csv` (100 rows → 94 valid / 6 invalid / avg satisfaction **3.58**).
- Shared core remains `services/api/app/incident_analysis.py`; CLI and API keep importing it.
- Teacher feedback addressed without changing API routes or backoffice page structure.

## Agent instructions

1. Keep CLI and API on the shared `incident_analysis` module; do not fork HealthCore domain rules.
2. Do not revert to `reported_date` / `location_id` or lowercase categories for this feature.
3. Do not move CONTEXT out of `docs/Project_Contexts/IncidentFileAnalyzer.md`.
4. Append new stamps; do not rewrite this stamp or PLAN-010 / PLAN-011.
5. Treat `memory-bank/evaluations/Results/IncidentFileAnalyzer-20260807.md` as the domain-fix acceptance record.
