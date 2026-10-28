---
stamp: HC-MS6-PLAN-097
sequence: 97
milestone: MS6
date: 2026-10-28
title: HealthCore Regression Model Evaluation Plan
status: planned
phase: planning
summary: >
  Plan for a formal evaluation of the PLAN-095 Random Forest before staging.
  TimeSeriesSplit with 5 folds on the 2016-2023 training window only, scaler
  and lag features rebuilt inside each fold, MAE and RMSE as mean ± sample
  standard deviation, and a learning curve under data/eval/. Diagnosis and
  the corrective action come from the curve. Does not close MS6. Results
  file only after human confirm.
related_paths:
  - docs/Project_Contexts/Evaluating_Regression_Model.md
  - docs/Project_Contexts/healthcore-sales-BRIEFING.en.md
  - data/process/sales_forecast.py
  - data/process/sales_forecast_eval.py
  - scripts/evaluate_regression_model.py
  - tests/pipelines/test_sales_forecast_time_cv.py
  - data/eval/evaluation_report.md
  - data/eval/learning_curve.png
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Change make_model hyperparameters while scoring this ticket
  - Swap the forest for XGBoost
  - Train on 2024-2025 or shuffle months
  - Fit the scaler on a fold's validation rows or on the holdout years
  - Use visits_count or avg_revenue_per_visit_usd as features
  - Build lag or rolling features on the full 2016-2025 series and then slice
  - Regenerate or edit healthcore_sales.csv
  - Rewrite PLAN-093 through PLAN-096
  - Save a regression-evaluation Results file without human confirmation
  - Close MS6 from this stamp
---

# HC-MS6-PLAN-097 — Regression Model Evaluation Plan

## Problem

The PLAN-095 Random Forest already forecasts consolidated `revenue_usd`. A low test RMSE is not a promotion decision. The tech lead wants a formal answer to three questions: is the forest underfit, overfit, or reasonably well fitted; how stable is that error when the training window moves; and, if something is wrong, what single change should happen next.

Company intent stays the sales briefing at [`docs/Project_Contexts/healthcore-sales-BRIEFING.en.md`](../../docs/Project_Contexts/healthcore-sales-BRIEFING.en.md). The series is aggregated monthly revenue for `region = consolidated`. No patient identifiers.

## Locked decisions

| Decision | Choice |
|----------|--------|
| Model under test | `make_model()` as left by PLAN-095: 400 trees, `max_depth=None`, `min_samples_leaf=1`, `random_state=42`. This ticket scores that forest. It does not edit those settings. |
| Target and columns | Target `revenue_usd`. File columns stay `month`, `revenue_usd`, `visits_count`, `avg_revenue_per_visit_usd`, `region`. Features stay the causal set already in `FEATURE_COLUMNS`. |
| Rows in cross-validation | Training years only: 2016–2023, then drop the lag warmup. 2024–2025 never enter a fold, the scaler, or the learning curve. |
| Splitter | `sklearn.model_selection.TimeSeriesSplit` with `n_splits=5`. No shuffle API. Expanding train prefix, contiguous validation block, validation blocks move forward in time. |
| Feature rebuild | For each fold, rebuild lags and the 3-month roll from raw training months that end on that fold's last validation month. Training-row sources for `revenue_lag_1`, `revenue_lag_12`, and `revenue_roll_mean_3` must sit strictly before the validation window. |
| Scaler | `StandardScaler` on `SCALE_COLUMNS` only, fit inside the fold on that fold's training rows. `n_samples_seen_` must equal the training row count. Do not scale `revenue_usd`. |
| Metrics | MAE and RMSE on each fold's training rows and validation rows. Primary metric is **RMSE**. Report each as **mean ± sample standard deviation** (divisor n−1) across the 5 folds, in USD. |
| Why RMSE is primary | The briefing tells Tom Callahan and Dr. Sandra Okonkwo to read squared error in USD² and as a percent of average monthly revenue. RMSE is that squared error in dollars, so a flu-season miss or an atypical drop outweighs a typical month. Ordinary months move about ±5%. MAE stays in the report as the typical absolute miss. |
| Costlier direction | **Overestimating** `revenue_usd`. The briefing's attention case is an atypical drop that looks like a normal low month (August versus a capacity problem). That miss is an overestimate, and it would make the executive-dashboard decision look funded by cash the month did not produce. |
| Learning curve | Growing prefixes of the earliest ready months. Fixed validation block = the last TimeSeriesSplit fold (still inside 2017–2023). Refit the scaler on each prefix. Plot training RMSE and validation RMSE in USD. Save `data/eval/learning_curve.png`. |
| Fit label | Read the largest prefix. Let the percent be RMSE divided by the mean actual `revenue_usd` on that fixed validation block. Ordinary-band ceiling is 8% (past the briefing's ±5% ordinary months). A wide gap is 3 percentage points. **Well fitted:** training and validation both under 8% and the absolute gap under 3 points. **Overfitting:** training under 8% and validation at or above 8%, or the gap at least 3 points. **Underfitting:** training at or above 8%. The largest prefix is the fit call. The 5-fold mean answers stability. |
| Stability | Coefficient of variation of the 5 validation RMSEs above 0.25 means the score moves too much when the training window changes. Folds with fewer than 48 training months (four seasonal cycles) are the short windows. Still publish the 5-fold mean ± std. |
| Corrective action | One action, matched to the label. **Overfitting:** recommend `min_samples_leaf=3` and `max_depth=6`, keep 400 trees and `random_state=42`, then redraw this curve. Do not add trees and do not add 2024–2025 first. **Underfitting:** add a causal `seasonal_index` (month's historical ratio of revenue to `revenue_lag_12`, using only earlier years) and redraw the curve. Do not add years first. **Well fitted and unstable:** promotion uses only folds with at least 48 training months, and the report still shows the 5-fold figure. **Well fitted and stable:** list every 2024–2025 month whose actual `revenue_usd` exceeds the 2016–2023 maximum, for Tom Callahan to review, because a tree cannot print a dollar level above that peak. Do not apply the model change in this ticket. |
| Code layout | Pure functions in `data/process/sales_forecast_eval.py`. CLI `scripts/evaluate_regression_model.py`. Unit test `tests/pipelines/test_sales_forecast_time_cv.py`. Report `data/eval/evaluation_report.md`. |
| Dependencies | `scikit-learn`, `pandas`, `matplotlib`, and `numpy` are already in the root `pyproject.toml`. Do not `pip install`. Do not add them to the FastAPI image. |
| Privacy | Aggregates only. No patient identifiers, diagnoses, or member IDs in the report, the chart, or logs. |

## Implementation phases

1. Add the fold builder, chronological check, per-fold feature prefix, per-fold scaler, and MAE/RMSE scoring. Call `make_model()` unchanged.
2. Add the expanding learning curve and the fit/stability/action rules above.
3. CLI writes `data/eval/learning_curve.png` and `data/eval/evaluation_report.md`.
4. Unit test in `tests/pipelines/`: at least 5 folds; inside each fold the positions and the `month` values are chronological; every training index is before every validation index; concatenating validation indexes in fold order is strictly increasing; a later fold's validation indexes are disjoint from the earlier fold and start after it.
5. Further tests in that file: lag sources for training rows stop before the validation window; the prefix ends before 2024-01; the scaler's `n_samples_seen_` equals the training row count. These tests do not fit the forest.
6. Document the command in `scripts/README.md` and the two artifacts in `data/eval/README.md`.

## Out of scope

- Editing `make_model()`, `metrics.md`, or the 2024–2025 forecast chart
- A backoffice page or an API route for this evaluation
- Changes to telemetry, inventory, Celery, nightly export, or public/backoffice UI
- Closing MS6
- Writing `memory-bank/evaluations/Results/` before human approval

## Agent instructions

1. Implement this plan, then stamp the implementation at the next sequence after the files ship.
2. Present the six “What We Will Evaluate” scores in chat. Write the Results file only after human approval.
3. Keep the fit label tied to the largest learning-curve prefix, and keep the 5-fold mean ± std in the report even when a short fold dominates the spread.
4. Do not regenerate `healthcore_sales.csv` and do not train on 2024–2025.
5. Do not close MS6 from this stamp.
