---
stamp: HC-MS5-PLAN-075
sequence: 75
milestone: MS5
date: 2026-10-05
title: HealthCore Business Performance Pipeline Context Document
status: implemented
phase: docs
summary: >
  Authored docs/Project_Contexts/CONTEXT-data-pipeline.md. Docs only.
  Monthly Clinic Supply Performance Report for Dr. Okonkwo and Claire.
  Does not add Prefect code, reporting tables, or telemetry report changes.
related_paths:
  - docs/Project_Contexts/CONTEXT-data-pipeline.md
  - docs/README.md
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Treat this stamp as data/pipelines/PIPELINE_DESIGN.md or as orchestration code
  - Change services/telemetry/analysis.py or GET /telemetry/report
  - Write this pipeline's output into telemetry_events
  - Put patient identifiers, staff email, or order notes in pipeline output or logs
  - Invent clinic ids outside scripts/samples/incidents-healthcore.csv
  - Rewrite CONTEXT-healthcore.md or prior stamps
  - Close MS5 from this stamp
---

# HC-MS5-PLAN-075 — HealthCore Business Performance Pipeline Context Document

## Decisions locked

- Context path: `docs/Project_Contexts/CONTEXT-data-pipeline.md`.
- Deliverable is the Monthly Clinic Supply Performance Report. Destination table is `reporting.monthly_clinic_supply_performance`. Unique key is `(clinic_id, month_start)`.
- KPIs are Supply Cost per Clinic, Supply Consumption Volume, Critical Stockout Frequency, and Expiry Risk Count.
- Source events are `inbound_order_created`, `outbound_order_created`, `stock_threshold_triggered`, and `supply_expiry_flagged`. `telemetry_events` is read-only.
- `clinic_id` values are the distinct ids in `scripts/samples/incidents-healthcore.csv`. Currency is `USD` for `US` and `GBP` for `UK`, with no FX conversion.
- This stamp does not write the design document. That is PLAN-076.

## Agent instructions

1. Follow `docs/Project_Contexts/CONTEXT-data-pipeline.md` and `data/pipelines/PIPELINE_DESIGN.md` before any pipeline code.
2. Do not modify `services/telemetry/analysis.py` or `GET /telemetry/report`.
3. Do not write KPI rows into `telemetry_events`.
4. Do not add emitters, Prefect flows, or `services/reporting/` routes until a later implementation task says to.
5. Do not rewrite this stamp when the design or the implementation ships. Append a new stamp.
6. Do not close MS5 from this stamp.
