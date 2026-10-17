---
stamp: HC-MS6-PLAN-091
sequence: 91
milestone: MS6
date: 2026-10-16
title: Async Task Queue Redis Celery Implementation Plan
status: planned
phase: planning
summary: >
  Plan for Ticket #DEV-55: add Redis + Flower + Celery worker to Compose,
  convert POST /reporting/pipeline-runs to enqueue-and-202, add GET
  /tasks/{task_id}, SQL DLQ after 3 failures with backoff, lightweight
  messages (month_start only). Does not close MS6. Eval Results only after
  human confirm.
related_paths:
  - docs/Project_Contexts/MessageQueue.md
  - CONTEXT-healthcore.md
  - docker-compose.yml
  - services/celery_app.py
  - services/tasks/
  - services/reporting/router.py
  - services/api/requirements.txt
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Run Celery workers inside FastAPI lifespan
  - Put full telemetry batches or CSV blobs in Redis messages
  - Replace job_runs or pipeline_runs with the DLQ table
  - Change GET /telemetry/report or analysis.py for this ticket
  - Save MessageQueue Results eval without human confirmation
  - Close MS6 from this stamp
---

# HC-MS6-PLAN-091 — Message Queue Implementation Plan

## Problem

`POST /reporting/pipeline-runs` runs the monthly clinic-supply Prefect ETL **inside the HTTP request** and returns only after `Completed`. That blocks other API clients. Ticket `#DEV-55` requires producer/broker/consumer separation via Redis + Celery, status polling, retries with backoff, DLQ persistence, and Flower.

## Locked decisions

| Decision | Choice |
|----------|--------|
| Heavy endpoint | `POST /reporting/pipeline-runs` → enqueue Celery task; respond **`202 Accepted`** + `{"task_id": "..."}` |
| Message payload | **`month_start` only** (worker loads telemetry / fixture itself) — HIPAA-safe, no PHI |
| Status API | New **`GET /tasks/{task_id}`** → `{task_id, status, result}` with Celery states mapped to `pending` \| `started` \| `success` \| `failure` |
| Broker / backend | Redis (`REDIS_URL`, default `redis://redis:6379/0`) for broker **and** result backend |
| Compose | Add `redis` (6379, `noeviction`), `flower` (5555), `worker` (separate process); API + worker share `REDIS_URL` |
| Deps | Add `celery`, `redis`, `flower` to `services/api/requirements.txt` (repo uses pip/`uv pip`, not `uv add` project) |
| Celery module | `services/celery_app.py` + task in `services/tasks/pipeline.py` |
| Retries | `max_retries=3`, exponential backoff (`countdown` / `retry_backoff`) — never immediate retry |
| DLQ | SQL table `task_dead_letters` (`task_id`, `attempt`, `error_message`, `created_at`) via SQLAlchemy, same URL family as `job_runs` (`JOB_RUNS_DATABASE_URL` / telemetry / sqlite fallback). **Separate** from `job_runs` and `pipeline_runs` |
| Observability | Structured logs: `task_id`, attempt, status, duration; failures log full error; Flower shows queue |
| Prior evals | Update `services/api/tests/test_reporting.py` for 202 + task poll; keep KPI query assertions. Do not change `GET /telemetry/report` |
| Docs | Document worker start/stop in `services/README.md` and `scripts/README.md` (or root README pointer) |

## Architecture

```
Client → FastAPI (producer) → Redis → Celery worker (consumer) → Prefect ETL
                ↓                              ↓
         GET /tasks/{id}                 task_dead_letters (DLQ)
                ↓
              Flower :5555
```

## Implementation phases

1. **Infrastructure** — Redis + Flower + worker services; `REDIS_URL` on api/worker; volume mounts so worker sees `data/pipelines` and `services/`.
2. **Celery app + task** — configure broker/backend; `run_monthly_clinic_supply_pipeline(month_start)`; retries + DLQ write on exhausted failures; duration logging.
3. **API** — change `POST /reporting/pipeline-runs` to `apply_async` + 202; add tasks router `GET /tasks/{task_id}`; JWT on both (match reporting auth).
4. **Tests** — unit tests with eager/fake broker or redis mock: 202 latency path, status lifecycle mapping, retry backoff config, DLQ row after 3 failures; update reporting integration test.
5. **Docs** — worker/Flower how-to; env var note (no committing secrets).

## Out of scope

- Replacing Prefect retries inside the flow
- Converting `GET /telemetry/report` or nightly_export to Celery
- Closing MS6
- Writing Results eval file before human approval

## Agent instructions

1. Execute this plan; mark implemented via a follow-up stamp (PLAN-092) after code ships.
2. Present “What We Will Evaluate” scores in chat; write Results only after human approval.
3. Do not put the worker inside `services/api/app/main.py` lifespan.
4. Do not close MS6 from this stamp.
