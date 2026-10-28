# `data/eval` folder

This folder is for **evaluation and validation**: evaluation datasets, golden sets, experiment results, metrics, and artifacts used to measure quality for models, RAG, agents, or pipelines.

- **Main purpose**: centralize evaluation inputs and outputs so improvements stay measurable across project milestones.
- **Recommendation**: document each evaluation set (what it measures, how it was built, success criteria) and avoid sensitive data; use synthetic or anonymized data when needed.

> _Spanish version: [README.es.md](./README.es.md)._

## Sales forecast artifacts (`sales_forecast/`)

`scripts/train_sales_forecast.py` writes three files here after a run:

- `decomposition.png` — trend, seasonality, and residual for consolidated monthly revenue (diagnostic, not the model).
- `forecast_vs_actual.png` — 2024–2025 forecast with the tree-to-tree variability band against actual revenue.
- `metrics.md` — test-set MSE, PSI, Gini, and D'Agostino K².

`scripts/evaluate_regression_model.py` writes the promotion review next to that folder:

- `learning_curve.png` — training and validation MAE and RMSE for the yearly-lift forest.
- `evaluation_report.md` — five-fold mean ± standard deviation, the fit label, and the comparison with the dollar-target run.
- `learning_curve_dollar.png` and `evaluation_report_dollar.md` — the earlier dollar-target forest (leaf size 1).

Numbers are aggregates. They are not a patient record.
