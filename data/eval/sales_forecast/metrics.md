# HealthCore consolidated revenue forecast — test years 2024–2025

Model: Random Forest (`random_state=42`). Target: `revenue_usd`.
Train: 2016–2023 after dropping the 12-month lag warmup. Test: 2024–2025 only.

Decomposition matches the briefing: July-August seasonal mean -487,766 USD, October-December seasonal mean 386,002 USD, trend rises from the first fitted year to the last.

## Why Random Forest

The series has 120 months. After the lag warmup, training is under 100 rows.
XGBoost can chase those rows with sequential corrections and a tuning search
this ticket does not have. Random Forest averages trees, stays explainable for
Tom Callahan and Dr. Okonkwo, and the spread across trees is the variability
band on the chart. Seed is fixed so the same file produces the same report.
Each leaf may be one historical month, so the forecast can reach the strongest
months in the training years. It still cannot print a dollar level above the
2016-2023 peak.

## Test metrics

A low training MSE would only show that the forest remembered 2016-2023.
MSE, Gini, and K2 below use 2024-2025 actuals. PSI compares the training
score shape with the 2024-2025 score shape.

| Metric | Value | What it tells Finance |
|--------|------:|------------------------|
| MSE | 34,099,742,320 USD² | Average squared miss, in dollars squared |
| RMSE | 184,661 USD | Typical miss size (square root of MSE) |
| RMSE vs average month | 5.5% | RMSE as a percent of average test-month revenue (3,366,658 USD) |
| PSI | 0.584 | Shift in forecast / same-month-last-year between training scores and 2024-2025. Under 0.10 is stable. |
| Gini | 0.900 | Whether the model ranks high months above low months. 1 is a perfect order. |
| K2 Score | 0.247 | D'Agostino K² on test residuals (p = 0.884). A large score means the errors are skewed, not a tidy bell. |

Why MSE alone is not enough: a model can sit close to the average dollar level
and still rank August like October, or drift when the visit mix moves. Gini
checks the order Sandra needs (a normal summer dip versus a real drop). PSI
compares forecast / same-month-last-year. The training median lift is
1.039 and the test median lift is 1.037
(about 4% above last year, the briefing growth rate). A PSI above 0.25 here
means a few test months sit further from last year than the training months
did. It does not mean the center of the forecast broke, and it is not a US/UK
mix shift: the file has only consolidated rows. PSI on average revenue per
visit is 0.449. That yield stays in the same band (about 169-191 USD)
in both periods. K² checks whether the remaining errors are lopsided.

## Feature importances (training fit)

| Feature | Importance |
|---------|----------:|
| `revenue_lag_12` | 0.939 |
| `revenue_lag_1` | 0.029 |
| `revenue_roll_mean_3` | 0.014 |
| `month_sin` | 0.006 |
| `month_cos` | 0.006 |
| `month_of_year` | 0.004 |
| `quarter` | 0.002 |

Lag and rolling features were shifted before they were rolled, so a month never
sees its own revenue. Calendar features (month, quarter, sin/cos) are known
before the month happens. Same-month visits are not used.
