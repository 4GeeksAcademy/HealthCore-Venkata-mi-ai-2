"""Temporal cross-validation keeps month order and keeps later folds out of earlier lags."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from data.process.sales_forecast import (  # noqa: E402
    FEATURE_COLUMNS,
    load_sales,
    scale_feature_frames,
    split_by_year,
)
from data.process.sales_forecast_eval import (  # noqa: E402
    CurvePoint,
    as_month,
    assert_training_lags_stop_before,
    assert_windows_chronological,
    classify_fit,
    corrective_action,
    features_through,
    fold_windows,
    raw_prefix_through,
    training_ready_frame,
)


def _point(train_pct: float, val_pct: float, rows: int) -> CurvePoint:
    return CurvePoint(
        train_rows=rows,
        train_mae=0.0,
        train_rmse=0.0,
        val_mae=0.0,
        val_rmse=0.0,
        train_rmse_pct=train_pct,
        val_rmse_pct=val_pct,
    )


def test_temporal_cv_preserves_chronological_order():
    ready = training_ready_frame(load_sales())
    months = list(ready["month"])
    windows = fold_windows(len(ready))
    assert_windows_chronological(windows, months)

    assert len(windows) >= 5
    assert as_month(months[0]) >= pd.Timestamp("2017-01-01")
    assert as_month(months[-1]) < pd.Timestamp("2024-01-01")
    assert [as_month(month) for month in months] == sorted(as_month(month) for month in months)

    concatenated = []
    previous_val_max = -1
    for window in windows:
        train = window.train_positions
        val = window.val_positions
        assert list(train) == sorted(train)
        assert list(val) == sorted(val)
        assert train[-1] < val[0]
        train_months = [as_month(months[index]) for index in train]
        val_months = [as_month(months[index]) for index in val]
        assert train_months == sorted(train_months)
        assert val_months == sorted(val_months)
        assert train_months[-1] < val_months[0]
        assert val[0] > previous_val_max
        previous_val_max = val[-1]
        concatenated.extend(val)

    assert concatenated == sorted(concatenated)
    for earlier, later in zip(windows, windows[1:]):
        earlier_idx = set(earlier.train_positions) | set(earlier.val_positions)
        assert set(later.val_positions).isdisjoint(earlier_idx)
        assert min(later.val_positions) > max(earlier.val_positions)
        assert min(later.train_positions) >= min(earlier.train_positions)


def test_lag_features_do_not_cross_the_fold_boundary():
    frame = load_sales()
    raw_train, raw_test = split_by_year(frame)
    ready = training_ready_frame(frame)
    assert "visits_count" not in FEATURE_COLUMNS
    assert "avg_revenue_per_visit_usd" not in FEATURE_COLUMNS
    assert set(ready["month"]).isdisjoint(set(raw_test["month"]))

    revenue = {as_month(month): float(value) for month, value in zip(raw_train["month"], raw_train["revenue_usd"])}
    for window in fold_windows(len(ready)):
        last = ready.iloc[window.val_positions[-1]]["month"]
        val_start = as_month(ready.iloc[window.val_positions[0]]["month"])
        raw_prefix = raw_prefix_through(raw_train, last)
        prefix = features_through(raw_train, last)
        assert as_month(prefix["month"].iloc[-1]) == as_month(last)
        assert as_month(prefix["month"].max()) < pd.Timestamp("2024-01-01")
        assert set(prefix["month"]).isdisjoint(set(raw_test["month"]))
        train_rows = prefix.iloc[list(window.train_positions)]
        assert_training_lags_stop_before(raw_prefix, train_rows, val_start)
        for _, row in train_rows.iterrows():
            month = as_month(row["month"])
            prior = as_month(month - pd.DateOffset(months=1))
            assert prior < val_start
            assert row["revenue_lag_1"] == pytest.approx(revenue[prior])
            for step in (1, 2, 3):
                assert as_month(month - pd.DateOffset(months=step)) < val_start


def test_scaler_sees_only_the_fold_training_rows():
    frame = load_sales()
    raw_train, _raw_test = split_by_year(frame)
    ready = training_ready_frame(frame)
    for window in fold_windows(len(ready)):
        last = ready.iloc[window.val_positions[-1]]["month"]
        prefix = features_through(raw_train, last)
        train_df = prefix.iloc[list(window.train_positions)]
        val_df = prefix.iloc[list(window.val_positions)]
        _train_scaled, _val_scaled, scaler = scale_feature_frames(train_df, val_df)
        assert int(scaler.n_samples_seen_) == len(window.train_positions)
        assert int(scaler.n_samples_seen_) != len(window.train_positions) + len(window.val_positions)


def test_fit_label_follows_the_learning_curve_rules():
    overfitting = [
        _point(6.0, 14.0, 28),
        _point(3.0, 11.0, 49),
        _point(2.0, 9.0, 70),
    ]
    underfitting = [
        _point(14.0, 15.0, 28),
        _point(11.0, 12.0, 70),
    ]
    fitted = [
        _point(6.0, 7.0, 28),
        _point(4.0, 5.0, 70),
    ]
    assert classify_fit(overfitting) == "overfitting"
    assert classify_fit(underfitting) == "underfitting"
    assert classify_fit(fitted) == "well fitted"

    over_action = corrective_action("overfitting", stable=False, peak=1_000.0, months_above=["2025-10"])
    under_action = corrective_action("underfitting", stable=True, peak=1_000.0, months_above=["2025-10"])
    unstable_action = corrective_action("well fitted", stable=False, peak=3_000_000.0, months_above=["2025-06"])
    stable_action = corrective_action(
        "well fitted", stable=True, peak=3_729_681.0, months_above=["2025-06"]
    )
    assert "min_samples_leaf=3" in over_action
    assert "max_depth=6" in over_action
    assert "seasonal_index" in under_action
    assert "48" in unstable_action
    assert "min_samples_leaf=3" not in unstable_action
    assert "2025-06" in stable_action
    assert "3,729,681" in stable_action
