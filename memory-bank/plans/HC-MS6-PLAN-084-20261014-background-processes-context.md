---
stamp: HC-MS6-PLAN-084
sequence: 84
milestone: MS6
date: 2026-10-14
title: HealthCore Background Processes Context Archive
status: implemented
phase: docs
summary: >
  Archived BackgroundProcesses.md under docs/Project_Contexts for Ticket #DEV-53
  (nightly telemetry CSV export + pipeline subprocess + job_runs). Locked fit
  decisions for PLAN-085. Does not implement code. Does not close MS6.
related_paths:
  - docs/Project_Contexts/BackgroundProcesses.md
  - BackgroundProcesses.md
  - CONTEXT-healthcore.md
  - docs/README.md
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Treat this stamp as the nightly_export implementation
  - Merge job_runs into pipeline_runs
  - Run the nightly script inside FastAPI lifespan or APScheduler
  - Wire the pipeline to read the CSV export as input
  - Close MS6 from this stamp
---

# HC-MS6-PLAN-084 — HealthCore Background Processes Context Archive

## Decisions locked

- Canonical brief: `docs/Project_Contexts/BackgroundProcesses.md` (plural filename).
- Company parent: `CONTEXT-healthcore.md`.
- `job_runs` is a separate layer from `reporting.pipeline_runs`.
- Pipeline subprocess for this monorepo: `python data/pipelines/pipeline.py` (assignment’s `telemetry_kpi_daily` module does not exist).
- Lock = `processing` status only; idempotency = `(job_name, target_date)` completed.
- Trigger = OS crontab (documented), never FastAPI main thread.
- Implementation follows PLAN-085.

## Agent instructions

1. Do not rewrite this stamp or the archived challenge brief.
2. Implement against BackgroundProcesses.md Acceptance Criteria and “What We Will Evaluate”.
3. Do not close MS6 from this stamp.
4. Eval Results file only after human confirmation (later stamp).
