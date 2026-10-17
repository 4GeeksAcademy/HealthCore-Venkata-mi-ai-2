---
stamp: HC-MS6-PLAN-092
sequence: 92
milestone: MS6
date: 2026-10-16
title: Async Task Queue Redis Celery Implementation
status: implemented
phase: implementation
summary: >
  Implemented Ticket #DEV-55: Redis + Flower + Celery worker in Compose,
  POST /reporting/pipeline-runs returns 202 + task_id, GET /tasks/{task_id},
  retries with exponential backoff, SQL task_dead_letters DLQ, pytest coverage.
  Does not close MS6. Eval Results only after human confirm.
related_paths:
  - docs/Project_Contexts/MessageQueue.md
  - docker-compose.yml
  - services/celery_app.py
  - services/tasks/
  - services/reporting/router.py
  - services/api/app/routers/tasks.py
  - services/api/app/celery_client.py
  - services/api/requirements.txt
  - services/api/tests/test_reporting.py
  - tests/tasks/test_celery_pipeline.py
  - services/README.md
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Run Celery workers inside FastAPI lifespan
  - Put full telemetry batches in Redis messages
  - Merge task_dead_letters into job_runs or pipeline_runs
  - Change GET /telemetry/report or analysis.py for this ticket
  - Save MessageQueue Results eval without human confirmation
  - Close MS6 from this stamp
---

# HC-MS6-PLAN-092 — Message Queue Implementation

## Decisions locked (executed)

- Heavy endpoint: `POST /reporting/pipeline-runs` → Celery `apply_async` → **202** + `task_id`
- Task name: `healthcore.run_monthly_clinic_supply_pipeline` (`month_start` only)
- Status: `GET /tasks/{task_id}` maps Celery states to `pending|started|success|failure`
- Compose: `redis` (6379, `noeviction`), `worker`, `flower` (5555); `REDIS_URL=redis://redis:6379/0`
- DLQ table: `task_dead_letters` via `services/tasks/dlq.py`
- Retries: `max_retries=3`, `retry_countdown = max(2**retries, 1)`
- Tests: reporting enqueue &lt;200ms (mocked broker) + eager completion; `tests/tasks/` for backoff/DLQ

## Agent instructions

1. Do not put the worker inside `services/api/app/main.py`.
2. Present “What We Will Evaluate” scores in chat; write Results only after human approval.
3. Do not close MS6 from this stamp.
4. Same-day MessageQueue re-evals overwrite a single Results file once it exists.
