---
stamp: HC-MS5-PLAN-079
sequence: 79
milestone: MS5
date: 2026-10-07
title: Resilient Monthly Clinic Supply Pipeline Implementation
status: implemented
phase: implementation
summary: >
  Prefect ETL for monthly clinic supply KPIs, reporting tables, CLI entry,
  and three JWT services/reporting endpoints. Option A fixture fallback.
  Does not change the engineering telemetry report. Does not close MS5.
related_paths:
  - docs/Project_Contexts/CONTEXT-resilience-pipeline.md
  - data/pipelines/pipeline.py
  - data/pipelines/monthly_clinic_supply/
  - data/raw/monthly_clinic_supply_events.json
  - data/pipelines/PIPELINE_DESIGN.md
  - services/reporting/
  - services/api/app/routers/reporting.py
  - services/api/app/main.py
  - services/api/requirements.txt
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Change services/telemetry/analysis.py or GET /telemetry/report
  - Write KPI rows into telemetry_events
  - Sum USD and GBP into one total
  - Join incident rows or copy patient_id into the pipeline
  - Put ETL logic inside services/reporting route handlers
  - Close MS5 from this stamp
---

# HC-MS5-PLAN-079 — Resilient Monthly Clinic Supply Pipeline Implementation

## Decisions locked

- Entry: `data/pipelines/pipeline.py`.
- Flow: `monthly_clinic_supply_performance`. Tasks: extract, transform, load, plus optional `write_eval_snapshot`.
- Destination: `reporting.monthly_clinic_supply_performance` and `reporting.pipeline_runs` (SQLite local file when no Supabase URI).
- Option A: fixture `data/raw/monthly_clinic_supply_events.json` when the month has no accepted live events.
- Routes: `GET/POST /reporting/pipeline-runs*`, `GET /reporting/monthly-clinic-supply-performance`.
- Rubric eval is shown in chat first; Results file only after human approve.

## Agent instructions

1. Keep handlers thin: import from `data/pipelines/` only.
2. Do not rewrite PLAN-075–078.
3. Do not close MS5 from this stamp.
4. Same-day rubric re-evals, if saved later, overwrite one Results file only.
