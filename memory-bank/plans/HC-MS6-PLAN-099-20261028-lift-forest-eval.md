---
stamp: HC-MS6-PLAN-099
sequence: 99
milestone: MS6
date: 2026-10-28
title: Yearly Lift Forest Evaluation
status: implemented
phase: implementation
summary: >
  Re-scored the promotion review on a yearly-lift forest (depth 6, leaf size 3).
  The fit label is well fitted. Five-fold validation RMSE is 131,697 ± 15,999 USD,
  down from 162,325 ± 28,770 USD on the dollar-target forest. The dollar-target
  report is kept beside it. make_model() is unchanged. Does not close MS6.
  Results file only after human confirm.
related_paths:
  - data/process/sales_forecast_eval.py
  - scripts/evaluate_regression_model.py
  - data/eval/evaluation_report.md
  - data/eval/learning_curve.png
  - data/eval/evaluation_report_dollar.md
  - data/eval/learning_curve_dollar.png
  - data/eval/README.md
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Point this review back at the leaf-1 dollar forest without a new stamp
  - Change make_model() in data/process/sales_forecast.py from this stamp
  - Train the evaluation folds on 2024-2025
  - Shuffle months or fit the scaler on a validation window
  - Use visits_count or avg_revenue_per_visit_usd as features
  - Regenerate healthcore_sales.csv
  - Rewrite PLAN-093 through PLAN-098
  - Save the regression-evaluation Results file without human confirmation
  - Close MS6 from this stamp
---

# HC-MS6-PLAN-099 — Yearly Lift Forest Evaluation

## What changed

The evaluation forest now learns `revenue_usd / revenue_lag_12` and turns that lift back into dollars with `revenue_lag_12`. Tree settings are 400 trees, `max_depth=6`, `min_samples_leaf=3`, `random_state=42`. The PLAN-095 trainer `make_model()` is still the dollar forest and is not called by this review.

The earlier review is preserved at `data/eval/evaluation_report_dollar.md` and `data/eval/learning_curve_dollar.png`.

## Comparison

| | Dollar target (PLAN-098) | Yearly lift (this stamp) |
|--|-------------------------:|-------------------------:|
| Fit label | overfitting | well fitted |
| Validation RMSE | 162,325 ± 28,770 USD | 131,697 ± 15,999 USD |
| Largest-prefix gap | 4.8 points (1.3% vs 6.2%) | 2.6 points (2.1% vs 4.7%) |

Pytest on `tests/pipelines/test_sales_forecast_time_cv.py`: **4 passed**.

## Agent instructions

1. Treat the yearly-lift report as the current promotion review. Keep the dollar-target files as the comparison baseline.
2. Present rubric scores in chat. Write `memory-bank/evaluations/Results/` only after human approval.
3. Do not edit `make_model()` from this stamp.
4. Do not close MS6 from this stamp.
