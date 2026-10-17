# `scripts` folder

This folder contains **helper scripts** for the monorepo: development automation, maintenance utilities, repetitive tasks (setup, lint, migrations, data generation, etc.), and internal tooling.

- **Main purpose**: group support tools that do not belong to a specific app, agent, or pipeline but make the team’s work easier.
- **Recommendation**: document each script (what it does, parameters, requirements, usage examples) and keep them reproducible (and safe) across environments.

> _Spanish version: [README.es.md](./README.es.md)._

## Nightly telemetry export (`nightly_export.py`)

Ticket **#DEV-53** — independent process (not FastAPI). Status control: `services/job_runner` → table `job_runs` (separate from `pipeline_runs`).

```bash
# From repo root
python scripts/nightly_export.py
TARGET_DATE=2026-10-13 python scripts/nightly_export.py
NIGHTLY_SKIP_PIPELINE=1 TARGET_DATE=2026-10-13 python scripts/nightly_export.py
```

**Cron (OS crontab, UTC recommended — do not schedule inside the API process):**

```cron
15 2 * * * cd /path/to/HealthCore-Venkata-mi-ai-2 && /usr/bin/env python scripts/nightly_export.py >> /var/log/healthcore-nightly.log 2>&1
```

Justification: crontab keeps the worker off the FastAPI main thread so a hung export cannot block `/health` or inventory routes. CSV lands in `data/raw/telemetry_YYYY-MM-DD.csv` (backup only). Pipeline subprocess: `python data/pipelines/pipeline.py --month-start <first-of-target-month>`.

Brief: [`docs/Project_Contexts/BackgroundProcesses.md`](../docs/Project_Contexts/BackgroundProcesses.md).

## Celery async tasks (not a script — see services)

Ticket **#DEV-55** workers are documented in [`services/README.md`](../services/README.md). Start with `docker compose up -d redis worker flower` or `celery -A services.celery_app worker` from the repo root. Do not run the worker inside the FastAPI process.
