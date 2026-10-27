"""Train the HealthCore consolidated revenue forecast and write the test report.

Run from the repo root:

    uv run python scripts/train_sales_forecast.py

Reads ``data/raw/healthcore_sales.csv`` only. Writes charts and ``metrics.md``
under ``data/eval/sales_forecast/``. Metrics are for 2024–2025, the two years
the forest did not train on.
"""

from __future__ import annotations

import statistics
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from data.process.sales_forecast import (  # noqa: E402
    FEATURE_COLUMNS,
    TARGET_COLUMN,
    SalesDataError,
    build_features,
    decomposition_frame,
    default_sales_path,
    evaluate_on_test,
    load_sales,
    make_model,
    population_stability_index,
    rows_ready_for_model,
    scale_feature_frames,
    seasonality_note,
    split_by_year,
    tree_prediction_band,
)


def _write_metrics(
    path: Path,
    metrics,
    note: str,
    importances: list[tuple[str, float]],
    yield_psi: float,
    train_lift_median: float,
    test_lift_median: float,
) -> None:
    ranked = "\n".join(
        f"| `{name}` | {score:.3f} |" for name, score in importances
    )
    # A small MSE on the years the model already saw is not the decision.
    # PSI, Gini, and the K² residual check say whether 2024–2025 still look
    # like the history Tom and Sandra would budget from.
    body = f"""# HealthCore consolidated revenue forecast — test years 2024–2025

Model: Random Forest (`random_state=42`). Target: `revenue_usd`.
Train: 2016–2023 after dropping the 12-month lag warmup. Test: 2024–2025 only.

{note}

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
| MSE | {metrics.mse:,.0f} USD² | Average squared miss, in dollars squared |
| RMSE | {metrics.rmse:,.0f} USD | Typical miss size (square root of MSE) |
| RMSE vs average month | {metrics.rmse_pct_of_avg_revenue:.1f}% | RMSE as a percent of average test-month revenue ({metrics.avg_test_revenue_usd:,.0f} USD) |
| PSI | {metrics.psi:.3f} | Shift in forecast / same-month-last-year between training scores and 2024-2025. Under 0.10 is stable. |
| Gini | {metrics.gini:.3f} | Whether the model ranks high months above low months. 1 is a perfect order. |
| K2 Score | {metrics.k2_statistic:.3f} | D'Agostino K² on test residuals (p = {metrics.k2_pvalue:.3f}). A large score means the errors are skewed, not a tidy bell. |

Why MSE alone is not enough: a model can sit close to the average dollar level
and still rank August like October, or drift when the visit mix moves. Gini
checks the order Sandra needs (a normal summer dip versus a real drop). PSI
compares forecast / same-month-last-year. The training median lift is
{train_lift_median:.3f} and the test median lift is {test_lift_median:.3f}
(about 4% above last year, the briefing growth rate). A PSI above 0.25 here
means a few test months sit further from last year than the training months
did. It does not mean the center of the forecast broke, and it is not a US/UK
mix shift: the file has only consolidated rows. PSI on average revenue per
visit is {yield_psi:.3f}. That yield stays in the same band (about 169-191 USD)
in both periods. K² checks whether the remaining errors are lopsided.

## Feature importances (training fit)

| Feature | Importance |
|---------|----------:|
{ranked}

Lag and rolling features were shifted before they were rolled, so a month never
sees its own revenue. Calendar features (month, quarter, sin/cos) are known
before the month happens. Same-month visits are not used.
"""
    path.write_text(body, encoding="utf-8")


def _save_decomposition(frame: pd.DataFrame, path: Path) -> None:
    parts = decomposition_frame(frame)
    figure = parts.plot()
    figure.set_size_inches(10, 8)
    figure.suptitle("HealthCore consolidated revenue — trend, seasonality, residual")
    try:
        figure.savefig(path, dpi=120, bbox_inches="tight")
    finally:
        plt.close(figure)


def _save_forecast(test: pd.DataFrame, center, lower, upper, path: Path) -> None:
    months = pd.to_datetime(test["month"])
    figure, axis = plt.subplots(figsize=(10, 5))
    axis.plot(months, test[TARGET_COLUMN], label="Actual revenue", color="#0f3d5e")
    axis.plot(months, center, label="Forecast", color="#0e8a6a")
    axis.fill_between(months, lower, upper, color="#0e8a6a", alpha=0.25, label="Tree variability (±1 std)")
    axis.set_title("HealthCore consolidated revenue — 2024–2025 forecast")
    axis.set_ylabel("Revenue (USD)")
    axis.set_xlabel("Month")
    axis.legend(loc="upper left")
    axis.figure.autofmt_xdate()
    try:
        figure.savefig(path, dpi=120, bbox_inches="tight")
    finally:
        plt.close(figure)


def main() -> int:
    sales_path = default_sales_path(_REPO_ROOT)
    out_dir = _REPO_ROOT / "data" / "eval" / "sales_forecast"
    try:
        frame = load_sales(sales_path)
    except FileNotFoundError:
        print("Sales file not found. Expected data/raw/healthcore_sales.csv.", file=sys.stderr)
        return 1
    except SalesDataError as exc:
        print(f"Sales file is not usable: {exc}", file=sys.stderr)
        return 1

    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        print("Could not create the forecast output folder.", file=sys.stderr)
        return 1

    note = seasonality_note(frame["revenue_usd"], pd.DatetimeIndex(frame["month"]))
    try:
        _save_decomposition(frame, out_dir / "decomposition.png")
    except OSError:
        print("Could not write the decomposition chart.", file=sys.stderr)
        return 1
    except ValueError:
        print("Could not decompose the monthly revenue series.", file=sys.stderr)
        return 1

    raw_train, raw_test = split_by_year(frame)
    yield_psi = population_stability_index(
        raw_train["avg_revenue_per_visit_usd"].to_numpy(),
        raw_test["avg_revenue_per_visit_usd"].to_numpy(),
    )
    featured = build_features(frame)
    train, test = split_by_year(featured)
    train_ready = rows_ready_for_model(train)
    test_ready = rows_ready_for_model(test)
    if train_ready.empty or test_ready.empty:
        print("Not enough complete months to train and check the forecast.", file=sys.stderr)
        return 1
    if int(test_ready["month"].dt.year.min()) < 2024:
        print("Test frame includes a training year.", file=sys.stderr)
        return 1

    train_scaled, test_scaled, _scaler = scale_feature_frames(train_ready, test_ready)
    model = make_model()
    x_train = train_scaled.loc[:, list(FEATURE_COLUMNS)].to_numpy()
    x_test = test_scaled.loc[:, list(FEATURE_COLUMNS)].to_numpy()
    model.fit(x_train, train_scaled[TARGET_COLUMN].to_numpy())
    train_pred = model.predict(x_train)
    test_pred = model.predict(x_test)
    # Dollar levels rise every year. PSI on forecast / last year's same month
    # asks whether the seasonal lift moved, which is the stability question.
    train_index = train_pred / train_ready["revenue_lag_12"].to_numpy()
    test_index = test_pred / test_ready["revenue_lag_12"].to_numpy()
    metrics = evaluate_on_test(
        train_index,
        test_scaled[TARGET_COLUMN].to_numpy(),
        test_pred,
        psi_actual=test_index,
    )
    center, lower, upper = tree_prediction_band(model, test_scaled)

    try:
        _save_forecast(test_ready, center, lower, upper, out_dir / "forecast_vs_actual.png")
    except OSError:
        print("Could not write the forecast chart.", file=sys.stderr)
        return 1

    importances = sorted(
        zip(FEATURE_COLUMNS, model.feature_importances_, strict=True),
        key=lambda item: item[1],
        reverse=True,
    )
    try:
        _write_metrics(
            out_dir / "metrics.md",
            metrics,
            note,
            importances,
            yield_psi,
            statistics.median(train_index),
            statistics.median(test_index),
        )
    except OSError:
        print("Could not write the metrics report.", file=sys.stderr)
        return 1

    print(note)
    print(
        "Test MSE {mse:,.0f} USD^2; RMSE {rmse:.1f}% of average month; "
        "PSI {psi:.3f}; Gini {gini:.3f}; K2 {k2:.3f}.".format(
            mse=metrics.mse,
            rmse=metrics.rmse_pct_of_avg_revenue,
            psi=metrics.psi,
            gini=metrics.gini,
            k2=metrics.k2_statistic,
        )
    )
    print(f"Wrote {out_dir / 'metrics.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
