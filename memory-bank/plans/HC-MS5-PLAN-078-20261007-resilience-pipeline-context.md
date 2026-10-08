---
stamp: HC-MS5-PLAN-078
sequence: 78
milestone: MS5
date: 2026-10-07
title: HealthCore Resilience Pipeline Context Document
status: implemented
phase: docs
summary: >
  Authored docs/Project_Contexts/CONTEXT-resilience-pipeline.md for Part 2.
  Option A: live telemetry_events first, data/raw fixture when no accepted rows.
  Does not close MS5.
related_paths:
  - docs/Project_Contexts/CONTEXT-resilience-pipeline.md
  - docs/README.md
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Treat this stamp as the Prefect implementation
  - Change services/telemetry/analysis.py or GET /telemetry/report
  - Write pipeline output into telemetry_events
  - Rewrite CONTEXT-data-pipeline.md or PIPELINE_DESIGN intent
  - Close MS5 from this stamp
---

# HC-MS5-PLAN-078 — HealthCore Resilience Pipeline Context Document

## Decisions locked

- Context path: `docs/Project_Contexts/CONTEXT-resilience-pipeline.md`.
- Source strategy is Option A (fixture fallback under `data/raw/`).
- KPI table and routes remain those from PLAN-075 / PLAN-076.
- Implementation is PLAN-079.

## Agent instructions

1. Follow CONTEXT-resilience-pipeline.md and PIPELINE_DESIGN.md.
2. Do not modify the engineering telemetry report.
3. Do not close MS5 from this stamp.
