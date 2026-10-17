---
stamp: HC-MS6-PLAN-090
sequence: 90
milestone: MS6
date: 2026-10-16
title: HealthCore Message Queue Context Archive
status: implemented
phase: docs
summary: >
  Archived MessageQueue.md under docs/Project_Contexts for Ticket #DEV-55
  (Redis broker, Celery worker, Flower, DLQ, GET /tasks/{task_id}). Locked
  fit decisions for PLAN-091. Does not implement code. Does not close MS6.
related_paths:
  - docs/Project_Contexts/MessageQueue.md
  - MessageQueue.md
  - CONTEXT-healthcore.md
  - docs/README.md
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Treat this stamp as the Celery/Redis implementation
  - Run Celery workers inside the FastAPI process
  - Put large blobs in queue messages
  - Close MS6 from this stamp
---

# HC-MS6-PLAN-090 — HealthCore Message Queue Context Archive

## Decisions locked

- Canonical brief: `docs/Project_Contexts/MessageQueue.md` (also root copy for discoverability).
- Company parent: `CONTEXT-healthcore.md` (clinic-supply telemetry / inventory domain; no PHI in task payloads).
- Ticket: `#DEV-55` — Async Task Queue with Redis and Celery.
- Heavy operation candidate locked in PLAN-091: `POST /reporting/pipeline-runs` (sync Prefect ETL today).
- Implementation follows PLAN-091; eval Results only after human confirmation.

## Agent instructions

1. Do not rewrite this stamp or the archived challenge brief.
2. Implement against MessageQueue.md Acceptance Criteria and “What We Will Evaluate”.
3. Do not close MS6 from this stamp.
4. Eval Results file only after human confirmation (later stamp).
