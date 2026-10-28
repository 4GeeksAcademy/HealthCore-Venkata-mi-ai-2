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

## Monthly revenue forecast (`train_sales_forecast.py`)

Finance feasibility check for Dr. Okonkwo and Tom Callahan. Loads the official consolidated series `data/raw/healthcore_sales.csv` (no simulated rows). Trains a Random Forest on causal lag, rolling, and calendar features. Train years are 2016–2023. Test years are 2024–2025. Charts and test metrics land in `data/eval/sales_forecast/`.

```bash
# From repo root, after `uv sync`
uv run python scripts/train_sales_forecast.py
```

Column contract: [`docs/Project_Contexts/healthcore-sales-BRIEFING.en.md`](../docs/Project_Contexts/healthcore-sales-BRIEFING.en.md). Company intent stays [`CONTEXT-healthcore.md`](../CONTEXT-healthcore.md). Aggregated revenue only — no patient fields.

## Revenue forecast evaluation (`evaluate_regression_model.py`)

Promotion review of that same forest. Five `TimeSeriesSplit` folds on 2016–2023 only, plus a learning curve. Writes `data/eval/learning_curve.png` and `data/eval/evaluation_report.md`. Does not change the forest and does not fit on 2024–2025.

```bash
# From repo root, after `uv sync`
uv run python scripts/evaluate_regression_model.py
```

Chronological-order test: `tests/pipelines/test_sales_forecast_time_cv.py`. Brief: [`docs/Project_Contexts/Evaluating_Regression_Model.md`](../docs/Project_Contexts/Evaluating_Regression_Model.md).

## Celery async tasks (not a script — see services)

Ticket **#DEV-55** workers are documented in [`services/README.md`](../services/README.md). Start with `docker compose up -d redis worker flower` or `celery -A services.celery_app worker` from the repo root. Do not run the worker inside the FastAPI process.
