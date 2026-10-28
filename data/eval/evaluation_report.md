# HealthCore consolidated revenue forecast — technical evaluation

Promotion review of the yearly-lift forest before staging. The forest learns `revenue_usd / revenue_lag_12`. The dollar forecast is that lift times `revenue_lag_12`. Settings: `n_estimators=400`, `max_depth=6`, `min_samples_leaf=3`, `random_state=42`. Errors below are USD on `revenue_usd`. The PLAN-095 trainer `make_model()` is a separate dollar forest and is not the model scored here.

Target: `revenue_usd`. Series: `region = consolidated` in `data/raw/healthcore_sales.csv`, columns `month`, `revenue_usd`, `visits_count`, `avg_revenue_per_visit_usd`, and `region`. Same-month `visits_count` and `avg_revenue_per_visit_usd` are not features. Cross-validation and the learning curve use 2016–2023 only, after the 12-month lag warmup (ready months start in 2017). The 2024–2025 holdout stays outside every fold, every scaler, and the curve.

## Metric choice

**Primary metric: RMSE.** The sales briefing asks Tom Callahan and Dr. Sandra Okonkwo to read squared error in USD² and as a percent of average monthly revenue. RMSE is that squared error back in dollars. A flu-season month (October–December, about 15–20% above the year's average) or an atypical drop therefore counts more than an ordinary month, which the briefing puts at about ±5% around the trend.

**Companion metric: MAE.** MAE is the typical absolute miss in USD, so Finance can read an ordinary month without the square.

**Costlier direction: overestimating `revenue_usd`.** The briefing's attention case for Dr. Okonkwo is an atypical drop that looks like a normal low month — August versus a clinical capacity problem Marcus Reid would need to see. That miss is an overestimate of a weak month. It also makes the executive-dashboard decision look funded by cash the month did not produce. Underestimating the October–December lift is a staffing miss, and the squared metric still charges that large miss. The direction named for the go/no-go is the unseen drop.

On the five validation windows pooled together, predicted `revenue_usd` sits **below** actual by **18,759 USD** on average (predicted minus actual: -18,759 USD). **41%** of absolute validation error comes from months the forest set too high.

## Time-aware cross-validation

`TimeSeriesSplit` with 5 folds. The splitter has no shuffle. Each training window starts at the earliest ready month and expands. Each validation window is the next contiguous block. Fold features are rebuilt from raw 2016–2023 months that end on that fold's last validation month, so a later fold is not in the frame. For every training row, `revenue_lag_1`, `revenue_lag_12`, and `revenue_roll_mean_3` use only months before the validation window. A validation row may use an earlier month inside its own window (one-step score). It may not use the next fold. The dollar scaler is fit on that fold's training rows only (`n_samples_seen_` equals the training row count). `revenue_usd` is not scaled.

| Fold | Training months | Validation months | Train rows | Train MAE (USD) | Train RMSE (USD) | Val MAE (USD) | Val RMSE (USD) | Val RMSE vs that window |
|------|-----------------|-------------------|----------:|----------------:|-----------------:|--------------:|---------------:|-----------------------:|
| 1 | 2017-01–2018-02 | 2018-03–2019-04 | 14 | 45,907 | 60,499 | 92,739 | 112,228 | 4.3% |
| 2 | 2017-01–2019-04 | 2019-05–2020-06 | 28 | 47,468 | 61,281 | 106,722 | 126,854 | 4.7% |
| 3 | 2017-01–2020-06 | 2020-07–2021-08 | 42 | 48,633 | 61,341 | 113,056 | 143,205 | 5.1% |
| 4 | 2017-01–2021-08 | 2021-09–2022-10 | 56 | 54,851 | 68,662 | 95,390 | 123,835 | 4.1% |
| 5 | 2017-01–2022-10 | 2022-11–2023-12 | 70 | 54,533 | 68,081 | 125,802 | 152,364 | 4.7% |

Sample standard deviation uses divisor n−1.

| Metric | Training | Validation |
|--------|----------|------------|
| MAE | **50,278 ± 4,145 USD** | **106,742 ± 13,492 USD** |
| RMSE | **63,973 ± 4,035 USD** | **131,697 ± 15,999 USD** |

Primary number: validation RMSE **131,697 ± 15,999 USD**.

Stability: validation RMSE runs from **112,228 USD** on the lowest fold to **152,364 USD** on the highest. The coefficient of variation is **0.12**. The bar for a stable promotion score is 0.25, so the five-fold dollar score is **stable**. As a percent of each fold's own average validation `revenue_usd`, RMSE is **4.6% ± 0.4 points**. The shortest window is fold 1, with 14 training months (2017-01–2018-02). Folds with at least 48 training months (folds 4, 5): validation RMSE **138,099 ± 20,173 USD**.

## Learning curve

Chart: `data/eval/learning_curve.png`. The top panel is RMSE and the bottom panel is MAE. Both panels plot training error and validation error against the number of earliest training months.

The validation block is fixed: **2022-11–2023-12**, the last TimeSeriesSplit fold, still inside 2017–2023. Percents use that block's average actual `revenue_usd` (**3,212,674 USD**). Each prefix refits the scaler. The full prefix matches the last fold's validation RMSE, which is the check that the curve and the cross-validation share one window.

| Training months | Train MAE | Train RMSE | Val MAE | Val RMSE | Train RMSE % | Val RMSE % |
|----------------:|----------:|-----------:|--------:|---------:|-------------:|-----------:|
| 28 | 47,468 | 61,281 | 92,393 | 118,844 | 1.9% | 3.7% |
| 38 | 42,816 | 52,907 | 97,789 | 111,653 | 1.6% | 3.5% |
| 49 | 50,031 | 64,849 | 113,506 | 142,147 | 2.0% | 4.4% |
| 60 | 51,864 | 66,607 | 105,431 | 125,549 | 2.1% | 3.9% |
| 70 | 54,533 | 68,081 | 125,802 | 152,364 | 2.1% | 4.7% |

## Diagnosis

The model is **well fitted**.

At 49 training months the gap is 2.4 percentage points (validation RMSE 4.4% of the fixed block's average `revenue_usd`, training RMSE 2.0%). At 70 training months the gap is 2.6 percentage points (validation 4.7%, training 2.1%). The fit call uses this largest prefix. The ordinary-band ceiling is 8% and a wide gap is 3 points. The five-fold mean is the stability number, not a second fit label.

The chart shows the same pattern: read the two RMSE lines at the right-hand side of `data/eval/learning_curve.png`. Training RMSE there is 2.1% of the fixed block and validation RMSE is 4.7%.

## Corrective action

The learning curve supports staging this forest. Leave `min_samples_leaf` at 3, `max_depth` at 6, and `n_estimators` at 400. Before promotion, Tom Callahan reviews these 2024–2025 months, whose actual `revenue_usd` exceeds the 2016–2023 peak of 3,729,681 USD: 2024-11, 2024-12, 2025-10, 2025-11, 2025-12. Those months stayed out of the fit.

Months in 2024–2025 whose actual `revenue_usd` exceeds the 2016–2023 peak of 3,729,681 USD: 2024-11, 2024-12, 2025-10, 2025-11, 2025-12. Those actuals are a staging list. They are not rows in the fit, the folds, or the curve.

## Comparison with the dollar-target evaluation

The previous review scored a dollar-target forest (`max_depth=None`, `min_samples_leaf=1`) on these same folds and this same fixed block. That write-up is `data/eval/evaluation_report_dollar.md`. Its chart is `data/eval/learning_curve_dollar.png`.

This review is **better** than that one. The fit label moves from **overfitting** to **well fitted**. The five-fold validation RMSE moves by **30,628 USD** (positive means this run is lower). The fixed-block validation RMSE moves by **45,557 USD**. The learning-curve gap moves by **2.2** points.

| | Dollar target, leaf 1 | Yearly lift, leaf 3, depth 6 |
|--|----------------------:|-----------------------------:|
| Fit label | overfitting | well fitted |
| Validation RMSE | 162,325 ± 28,770 USD | 131,697 ± 15,999 USD |
| Validation MAE | 138,875 ± 25,883 USD | 106,742 ± 13,492 USD |
| Training RMSE | 40,528 USD | 63,973 USD |
| Largest prefix, training RMSE | 1.3% | 2.1% |
| Largest prefix, validation RMSE | 6.2% (197,921 USD) | 4.7% (152,364 USD) |
| Gap at the largest prefix | 4.8 points | 2.6 points |
| RMSE vs each fold's own window | 5.6% ± 0.6 points | 4.6% ± 0.4 points |
| Stability coefficient | 0.18 | 0.12 |

## What this run kept fixed

The run leaves the PLAN-095 `make_model()` trainer unchanged. It leaves 2024–2025 out of training. It leaves `visits_count` and `avg_revenue_per_visit_usd` out of the features. Months stay in calendar order. The scored target in dollars is still `revenue_usd`. The report uses aggregated revenue only.
