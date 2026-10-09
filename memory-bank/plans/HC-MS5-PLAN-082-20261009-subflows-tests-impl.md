---
stamp: HC-MS5-PLAN-082
sequence: 82
milestone: MS5
date: 2026-10-09
title: Monthly Clinic Supply Subflows, Tests, and Reporting Dashboard
status: implemented
phase: implementation
summary: >
  Refactor monthly_clinic_supply_performance into domain-named subflows,
  add data/process KPI helpers and tests/pipelines/test_pipeline.py,
  preserve CLI entry, add backoffice /reporting dashboard for all four KPIs.
  Does not change the engineering telemetry report. Does not close MS5.
related_paths:
  - docs/Project_Contexts/CONTEXT-subflows-tests.md
  - data/pipelines/pipeline.py
  - data/pipelines/monthly_clinic_supply/
  - data/process/clinic_supply_kpis.py
  - data/pipelines/PIPELINE_DESIGN.md
  - tests/pipelines/test_pipeline.py
  - uis/backoffice/app/(internal)/reporting/page.tsx
  - uis/backoffice/app/(internal)/layout.tsx
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Change services/telemetry/analysis.py or GET /telemetry/report
  - Write KPI rows into telemetry_events
  - Use generic subflow names like extract_data
  - Put ETL SQL inside the Next.js dashboard
  - Close MS5 from this stamp
  - Save Results without human confirmation
---

# HC-MS5-PLAN-082 — Monthly Clinic Supply Subflows, Tests, and Reporting Dashboard

## Decisions locked

- Main `@flow` lives in `data/pipelines/pipeline.py` and calls ≥3 `@flow` subflows.
- Subflows: `extract_clinic_supply_telemetry`, `transform_monthly_clinic_supply_kpis`, `load_monthly_clinic_supply_performance`, optional `snapshot_monthly_clinic_supply_eval`.
- Pure KPI math in `data/process/clinic_supply_kpis.py` for isolated pytest.
- Dashboard: `uis/backoffice` `/reporting` → JWT `GET /reporting/monthly-clinic-supply-performance`.
- Design Q10 concurrency lock already shipped in Part 2; note in PIPELINE_DESIGN only.
- Chat eval first; Results only after user confirms.

## Agent instructions

1. Keep `services/reporting` handlers thin.
2. Do not rewrite prior stamps.
3. Do not close MS5.
4. Same-day rubric re-evals overwrite one Results file only when approved.
