# Regression Model Evaluation

**Date:** 2026-10-28  
**Rubric:** Evaluating a Regression Model — “What We Will Evaluate” (six checks)  
**Implementation as of:** [HC-MS6-PLAN-099](../../plans/HC-MS6-PLAN-099-20261028-lift-forest-eval.md)  
**Saved after:** [HC-MS6-PLAN-100](../../plans/HC-MS6-PLAN-100-20261028-regression-eval-save.md)  
**Overall: PASS (6/6)**

| Doc | Path |
|-----|------|
| Challenge | [`docs/Project_Contexts/Evaluating_Regression_Model.md`](../../../docs/Project_Contexts/Evaluating_Regression_Model.md) |
| Sales briefing | [`docs/Project_Contexts/healthcore-sales-BRIEFING.en.md`](../../../docs/Project_Contexts/healthcore-sales-BRIEFING.en.md) |
| Series | [`data/raw/healthcore_sales.csv`](../../../data/raw/healthcore_sales.csv) |
| Evaluation | [`data/process/sales_forecast_eval.py`](../../../data/process/sales_forecast_eval.py) |
| Script | [`scripts/evaluate_regression_model.py`](../../../scripts/evaluate_regression_model.py) |
| Report | [`data/eval/evaluation_report.md`](../../../data/eval/evaluation_report.md) |
| Chart | [`data/eval/learning_curve.png`](../../../data/eval/learning_curve.png) |
| Prior dollar review | [`data/eval/evaluation_report_dollar.md`](../../../data/eval/evaluation_report_dollar.md) |
| Test | [`tests/pipelines/test_sales_forecast_time_cv.py`](../../../tests/pipelines/test_sales_forecast_time_cv.py) |

Saved after human approval. Same-day regression-model re-evals overwrite this single 2026-10-28 Results file only. Does not close MS6. Does not replace the sales-forecast, pipeline, telemetry, or background-process evals. Aggregated monthly `revenue_usd` only. No patient fields.

The approved model is the yearly-lift forest: it learns `revenue_usd / revenue_lag_12`, and the dollar forecast is that lift times `revenue_lag_12`. Settings are 400 trees, `max_depth=6`, `min_samples_leaf=3`, `random_state=42`. Scores are USD on `revenue_usd`. Folds and the learning curve use 2016–2023 only. The PLAN-095 trainer `make_model()` is unchanged.

## Method

- Re-ran `uv run python -m pytest tests/pipelines/test_sales_forecast_time_cv.py`: **4 passed**, including chronological order, lag-boundary checks, the per-fold scaler row count, and the fit-label rules.
- Read `data/eval/evaluation_report.md` from the lift forest.
- Confirmed `learning_curve.png` plots training and validation RMSE and MAE against the number of earliest training months, and the title states **well fitted**.
- Compared that run with the dollar-target review kept in `evaluation_report_dollar.md`.

## Approved numbers

| Item | Value |
|------|------:|
| Fit label | well fitted |
| Validation RMSE (5 folds) | 131,697 ± 15,999 USD |
| Validation MAE (5 folds) | 106,742 ± 13,492 USD |
| Largest prefix | training 2.1%, validation 4.7% (gap 2.6 points) |
| Fixed block | 2022-11–2023-12, validation RMSE 152,364 USD |
| RMSE vs each fold’s own window | 4.6% ± 0.4 points |
| Stability coefficient | 0.12 |

Primary metric is RMSE. The sales briefing asks Tom Callahan and Dr. Okonkwo to read squared error in dollars. Overestimating `revenue_usd` is the costlier direction, because the briefing’s attention case is an atypical drop that looks like a normal August. On the five validation windows the forecast sits 18,759 USD below actual on average.

## Comparison with the dollar-target review

| | Dollar target, leaf 1 | Yearly lift (approved) |
|--|----------------------:|-----------------------:|
| Fit label | overfitting | well fitted |
| Validation RMSE | 162,325 ± 28,770 USD | 131,697 ± 15,999 USD |
| Gap at the largest prefix | 4.8 points | 2.6 points |

This review is better than that one on the fit label, the five-fold validation RMSE, and the gap.

## Scorecard

| # | Criterion | Result | Evidence |
|---|-----------|--------|----------|
| 1 | Learning curve is generated and the pattern is interpreted | **Pass** | `data/eval/learning_curve.png`. At 70 training months, training RMSE is 2.1% and validation RMSE is 4.7%. The report classifies that pattern as **well fitted**. |
| 2 | Temporal CV keeps order, blocks lag leakage, and reports mean ± std | **Pass** | `TimeSeriesSplit`, 5 expanding folds, features rebuilt through each fold’s last validation month, scaler fit on training rows only. Validation RMSE **131,697 ± 15,999 USD**. 2024–2025 stay out of the folds. |
| 3 | Two metrics, with a business reason for the primary one | **Pass** | MAE and RMSE, training and validation. RMSE is primary because the briefing asks for squared error in dollars. MAE is the typical absolute miss. |
| 4 | Explicit diagnosis backed by the curve and the folds | **Pass** | **Well fitted.** Both errors are under the 8% ceiling and the gap is 2.6 points, under the 3-point bar. |
| 5 | Corrective action matches the diagnosis | **Pass** | Leave leaf size at 3, depth at 6, and 400 trees. Tom Callahan reviews 2024-11, 2024-12, 2025-10, 2025-11, and 2025-12, the months whose actual `revenue_usd` exceeds the 2016–2023 peak of 3,729,681 USD. |
| 6 | Chronological-order unit test passes | **Pass** | Pytest **4 passed** on `tests/pipelines/test_sales_forecast_time_cv.py`. Later validation indexes start after earlier folds, and months inside each fold stay in order. |

## Verdict

The yearly-lift review meets the official regression-evaluation rubric and is the better of the two same-day runs. **PASS (6/6).** Does not close MS6.
