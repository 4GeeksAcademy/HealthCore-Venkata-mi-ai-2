# Sales Forecast Evaluation

**Date:** 2026-10-26  
**Rubric:** Sales forecasting “What We Will Evaluate” (nine checks)  
**Implementation as of:** [HC-MS6-PLAN-095](../../plans/HC-MS6-PLAN-095-20261026-sales-forecast-tighter.md)  
**Saved after:** [HC-MS6-PLAN-096](../../plans/HC-MS6-PLAN-096-20261026-sales-forecast-eval.md)  
**Overall: PASS (9/9)**

| Doc | Path |
|-----|------|
| Challenge | [`docs/Project_Contexts/SalesForcasting_.regressiion.md`](../../../docs/Project_Contexts/SalesForcasting_.regressiion.md) |
| Sales briefing | [`docs/Project_Contexts/healthcore-sales-BRIEFING.en.md`](../../../docs/Project_Contexts/healthcore-sales-BRIEFING.en.md) |
| Company | [`CONTEXT-healthcore.md`](../../../CONTEXT-healthcore.md) |
| Series | [`data/raw/healthcore_sales.csv`](../../../data/raw/healthcore_sales.csv) |
| Model | [`data/process/sales_forecast.py`](../../../data/process/sales_forecast.py) |
| Script | [`scripts/train_sales_forecast.py`](../../../scripts/train_sales_forecast.py) |
| Report | [`data/eval/sales_forecast/metrics.md`](../../../data/eval/sales_forecast/metrics.md) |
| Chart | [`data/eval/sales_forecast/forecast_vs_actual.png`](../../../data/eval/sales_forecast/forecast_vs_actual.png) |
| Tests | [`tests/pipelines/test_sales_forecast_split.py`](../../../tests/pipelines/test_sales_forecast_split.py), [`test_sales_forecast_features.py`](../../../tests/pipelines/test_sales_forecast_features.py) |

Saved after human approval. Same-day re-evals overwrite this single 2026-10-26 Results file only. Does not close MS6. Does not replace pipeline, telemetry, or background-process evals. Aggregated monthly revenue only. No patient fields.

## Method

- Re-ran `uv run python -m pytest tests/pipelines/test_sales_forecast_split.py tests/pipelines/test_sales_forecast_features.py`: **2 passed**.
- Read `data/eval/sales_forecast/metrics.md` from the PLAN-095 forest (400 trees, `min_samples_leaf=1`, `random_state=42`).
- Confirmed `forecast_vs_actual.png` draws actual revenue, the forecast, and a ±1 tree-standard-deviation band for 2024–2025.
- Confirmed the series check in `load_sales`: 120 consolidated months, 2016-01 through 2025-12, positive revenue.

## Test-set numbers (2024–2025)

| Metric | Value |
|--------|------:|
| MSE | 34,099,742,320 USD² |
| RMSE | 184,661 USD (5.5% of average test-month revenue, 3,366,658 USD) |
| PSI | 0.584 (forecast / same month last year; medians 1.039 train, 1.037 test) |
| Gini | 0.900 |
| K2 Score | 0.247 (D'Agostino, p = 0.884) |

## Scorecard

| # | Criterion | Result | Evidence |
|---|-----------|--------|----------|
| 1 | 8-year / 2-year split, no mixed months | **Pass** | Train 2016–2023 (96 months), test 2024–2025 (24 months), disjoint. Unit test asserts both year sets and no shared month. |
| 2 | Lag, rolling, and calendar features used in training | **Pass** | `revenue_lag_1`, `revenue_lag_12`, `revenue_roll_mean_3`, `month_of_year`, `quarter`, `month_sin`, `month_cos` are the fit columns. Lag-12 importance 0.939. |
| 3 | Lag and rolling features are causal | **Pass** | `shift(1)` before the 3-month roll. Unit test: lag at t equals revenue at t−1; the roll excludes month t. |
| 4 | Random Forest or XGBoost, choice justified | **Pass** | Random Forest. Justification in `sales_forecast.py` and `metrics.md`: short series, Finance needs an explainable check, tree spread is the variability band. |
| 5 | MSE, PSI, Gini, and K2 on the test set | **Pass** | All four are in `metrics.md` for 2024–2025. Training MSE is not the reported result. PSI uses the training score shape as the reference and the test scores as the actual distribution. |
| 6 | Chart shows a variability range | **Pass** | `forecast_vs_actual.png` fills ±1 standard deviation across trees around the forecast, against actual revenue. |
| 7 | Official series, seasonality and growth left intact | **Pass** | `data/raw/healthcore_sales.csv` loaded as provided. Decomposition: July–August seasonal mean about −488,000 USD, October–December about +386,000 USD, trend rises. |
| 8 | Fixed random seed | **Pass** | `SEED = 42` on `RandomForestRegressor`. |
| 9 | Both unit tests pass | **Pass** | Pytest **2 passed** on 2026-10-26. |

## Residuals (do not fail the rubric)

- PSI 0.584 is above the 0.25 rule of thumb. The medians of forecast / same-month-last-year match (1.039 and 1.037). The file has only `consolidated` rows, so this is not a US/UK mix shift.
- Five months in 2025 are above the 2016–2023 peak (3,729,681 USD). The tree forecast cannot print a dollar level above that peak. Test RMSE is 5.5% of an average test month.
- The 12-month lag warmup drops early 2016 from the fit. Those months stay inside the training window. The split itself is still eight years versus two.

## Verdict

The Finance feasibility forecast meets the official sales-forecasting rubric. **PASS (9/9).** Does not close MS6.
