---
stamp: HC-MS6-PLAN-085
sequence: 85
milestone: MS6
date: 2026-10-14
title: Nightly Telemetry Export job_runs Implementation
status: implemented
phase: implementation
summary: >
  Implemented Ticket #DEV-53: job_runs schema + services/job_runner status
  machine (processing lock, per-target_date idempotency), scripts/nightly_export.py
  CSV backup + pipeline subprocess, OS crontab docs, pytest suite. Does not
  close MS6. Eval Results only after human confirm.
related_paths:
  - docs/Project_Contexts/BackgroundProcesses.md
  - services/job_runner/
  - scripts/nightly_export.py
  - scripts/README.md
  - tests/jobs/test_nightly_export.py
  - data/raw/README.md
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Merge job_runs into pipeline_runs
  - Schedule nightly_export inside FastAPI lifespan or APScheduler
  - Wire the monthly pipeline to consume data/raw telemetry CSV as input
  - Reintroduce assignment-only telemetry_kpi_daily module
  - Save BackgroundProcesses Results eval without human confirmation
  - Close MS6 from this stamp
---

# HC-MS6-PLAN-085 — Nightly Telemetry Export Implementation

## Decisions locked

- `job_name`: `nightly_export`
- Lock = `status='processing'` only (no second lock table)
- Idempotency = completed row for `(job_name, target_date)`
- CSV path: `data/raw/telemetry_YYYY-MM-DD.csv` (skip if exists)
- Pipeline subprocess: `python data/pipelines/pipeline.py --month-start <first day of target month>`
- Trigger docs: OS crontab `15 2 * * *` UTC (see `scripts/README.md`)
- Tests: `tests/jobs/test_nightly_export.py` (8 cases; `NIGHTLY_SKIP_PIPELINE` for unit runs)

## Agent instructions

1. Do not put cron in `services/api/app/main.py`.
2. Do not change `services/telemetry/analysis.py` or `GET /telemetry/report` for this ticket.
3. Present “What We Will Evaluate” scores in chat; write Results only after human approval.
4. Do not close MS6 from this stamp.
