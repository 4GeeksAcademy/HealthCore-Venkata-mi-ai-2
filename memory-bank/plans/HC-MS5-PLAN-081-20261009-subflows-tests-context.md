---
stamp: HC-MS5-PLAN-081
sequence: 81
milestone: MS5
date: 2026-10-09
title: HealthCore Subflows and Tests Context Document
status: implemented
phase: docs
summary: >
  Docs-only brief for Part 3: subflows, unit tests, CLI preserve, and
  backoffice reporting dashboard. Does not implement code. Does not close MS5.
related_paths:
  - docs/Project_Contexts/CONTEXT-subflows-tests.md
  - docs/Project_Contexts/CONTEXT-healthcore.md
  - docs/Project_Contexts/CONTEXT-data-pipeline.md
  - docs/Project_Contexts/CONTEXT-resilience-pipeline.md
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Implement Prefect code from this stamp alone
  - Change services/telemetry/analysis.py or GET /telemetry/report
  - Write KPI rows into telemetry_events
  - Close MS5 from this stamp
---

# HC-MS5-PLAN-081 — HealthCore Subflows and Tests Context Document

## Decisions locked

- Brief path: `docs/Project_Contexts/CONTEXT-subflows-tests.md`.
- Parent company context: CONTEXT-healthcore.md; KPI names from CONTEXT-data-pipeline.md.
- Part 3 phases: subflows → unit tests → CLI → `/reporting` dashboard.
- Rubric Results file only after human confirmation (later stamp).

## Agent instructions

1. Do not rewrite PLAN-075–080.
2. Do not close MS5 from this stamp.
3. Implementation follows PLAN-082.
