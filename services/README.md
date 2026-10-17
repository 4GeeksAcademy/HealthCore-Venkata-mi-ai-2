# `services` folder

This folder contains **all the backend services** (APIs and background workers) related to the company for the cross-functional AI Engineering project.

Each subfolder inside `services/` must correspond to **one specific service** (for example: `admin-api`, `data-processor-worker`) and include its own technical and functional documentation.

## Services

| Service | Path | Purpose |
|---------|------|---------|
| Incident Analyzer API | [`api/`](./api/) | FastAPI CSV incident analysis (`POST /api/incidents/analyze`, `GET /api/incidents/results/export`) |
| Celery worker | [`celery_app.py`](./celery_app.py), [`tasks/`](./tasks/) | Ticket `#DEV-55` — async monthly clinic-supply pipeline via Redis |
| Flower | Compose service `flower` | Queue monitor on port `5555` |

- **Main purpose**: to centralize all the backend logic, APIs, and queue consumers that support the company's use cases.
- **Recommendation**: document in this file (or in sub-READMEs) the services you add, their objective, the technology used, and how to run them.

## Celery worker (Ticket #DEV-55)

Requires Redis (`REDIS_URL`, default `redis://127.0.0.1:6379/0`). Broker and result backend are the same Redis instance.

**Start Redis + Flower + worker (Compose):**

```bash
docker compose up -d redis worker flower
# Flower UI: http://127.0.0.1:5555
# Local Flower REST uses FLOWER_UNAUTHENTICATED_API=true (dev only).
```

**Start worker on the host (repo root):**

```bash
# PowerShell
$env:REDIS_URL = "redis://127.0.0.1:6379/0"
$env:PYTHONPATH = "$PWD;$PWD\services;$PWD\data\pipelines"
celery -A services.celery_app worker --loglevel=info --concurrency=1
```

**Stop worker:** Ctrl+C in that terminal, or `docker compose stop worker`.

Stopping the FastAPI `api` container does **not** stop the worker; queued messages remain in Redis until consumed or expired.

`POST /reporting/pipeline-runs` returns `202` + `task_id`. Poll `GET /tasks/{task_id}` for `pending` | `started` | `success` | `failure`. Exhausted failures land in SQL table `task_dead_letters`.

Brief: [`docs/Project_Contexts/MessageQueue.md`](../docs/Project_Contexts/MessageQueue.md).

> _Spanish version: [README.es.md](./README.es.md)._
