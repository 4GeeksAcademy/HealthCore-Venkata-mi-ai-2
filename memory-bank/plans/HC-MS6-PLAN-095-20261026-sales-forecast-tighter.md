---
stamp: HC-MS6-PLAN-095
sequence: 95
milestone: MS6
date: 2026-10-26
title: Tighter Random Forest Revenue Forecast
status: implemented
phase: implementation
summary: >
  Same Random Forest, same revenue_usd target, same 8/2 split, same causal
  features. Leaves may be one training month and the forest uses 400 trees
  so the forecast can reach the strongest 2016-2023 months. Test RMSE moved
  from 5.8% to 5.5% of average monthly revenue. Does not close MS6.
related_paths:
  - data/process/sales_forecast.py
  - scripts/train_sales_forecast.py
  - data/eval/sales_forecast/metrics.md
  - data/eval/sales_forecast/forecast_vs_actual.png
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Change the target away from revenue_usd
  - Swap the forest for XGBoost
  - Add same-month visits or a non-causal feature to chase 2025 peaks
  - Regenerate healthcore_sales.csv
  - Train on 2024-2025
  - Save Sales Forecast Results eval without human confirmation
  - Close MS6 from this stamp
---

# HC-MS6-PLAN-095 — Tighter Random Forest Revenue Forecast

## What changed

`make_model()` now uses 400 trees, unlimited depth, and `min_samples_leaf=1`, still with `random_state=42`. Features, split, scaler, and target are unchanged from PLAN-094.

Five test months in 2025 are above every training month (training peak 3,729,681 USD, test peak 4,037,367 USD). A tree cannot forecast a dollar level above that peak. This stamp does not change the target to chase those months.

## Test-set result (2024–2025)

| Metric | Before | After |
|--------|-------:|------:|
| RMSE | 195,205 USD (5.8%) | 184,661 USD (5.5%) |
| PSI | 0.859 | 0.584 |
| Gini | 0.912 | 0.900 |
| K2 | 0.276 (p = 0.871) | 0.247 (p = 0.884) |

Pytest split and causality tests still pass.

## Agent instructions

1. Keep the target as `revenue_usd` on the official consolidated series.
2. Do not treat a further RMSE drop as a reason to switch algorithms or leak future rows.
3. Present updated scores in chat. Write Results only after human approval.
4. Do not close MS6 from this stamp.
