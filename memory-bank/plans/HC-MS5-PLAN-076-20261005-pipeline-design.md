---
stamp: HC-MS5-PLAN-076
sequence: 76
milestone: MS5
date: 2026-10-05
title: Monthly Clinic Supply Performance Pipeline Design
status: implemented
phase: docs
summary: >
  Design-only business pipeline in data/pipelines/PIPELINE_DESIGN.md.
  Extract, transform, and load for the monthly clinic supply pack.
  No Prefect code and no change to the engineering telemetry report.
related_paths:
  - data/pipelines/PIPELINE_DESIGN.md
  - docs/Project_Contexts/CONTEXT-data-pipeline.md
  - docs/README.md
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Implement Prefect flows, reporting tables, or services/reporting routes from this stamp
  - Change services/telemetry/analysis.py or GET /telemetry/report
  - Write this pipeline's output into telemetry_events
  - Upsert telemetry_events on eventId as part of this pipeline
  - Sum USD and GBP into one total
  - Join incident rows or copy patient_id into the pipeline
  - Rewrite PLAN-075
  - Close MS5 from this stamp
---

# HC-MS5-PLAN-076 — Monthly Clinic Supply Performance Pipeline Design

## Decisions locked

- Canonical design is `data/pipelines/PIPELINE_DESIGN.md`.
- Flow `monthly_clinic_supply_performance`. Tasks `extract_supply_events`, `transform_monthly_clinic_kpis`, `load_monthly_clinic_supply_performance`.
- Dedup key is `tags.eventId` at extract. Load is `ON CONFLICT (clinic_id, month_start) DO UPDATE`.
- Run audit table is `reporting.pipeline_runs`. One `Running` row per flow and `month_start`.
- Routes, design only: `GET /reporting/pipeline-runs/latest`, `POST /reporting/pipeline-runs`, `GET /reporting/monthly-clinic-supply-performance`.
- Part 1 rubric is scored in chat after this stamp. Do not write `memory-bank/evaluations/Results/` until a human asks to save.

## Agent instructions

1. Do not add orchestration code until a later implementation task says to.
2. Keep `services/reporting/` free of ETL. Import functions from `data/pipelines/`.
3. Do not modify the engineering telemetry report.
4. Drop source rows that lack `clinic_id`, a matching `country`, or the event's required properties. Do not guess them.
5. Append a new stamp for implementation. Do not rewrite this file.
6. Do not close MS5 from this stamp.
