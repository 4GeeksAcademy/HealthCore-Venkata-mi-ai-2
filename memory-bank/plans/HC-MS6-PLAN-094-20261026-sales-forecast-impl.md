---
stamp: HC-MS6-PLAN-094
sequence: 94
milestone: MS6
date: 2026-10-26
title: HealthCore Monthly Revenue Forecast Implementation
status: implemented
phase: implementation
summary: >
  Trained a seeded Random Forest on the official consolidated series
  data/raw/healthcore_sales.csv. Causal lag, rolling, and calendar features.
  Train 2016-2023, test 2024-2025. Test RMSE is 5.8% of average monthly
  revenue. Gini 0.912. K2 p=0.871. Pytest split and causality tests passed.
  Does not close MS6. Eval Results only after human confirm.
related_paths:
  - docs/Project_Contexts/SalesForcasting_.regressiion.md
  - docs/Project_Contexts/healthcore-sales-BRIEFING.en.md
  - data/raw/healthcore_sales.csv
  - data/process/sales_forecast.py
  - scripts/train_sales_forecast.py
  - tests/pipelines/test_sales_forecast_split.py
  - tests/pipelines/test_sales_forecast_features.py
  - data/eval/sales_forecast/
  - pyproject.toml
  - uv.lock
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Regenerate or edit healthcore_sales.csv
  - Train on 2024-2025 or shuffle the months
  - Use same-month visits or average revenue per visit as model features
  - Fit the scaler on the test years or scale the revenue target
  - Swap this forest for XGBoost without a new justification
  - Change telemetry, inventory, Celery, or CONTEXT-healthcore.md for this ticket
  - Save Sales Forecast Results eval without human confirmation
  - Close MS6 from this stamp
---

# HC-MS6-PLAN-094 — Monthly Revenue Forecast Implementation

## What shipped

- Official series at `data/raw/healthcore_sales.csv` (120 consolidated months, 2016-01 to 2025-12). Not simulated.
- `data/process/sales_forecast.py` — load checks, causal features, 8/2 split, train-only scaler, Random Forest (`random_state=42`), test metrics.
- `scripts/train_sales_forecast.py` — writes `data/eval/sales_forecast/decomposition.png`, `forecast_vs_actual.png`, and `metrics.md`.
- Tests: `tests/pipelines/test_sales_forecast_split.py`, `tests/pipelines/test_sales_forecast_features.py`. Both passed.
- Dependencies via `uv add` in root `pyproject.toml` (`scikit-learn`, `pandas`, `matplotlib`, `statsmodels`, `scipy`; pytest in the dev group).

## Test-set result (2024–2025)

| Metric | Value |
|--------|------:|
| MSE | 38,104,935,066 USD² |
| RMSE | 195,205 USD (5.8% of average test month, 3,366,658 USD) |
| PSI | 0.859 on forecast / same month last year (medians 1.040 train, 1.039 test) |
| Gini | 0.912 |
| K2 Score | 0.276 (D'Agostino, p = 0.871) |

Decomposition matches the briefing: summer seasonal mean is negative, October–December is positive, trend rises.

## Agent instructions

1. Present the nine “What We Will Evaluate” scores in chat. Write Results only after human approval.
2. Do not regenerate `healthcore_sales.csv`.
3. Do not close MS6 from this stamp.
4. Re-run with `uv run python scripts/train_sales_forecast.py` from the repo root.
