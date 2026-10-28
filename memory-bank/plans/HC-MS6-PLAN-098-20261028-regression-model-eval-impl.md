---
stamp: HC-MS6-PLAN-098
sequence: 98
milestone: MS6
date: 2026-10-28
title: HealthCore Regression Model Evaluation
status: implemented
phase: implementation
summary: >
  Evaluated the PLAN-095 Random Forest with 5 TimeSeriesSplit folds on
  2016-2023 only. Validation RMSE is 162,325 ± 28,770 USD. The learning
  curve labels the forest overfitting: training RMSE stays at 1.3% while
  validation RMSE flattens at 6.2%. Recommended next change is
  min_samples_leaf=3 and max_depth=6. That change is not applied here.
  Does not close MS6. Results file only after human confirm.
related_paths:
  - docs/Project_Contexts/Evaluating_Regression_Model.md
  - docs/Project_Contexts/healthcore-sales-BRIEFING.en.md
  - data/process/sales_forecast_eval.py
  - scripts/evaluate_regression_model.py
  - tests/pipelines/test_sales_forecast_time_cv.py
  - data/eval/evaluation_report.md
  - data/eval/learning_curve.png
  - data/eval/README.md
  - scripts/README.md
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Apply min_samples_leaf=3 or max_depth=6 inside this stamp
  - Change the target away from revenue_usd
  - Train the evaluation folds on 2024-2025
  - Shuffle months or fit the scaler on a validation window
  - Use visits_count or avg_revenue_per_visit_usd as features
  - Regenerate healthcore_sales.csv
  - Rewrite PLAN-093 through PLAN-097
  - Save the regression-evaluation Results file without human confirmation
  - Close MS6 from this stamp
---

# HC-MS6-PLAN-098 — Regression Model Evaluation

## What shipped

`data/process/sales_forecast_eval.py` scores the unchanged PLAN-095 forest. `scripts/evaluate_regression_model.py` writes `data/eval/learning_curve.png` and `data/eval/evaluation_report.md`. The chronological-order test is `tests/pipelines/test_sales_forecast_time_cv.py`.

Cross-validation is `TimeSeriesSplit` with 5 expanding folds on ready months from 2017-01 through 2023-12. Each fold rebuilds lags from raw months that end on that fold's last validation month. The dollar scaler is fit on the training rows only. 2024–2025 stay out of the folds and out of the curve.

## Result used for the fit call

| Item | Value |
|------|------:|
| Validation RMSE (5 folds) | 162,325 ± 28,770 USD |
| Validation MAE (5 folds) | 138,875 ± 25,883 USD |
| Training RMSE (5 folds) | 40,528 ± 2,755 USD |
| Largest prefix, training RMSE | 1.3% of the 2022-11–2023-12 block |
| Largest prefix, validation RMSE | 6.2% (197,921 USD) |
| Gap at 70 training months | 4.8 points, flat versus 60 months |
| Label | overfitting |
| Stability (dollar CV) | 0.18, marked stable against the 0.25 bar |
| RMSE as % of each fold's own window | 5.6% ± 0.6 points |

The recommended next edit is `min_samples_leaf=3` and `max_depth=6`, with `n_estimators=400` and `random_state=42` kept. This stamp does not apply it.

Pytest on the three forecast test modules: **6 passed**.

## Agent instructions

1. Present the six-item regression rubric in chat. Write `memory-bank/evaluations/Results/` only after human approval.
2. Do not treat the leaf-size recommendation as already applied.
3. Keep 2024–2025 out of the folds and the learning curve.
4. Do not close MS6 from this stamp.
