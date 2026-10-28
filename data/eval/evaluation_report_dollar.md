# HealthCore consolidated revenue forecast — technical evaluation

Promotion review of the existing Random Forest before staging. The forest is the PLAN-095 model: `n_estimators=400`, `max_depth=None`, `min_samples_leaf=1`, `random_state=42`. This run does not change those settings and does not fit a second algorithm.

Target: `revenue_usd`. Series: `region = consolidated` in `data/raw/healthcore_sales.csv`, columns `month`, `revenue_usd`, `visits_count`, `avg_revenue_per_visit_usd`, and `region`. Same-month `visits_count` and `avg_revenue_per_visit_usd` are not features. Cross-validation and the learning curve use 2016–2023 only, after the 12-month lag warmup (ready months start in 2017). The 2024–2025 holdout stays outside every fold, every scaler, and the curve.

## Metric choice

**Primary metric: RMSE.** The sales briefing asks Tom Callahan and Dr. Sandra Okonkwo to read squared error in USD² and as a percent of average monthly revenue. RMSE is that squared error back in dollars. A flu-season month (October–December, about 15–20% above the year's average) or an atypical drop therefore counts more than an ordinary month, which the briefing puts at about ±5% around the trend.

**Companion metric: MAE.** MAE is the typical absolute miss in USD, so Finance can read an ordinary month without the square.

**Costlier direction: overestimating `revenue_usd`.** The briefing's attention case for Dr. Okonkwo is an atypical drop that looks like a normal low month — August versus a clinical capacity problem Marcus Reid would need to see. That miss is an overestimate of a weak month. It also makes the executive-dashboard decision look funded by cash the month did not produce. Underestimating the October–December lift is a staffing miss, and the squared metric still charges that large miss. The direction named for the go/no-go is the unseen drop.

On the five validation windows pooled together, predicted `revenue_usd` sits **below** actual by **84,760 USD** on average (predicted minus actual: -84,760 USD). **19%** of absolute validation error comes from months the forest set too high.

## Time-aware cross-validation

`TimeSeriesSplit` with 5 folds. The splitter has no shuffle. Each training window starts at the earliest ready month and expands. Each validation window is the next contiguous block. Fold features are rebuilt from raw 2016–2023 months that end on that fold's last validation month, so a later fold is not in the frame. For every training row, `revenue_lag_1`, `revenue_lag_12`, and `revenue_roll_mean_3` use only months before the validation window. A validation row may use an earlier month inside its own window (one-step score). It may not use the next fold. The dollar scaler is fit on that fold's training rows only (`n_samples_seen_` equals the training row count). `revenue_usd` is not scaled.

| Fold | Training months | Validation months | Train rows | Train MAE (USD) | Train RMSE (USD) | Val MAE (USD) | Val RMSE (USD) | Val RMSE vs that window |
|------|-----------------|-------------------|----------:|----------------:|-----------------:|--------------:|---------------:|-----------------------:|
| 1 | 2017-01–2018-02 | 2018-03–2019-04 | 14 | 39,459 | 43,259 | 106,282 | 122,868 | 4.7% |
| 2 | 2017-01–2019-04 | 2019-05–2020-06 | 28 | 29,417 | 37,241 | 138,939 | 161,532 | 5.9% |
| 3 | 2017-01–2020-06 | 2020-07–2021-08 | 42 | 31,336 | 38,337 | 121,115 | 149,233 | 5.3% |
| 4 | 2017-01–2021-08 | 2021-09–2022-10 | 56 | 33,386 | 40,575 | 159,688 | 180,070 | 6.0% |
| 5 | 2017-01–2022-10 | 2022-11–2023-12 | 70 | 35,120 | 43,230 | 168,349 | 197,921 | 6.2% |

Sample standard deviation uses divisor n−1.

| Metric | Training | Validation |
|--------|----------|------------|
| MAE | **33,744 ± 3,847 USD** | **138,875 ± 25,883 USD** |
| RMSE | **40,528 ± 2,755 USD** | **162,325 ± 28,770 USD** |

Primary number: validation RMSE **162,325 ± 28,770 USD**.

Stability: validation RMSE runs from **122,868 USD** on the lowest fold to **197,921 USD** on the highest. The coefficient of variation is **0.18**. The bar for a stable promotion score is 0.25, so the five-fold dollar score is **stable**. As a percent of each fold's own average validation `revenue_usd`, RMSE is **5.6% ± 0.6 points**. The shortest window is fold 1, with 14 training months (2017-01–2018-02). Folds with at least 48 training months (folds 4, 5): validation RMSE **188,996 ± 12,623 USD**.

## Learning curve

Chart: `data/eval/learning_curve.png`. The top panel is RMSE and the bottom panel is MAE. Both panels plot training error and validation error against the number of earliest training months.

The validation block is fixed: **2022-11–2023-12**, the last TimeSeriesSplit fold, still inside 2017–2023. Percents use that block's average actual `revenue_usd` (**3,212,674 USD**). Each prefix refits the scaler. The full prefix matches the last fold's validation RMSE, which is the check that the curve and the cross-validation share one window.

| Training months | Train MAE | Train RMSE | Val MAE | Val RMSE | Train RMSE % | Val RMSE % |
|----------------:|----------:|-----------:|--------:|---------:|-------------:|-----------:|
| 28 | 29,417 | 37,241 | 442,630 | 492,475 | 1.2% | 15.3% |
| 38 | 27,447 | 33,499 | 251,543 | 307,436 | 1.0% | 9.6% |
| 49 | 32,223 | 38,956 | 244,784 | 289,380 | 1.2% | 9.0% |
| 60 | 33,862 | 40,709 | 169,866 | 198,793 | 1.3% | 6.2% |
| 70 | 35,120 | 43,230 | 168,349 | 197,921 | 1.3% | 6.2% |

## Diagnosis

The model is **overfitting**.

At 49 training months the gap is 7.8 percentage points (validation RMSE 9.0% of the fixed block's average `revenue_usd`, training RMSE 1.2%). At 70 training months the gap is 4.8 percentage points (validation 6.2%, training 1.3%). The fit call uses this largest prefix. The ordinary-band ceiling is 8% and a wide gap is 3 points. The five-fold mean is the stability number, not a second fit label. Validation RMSE on that prefix is inside the 8% ceiling. The label stays overfitting because the training line stays near the leaf floor and the gap is still at least 3 points.

The chart shows the same pattern: read the two RMSE lines at the right-hand side of `data/eval/learning_curve.png`. Training RMSE there is 1.3% of the fixed block and validation RMSE is 6.2%.

## Corrective action

Training RMSE stays on the floor of the curve at every prefix. That is the leaf rule in `make_model()`: `min_samples_leaf=1` and `max_depth=None` let one training month occupy a leaf. Validation RMSE falls as the prefix grows, then flattens while the gap is still wide, so another slice of the same history is not the first fix. Set `min_samples_leaf=3` and `max_depth=6`, keep `n_estimators=400` and `random_state=42`, and redraw this learning curve before staging. Keep the tree count at 400. Keep 2024–2025 out of that refit. On this series, validation RMSE is 198,793 USD at 60 training months and 197,921 USD at 70 training months (6.2% of the fixed block). Training RMSE at that prefix is 43,230 USD (1.3%).

Months in 2024–2025 whose actual `revenue_usd` exceeds the 2016–2023 peak of 3,729,681 USD: 2024-11, 2024-12, 2025-10, 2025-11, 2025-12. Those actuals are a staging list. They are not rows in the fit, the folds, or the curve.

## What this run kept fixed

The run leaves `make_model()` as specified in PLAN-095. It leaves 2024–2025 out of training. It leaves `visits_count` and `avg_revenue_per_visit_usd` out of the features. Months stay in calendar order. The report uses aggregated `revenue_usd` only.
