"""Evaluate the HealthCore revenue forest and write the promotion report.

Run from the repo root:

    uv run python scripts/evaluate_regression_model.py

Reads ``data/raw/healthcore_sales.csv`` only. Writes
``data/eval/learning_curve.png`` and ``data/eval/evaluation_report.md``.
The 2024–2025 holdout is not used to fit or to draw the curve.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

from data.process.sales_forecast import SalesDataError, default_sales_path, load_sales  # noqa: E402
from data.process.sales_forecast_eval import (  # noqa: E402
    EvaluationResult,
    FoldLeakError,
    FoldOrderError,
    render_report,
    run_evaluation,
)


def _save_learning_curve(result: EvaluationResult, path: Path) -> None:
    sizes = [point.train_rows for point in result.curve]
    figure, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    panels = (
        (
            axes[0],
            [point.train_rmse for point in result.curve],
            [point.val_rmse for point in result.curve],
            "RMSE (USD)",
        ),
        (
            axes[1],
            [point.train_mae for point in result.curve],
            [point.val_mae for point in result.curve],
            "MAE (USD)",
        ),
    )
    for axis, train_error, val_error, ylabel in panels:
        axis.plot(sizes, train_error, color="#0f3d5e", marker="o", label="Training error")
        axis.plot(sizes, val_error, color="#0e8a6a", marker="s", label="Validation error")
        axis.set_ylabel(ylabel)
        axis.yaxis.set_major_formatter(FuncFormatter(lambda value, _pos: f"{value:,.0f}"))
        axis.legend(loc="best")
        axis.grid(True, axis="y", alpha=0.3)
    axes[1].set_xlabel("Training months (earliest months only)")
    figure.suptitle(
        f"HealthCore consolidated revenue — learning curve ({result.diagnosis.label})"
    )
    try:
        figure.savefig(path, dpi=120, bbox_inches="tight")
    finally:
        plt.close(figure)


def main() -> int:
    sales_path = default_sales_path(_REPO_ROOT)
    out_dir = _REPO_ROOT / "data" / "eval"
    try:
        frame = load_sales(sales_path)
    except FileNotFoundError:
        print("Sales file not found. Expected data/raw/healthcore_sales.csv.", file=sys.stderr)
        return 1
    except SalesDataError as exc:
        print(f"Sales file is not usable: {exc}", file=sys.stderr)
        return 1

    try:
        result = run_evaluation(frame)
    except (FoldOrderError, FoldLeakError) as exc:
        print(f"Temporal evaluation failed: {exc}", file=sys.stderr)
        return 1

    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        print("Could not create the evaluation folder.", file=sys.stderr)
        return 1

    chart_path = out_dir / "learning_curve.png"
    report_path = out_dir / "evaluation_report.md"
    try:
        _save_learning_curve(result, chart_path)
    except OSError:
        print("Could not write the learning curve.", file=sys.stderr)
        return 1

    try:
        report_path.write_text(render_report(result), encoding="utf-8")
    except OSError:
        print("Could not write the evaluation report.", file=sys.stderr)
        return 1

    diagnosis = result.diagnosis
    print(
        "Diagnosis: {label}. Validation RMSE {mean:,.0f} ± {std:,.0f} USD "
        "(5 folds). Largest prefix: train {train:.1f}%, validation {val:.1f}%.".format(
            label=diagnosis.label,
            mean=result.val_rmse.mean,
            std=result.val_rmse.std,
            train=diagnosis.train_rmse_pct,
            val=diagnosis.val_rmse_pct,
        )
    )
    print("Wrote data/eval/learning_curve.png and data/eval/evaluation_report.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
