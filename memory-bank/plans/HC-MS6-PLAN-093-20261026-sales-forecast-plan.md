---
stamp: HC-MS6-PLAN-093
sequence: 93
milestone: MS6
date: 2026-10-26
title: HealthCore Monthly Revenue Forecast Plan
status: planned
phase: planning
summary: >
  Plan for the sales-forecasting challenge on HealthCore consolidated monthly
  revenue. Load the official healthcore_sales.csv (do not simulate). Train
  Random Forest on causal lag, rolling, and calendar features with an 8-year /
  2-year time split. Report test-set MSE, PSI, Gini, and D'Agostino K2.
  Does not close MS6. Eval Results only after human confirm.
related_paths:
  - docs/Project_Contexts/SalesForcasting_.regressiion.md
  - docs/Project_Contexts/healthcore-sales-BRIEFING.en.md
  - CONTEXT-healthcore.md
  - data/raw/healthcore_sales.csv
  - data/process/sales_forecast.py
  - scripts/train_sales_forecast.py
  - tests/pipelines/test_sales_forecast_split.py
  - tests/pipelines/test_sales_forecast_features.py
  - data/eval/sales_forecast/
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Generate or alter healthcore_sales.csv seasonality or growth
  - Use a random train_test_split or shuffle months
  - Feed current-row revenue, visits, or avg revenue per visit into features
  - Fit the scaler on the test years
  - Scale the revenue target (MSE must stay in USD squared)
  - Change telemetry, inventory, Celery, or CONTEXT-healthcore.md for this ticket
  - Save Sales Forecast Results eval without human confirmation
  - Close MS6 from this stamp
---

# HC-MS6-PLAN-093 — Monthly Revenue Forecast Plan

## Problem

Finance (Tom Callahan) asked whether HealthCore can predict coming months' revenue before Dr. Sandra Okonkwo funds a network executive dashboard. The series is monthly and seasonal (flu season October–December, summer drop July–August). A row-wise regression on raw columns would ignore last month, the same month last year, and whether the trend is flattening.

Company intent stays [`CONTEXT-healthcore.md`](../../CONTEXT-healthcore.md): outpatient supplies and operations, no PHI. This ticket uses **aggregated monthly revenue only**. It does not touch patients, inventory routes, or telemetry.

## Locked decisions

| Decision | Choice |
|----------|--------|
| Dataset | Official `healthcore_sales.csv` copied verbatim to `data/raw/healthcore_sales.csv`. Source: syllabus `content/contexts/sales-forecasting/healthcore/`. Do not regenerate. |
| Briefing archive | `docs/Project_Contexts/healthcore-sales-BRIEFING.en.md` (column contract). Do not edit `CONTEXT-healthcore.md`. |
| Grain | One row per month, `region == consolidated`, `2016-01` through `2025-12` (120 months). Target: `revenue_usd`. |
| Split | Train **2016–2023** (first 8 years). Test **2024–2025** (latest 2 years). Chronological. No shuffle. |
| Model | **Random Forest** (`sklearn`, `random_state=42`). Chosen for a ~100-row series and because Sandra and Tom need an explainable feasibility check, not a tuned black box. XGBoost is not trained. |
| Features | Causal only: `revenue_lag_1`, `revenue_lag_12`, `revenue_roll_mean_3` (`shift(1)` then `rolling(3)`), `month`, `quarter`, `month_sin`, `month_cos`. No same-month `visits_count` or `avg_revenue_per_visit_usd`. |
| Nulls | Drop feature-warmup rows (first 12 months) from **training** only. Test months keep lags that look back into 2023 actuals. That lookback is allowed. Test labels never enter training. |
| Scaling | `StandardScaler` on lag and rolling revenue features only. Fit on train, transform test. Do not scale the target. Calendar sin/cos stay unscaled (already on \[-1, 1\]). Trees are split-invariant; scaling is so dollar lags are not compared raw to month indexes if a later linear check is added. |
| Decomposition | `seasonal_decompose` additive, `period=12`, diagnostic only. Note in the report whether October–December is high and July–August is low, matching the briefing. |
| Metrics (test only) | **MSE** in USD² plus RMSE as a percent of average test-month revenue. **PSI** of the predicted-revenue distribution (train scores = expected, test scores = actual, 10 bins). **Gini** = normalized Gini of test predictions vs actual revenue (ranking power for a quiet August vs a real drop). **K2 Score** = D'Agostino K² (`scipy.stats.normaltest`) on test residuals. |
| Variability plot | Mean of the forest's trees, band = ±1 std across trees, vs actual 2024–2025. Save under `data/eval/sales_forecast/`. |
| Code layout | Pure functions in `data/process/sales_forecast.py`. CLI `scripts/train_sales_forecast.py`. Tests in `tests/pipelines/`. Do not add a second root `pipelines/` package beside `data/pipelines/`. |
| Dependencies | `uv add` into a root `pyproject.toml` for `scikit-learn`, `pandas`, `matplotlib`, `statsmodels`, `scipy`. Do not `pip install`. Do not add these to the FastAPI image. |
| Privacy | Aggregates only. No patient identifiers, diagnoses, or member IDs in features, logs, or the plot. |

## Why Random Forest

| Criterion | This series |
|-----------|-------------|
| Data size | 120 months; about 84 trainable rows after the 2016 warmup drop |
| Explainability | Tom and Sandra need feature importances (lag-12, calendar) they can say out loud |
| Tuning time | No budget to tune boosting on fewer than 100 rows without memorizing the past |
| Uncertainty | Tree-to-tree spread is the variability band Finance asked for |

## Implementation phases

1. Archive the sales briefing and place the official CSV at `data/raw/healthcore_sales.csv`.
2. Implement load, null checks, decomposition, causal features, 8/2 split, train-only scaler, forest, and the four test metrics.
3. CLI writes `decomposition.png`, `forecast_vs_actual.png`, and `metrics.md` under `data/eval/sales_forecast/`.
4. Unit tests: disjoint 8-year / 2-year years; `revenue_lag_1` at row t equals raw revenue at t−1; rolling window does not include row t.
5. Document the run command in `scripts/README.md`.

## Out of scope

- Executive dashboard, backoffice page, or API route for the forecast
- Regional 75/25 US/UK split (the file has only `consolidated`)
- XGBoost training, hyperparameter search, or a second model
- Changes to telemetry, inventory, Celery, nightly export, or public/backoffice UI
- Closing MS6
- Writing the Results eval file before human approval

## Agent instructions

1. Execute this plan, then stamp the implementation (next sequence) after files ship.
2. Present the nine “What We Will Evaluate” scores in chat. Write `memory-bank/evaluations/Results/` only after human approval.
3. Do not regenerate `healthcore_sales.csv`.
4. Do not close MS6 from this stamp.
5. Keep revenue errors in dollars a finance lead can read. A low MSE on the training years is not the result.
