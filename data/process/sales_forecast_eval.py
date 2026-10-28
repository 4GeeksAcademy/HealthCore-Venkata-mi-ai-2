"""Formal evaluation of the HealthCore consolidated revenue forest.

The forest under test learns the yearly lift, ``revenue_usd / revenue_lag_12``,
then the dollar forecast is that lift times ``revenue_lag_12``. Errors in this
report are still in USD on ``revenue_usd``. The tree is 400 trees, depth 6,
leaf size 3, seed 42. ``make_model()`` in the monthly trainer stays the
PLAN-095 dollar forest and is not called here.

Cross-validation uses only 2016–2023. The 2024–2025 holdout stays out of every
fold, every scaler, and the learning curve. Each fold rebuilds lag and rolling
features from raw months that end on that fold's last validation month, then
fits the dollar scaler on the training rows alone.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import TimeSeriesSplit

from data.process.sales_forecast import (
    FEATURE_COLUMNS,
    SEED,
    TARGET_COLUMN,
    build_features,
    rows_ready_for_model,
    scale_feature_frames,
    split_by_year,
)

N_SPLITS = 5
# Ordinary months in the sales briefing move about ±5% around the trend.
# 8% is past that band, so both curves sitting there means the season was missed.
ORDINARY_BAND_PCT = 8.0
# A 3 point gap is wider than a small residual inside that band and narrower
# than the briefing's 12–18% summer drop, so it marks generalization.
WIDE_GAP_PCT = 3.0
# Validation RMSE std / mean above this means the score depends on the window.
STABILITY_CV = 0.25
# Four seasonal cycles. revenue_lag_12 needs a prior year; a promotion vote
# needs several repeats of flu season and the summer drop.
MIN_STABLE_TRAIN_MONTHS = 48
HOLDOUT_START = pd.Timestamp("2024-01-01")
EVAL_TREES = 400
EVAL_MAX_DEPTH = 6
EVAL_MIN_SAMPLES_LEAF = 3
# Dollar-target forest from the first promotion review (leaf size 1, unlimited depth).
PRIOR_LABEL = "overfitting"
PRIOR_VAL_RMSE_MEAN = 162_325.0
PRIOR_VAL_RMSE_STD = 28_770.0
PRIOR_VAL_MAE_MEAN = 138_875.0
PRIOR_VAL_MAE_STD = 25_883.0
PRIOR_TRAIN_RMSE_MEAN = 40_528.0
PRIOR_TRAIN_RMSE_PCT = 1.3
PRIOR_VAL_RMSE_PCT = 6.2
PRIOR_GAP_PCT = 4.8
PRIOR_BLOCK_VAL_RMSE = 197_921.0
PRIOR_FOLD_PCT_MEAN = 5.6
PRIOR_FOLD_PCT_STD = 0.6
PRIOR_STABILITY_CV = 0.18


class FoldOrderError(Exception):
    """A time-series fold was empty, short, or out of chronological order."""


class FoldLeakError(Exception):
    """A fold could see a later month through a lag, a roll, or the scaler."""


@dataclass(frozen=True)
class FoldWindow:
    fold_number: int
    train_positions: tuple[int, ...]
    val_positions: tuple[int, ...]


@dataclass(frozen=True)
class FoldScore:
    fold_number: int
    train_rows: int
    val_rows: int
    train_start: str
    train_end: str
    val_start: str
    val_end: str
    train_mae: float
    train_rmse: float
    val_mae: float
    val_rmse: float
    val_mean_revenue: float
    scaler_rows: int


@dataclass(frozen=True)
class CurvePoint:
    train_rows: int
    train_mae: float
    train_rmse: float
    val_mae: float
    val_rmse: float
    train_rmse_pct: float
    val_rmse_pct: float


@dataclass(frozen=True)
class Spread:
    mean: float
    std: float


@dataclass(frozen=True)
class Diagnosis:
    label: str
    stable: bool
    rationale: str
    action: str
    train_rmse_pct: float
    val_rmse_pct: float
    gap_pct: float


@dataclass(frozen=True)
class EvaluationResult:
    folds: tuple[FoldScore, ...]
    curve: tuple[CurvePoint, ...]
    diagnosis: Diagnosis
    train_mae: Spread
    train_rmse: Spread
    val_mae: Spread
    val_rmse: Spread
    stability_cv: float
    long_window_rmse: Spread | None
    long_window_folds: tuple[int, ...]
    baseline_revenue_usd: float
    validation_mean_signed_error: float
    overestimate_abs_share: float
    train_peak_usd: float
    months_above_peak: tuple[str, ...]
    curve_val_start: str
    curve_val_end: str


def as_month(value) -> pd.Timestamp:
    stamp = pd.Timestamp(value)
    return pd.Timestamp(year=int(stamp.year), month=int(stamp.month), day=1)


def month_label(value) -> str:
    return as_month(value).strftime("%Y-%m")


def training_ready_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """2017–2023 rows whose lags were built from 2016–2023 only."""
    raw_train, _raw_test = split_by_year(frame)
    ready = rows_ready_for_model(build_features(raw_train))
    if ready.empty:
        raise FoldOrderError("No training months remain after the lag warmup.")
    return ready.reset_index(drop=True)


def fold_windows(n_rows: int, n_splits: int = N_SPLITS) -> list[FoldWindow]:
    """Expanding TimeSeriesSplit windows. The splitter does not shuffle."""
    if n_splits < N_SPLITS:
        raise FoldOrderError("Cross-validation needs at least 5 folds.")
    if n_rows < n_splits + 1:
        raise FoldOrderError("Not enough months for 5 chronological folds.")
    splitter = TimeSeriesSplit(n_splits=n_splits)
    windows: list[FoldWindow] = []
    for number, (train_idx, val_idx) in enumerate(splitter.split(np.arange(n_rows)), start=1):
        windows.append(
            FoldWindow(
                fold_number=number,
                train_positions=tuple(int(index) for index in train_idx),
                val_positions=tuple(int(index) for index in val_idx),
            )
        )
    return windows


def assert_windows_chronological(windows: list[FoldWindow], months: list) -> None:
    """Reject a shuffled fold or a later validation block that starts too early."""
    if len(windows) < N_SPLITS:
        raise FoldOrderError("Cross-validation needs at least 5 folds.")
    ordered_months = [as_month(month) for month in months]
    previous_val_max = -1
    concatenated_val: list[int] = []
    previous_train_len = 0
    for window in windows:
        train = window.train_positions
        val = window.val_positions
        if not train or not val:
            raise FoldOrderError("A fold is missing training or validation months.")
        if list(train) != sorted(train) or list(val) != sorted(val):
            raise FoldOrderError("A fold was shuffled.")
        if train != tuple(range(train[0], train[-1] + 1)):
            raise FoldOrderError("Training positions are not a contiguous block.")
        if val != tuple(range(val[0], val[-1] + 1)):
            raise FoldOrderError("Validation positions are not a contiguous block.")
        if train[0] != 0:
            raise FoldOrderError("The training window does not start at the earliest month.")
        if train[-1] >= val[0]:
            raise FoldOrderError("A training month is not before the validation window.")
        if len(train) < previous_train_len:
            raise FoldOrderError("A later fold trains on an earlier slice than the fold before it.")
        if val[0] <= previous_val_max:
            raise FoldOrderError("A later fold starts before an earlier fold.")
        train_months = [ordered_months[index] for index in train]
        val_months = [ordered_months[index] for index in val]
        if train_months != sorted(train_months) or val_months != sorted(val_months):
            raise FoldOrderError("Months inside a fold are out of chronological order.")
        if train_months[-1] >= val_months[0]:
            raise FoldOrderError("A training month is not before the validation month.")
        previous_val_max = val[-1]
        previous_train_len = len(train)
        concatenated_val.extend(val)
    if concatenated_val != sorted(concatenated_val):
        raise FoldOrderError("An index from a later fold appears before an earlier fold.")
    for earlier, later in zip(windows, windows[1:]):
        earlier_idx = set(earlier.train_positions) | set(earlier.val_positions)
        if set(later.val_positions) & earlier_idx:
            raise FoldOrderError("A later validation month appears inside an earlier fold.")
        if min(later.val_positions) <= max(earlier.val_positions):
            raise FoldOrderError("A later fold's validation index is not after the earlier fold.")


def raw_prefix_through(raw_train: pd.DataFrame, last_month) -> pd.DataFrame:
    """Raw training months up to and including the fold's last validation month."""
    last = as_month(last_month)
    prefix = raw_train.loc[raw_train["month"].map(as_month) <= last].copy()
    prefix = prefix.sort_values("month").reset_index(drop=True)
    if prefix.empty or as_month(prefix["month"].iloc[-1]) != last:
        raise FoldLeakError("Fold prefix does not end on the validation window.")
    months = [as_month(month) for month in prefix["month"]]
    if months != sorted(months):
        raise FoldOrderError("Fold prefix is not chronological.")
    if len(months) != len(set(months)):
        raise FoldOrderError("Fold prefix repeats a month.")
    if months[-1] >= HOLDOUT_START:
        raise FoldLeakError("Fold prefix includes a 2024–2025 holdout month.")
    return prefix


def features_through(raw_train: pd.DataFrame, last_month) -> pd.DataFrame:
    """Causal features for one fold. Later folds are not in this frame."""
    prefix = raw_prefix_through(raw_train, last_month)
    ready = rows_ready_for_model(build_features(prefix))
    if ready.empty:
        raise FoldLeakError("Fold prefix has no rows after the lag warmup.")
    if as_month(ready["month"].iloc[-1]) > as_month(last_month):
        raise FoldLeakError("Ready rows passed the validation window.")
    if as_month(ready["month"].max()) >= HOLDOUT_START:
        raise FoldLeakError("Ready rows include a holdout year.")
    return ready.reset_index(drop=True)


def _revenue_lookup(raw_prefix: pd.DataFrame) -> dict[pd.Timestamp, float]:
    return {
        as_month(month): float(revenue)
        for month, revenue in zip(raw_prefix["month"], raw_prefix["revenue_usd"], strict=True)
    }


def assert_training_lags_stop_before(
    raw_prefix: pd.DataFrame, train_rows: pd.DataFrame, val_start
) -> None:
    """Training lags and the 3-month roll stop before the validation window."""
    start = as_month(val_start)
    lookup = _revenue_lookup(raw_prefix)
    if train_rows.empty:
        raise FoldLeakError("A fold has no training rows to check.")
    for _, row in train_rows.iterrows():
        month = as_month(row["month"])
        if month >= start:
            raise FoldLeakError("A training row sits inside the validation window.")
        sources = [as_month(month - pd.DateOffset(months=k)) for k in (1, 2, 3, 12)]
        for source in sources:
            if source >= start:
                raise FoldLeakError("A lag source crosses the validation window.")
            if source not in lookup:
                raise FoldLeakError("A lag source month is missing from this fold prefix.")
        prior = as_month(month - pd.DateOffset(months=1))
        year_ago = as_month(month - pd.DateOffset(months=12))
        if not math.isclose(float(row["revenue_lag_1"]), lookup[prior], rel_tol=0, abs_tol=0.01):
            raise FoldLeakError("revenue_lag_1 is not the prior month inside this fold.")
        if not math.isclose(float(row["revenue_lag_12"]), lookup[year_ago], rel_tol=0, abs_tol=0.01):
            raise FoldLeakError("revenue_lag_12 is not the same month last year inside this fold.")
        roll_months = [as_month(month - pd.DateOffset(months=k)) for k in (1, 2, 3)]
        expected = float(np.mean([lookup[item] for item in roll_months]))
        if not math.isclose(float(row["revenue_roll_mean_3"]), expected, rel_tol=0, abs_tol=0.05):
            raise FoldLeakError("revenue_roll_mean_3 uses a month outside the prior three.")


def assert_validation_lags_stay_inside_prefix(
    raw_prefix: pd.DataFrame, val_rows: pd.DataFrame, last_month
) -> None:
    """Validation lags may use earlier months in this fold. They may not use the next fold."""
    last = as_month(last_month)
    known = set(_revenue_lookup(raw_prefix))
    if any(month > last for month in known):
        raise FoldLeakError("Prefix contains a month after this fold.")
    if val_rows.empty:
        raise FoldLeakError("A fold has no validation rows to check.")
    for _, row in val_rows.iterrows():
        month = as_month(row["month"])
        if month > last:
            raise FoldLeakError("A validation row is past this fold.")
        for step in (1, 2, 3, 12):
            source = as_month(month - pd.DateOffset(months=step))
            if source > last or source not in known:
                raise FoldLeakError("A validation lag reaches outside this fold.")


def _errors(y_true: np.ndarray, y_pred: np.ndarray) -> tuple[float, float]:
    mae = float(mean_absolute_error(y_true, y_pred))
    mse = float(mean_squared_error(y_true, y_pred))
    return mae, float(np.sqrt(mse))


def make_eval_model() -> RandomForestRegressor:
    """Lift forest. Depth and leaf size stop a single month from being a leaf."""
    return RandomForestRegressor(
        n_estimators=EVAL_TREES,
        max_depth=EVAL_MAX_DEPTH,
        min_samples_leaf=EVAL_MIN_SAMPLES_LEAF,
        random_state=SEED,
        n_jobs=1,
    )


def _fit_fold(train_df: pd.DataFrame, val_df: pd.DataFrame):
    """Fit the yearly lift. Return predictions in USD. Scaler sees training rows only."""
    train_scaled, val_scaled, scaler = scale_feature_frames(train_df, val_df)
    seen = int(getattr(scaler, "n_samples_seen_", -1))
    if seen != len(train_df):
        raise FoldLeakError("Scaler saw a different row count than this fold's training window.")
    lag_train = train_df["revenue_lag_12"].to_numpy(dtype=float)
    lag_val = val_df["revenue_lag_12"].to_numpy(dtype=float)
    if np.any(lag_train <= 0) or np.any(lag_val <= 0):
        raise FoldLeakError("revenue_lag_12 must stay positive to score the yearly lift.")
    y_train = train_scaled[TARGET_COLUMN].to_numpy(dtype=float)
    y_val = val_scaled[TARGET_COLUMN].to_numpy(dtype=float)
    model = make_eval_model()
    x_train = train_scaled.loc[:, list(FEATURE_COLUMNS)].to_numpy()
    x_val = val_scaled.loc[:, list(FEATURE_COLUMNS)].to_numpy()
    model.fit(x_train, y_train / lag_train)
    return (
        y_train,
        model.predict(x_train) * lag_train,
        y_val,
        model.predict(x_val) * lag_val,
        seen,
    )


def _score_window(
    raw_train: pd.DataFrame, ready: pd.DataFrame, window: FoldWindow
) -> tuple[FoldScore, float, float, float]:
    last_month = ready.iloc[window.val_positions[-1]]["month"]
    val_start = ready.iloc[window.val_positions[0]]["month"]
    raw_prefix = raw_prefix_through(raw_train, last_month)
    prefix = features_through(raw_train, last_month)
    if len(prefix) != window.val_positions[-1] + 1:
        raise FoldLeakError("Fold prefix length does not match the validation end index.")
    left = pd.to_datetime(prefix["month"]).to_numpy()
    right = pd.to_datetime(ready["month"].iloc[: len(prefix)]).to_numpy()
    if not np.array_equal(left, right):
        raise FoldLeakError("Fold prefix months do not match the training series.")
    train_df = prefix.iloc[list(window.train_positions)]
    val_df = prefix.iloc[list(window.val_positions)]
    if as_month(train_df["month"].iloc[-1]) >= as_month(val_start):
        raise FoldOrderError("Training months are not strictly before validation months.")
    assert_training_lags_stop_before(raw_prefix, train_df, val_start)
    assert_validation_lags_stay_inside_prefix(raw_prefix, val_df, last_month)
    y_train, train_pred, y_val, val_pred, seen = _fit_fold(train_df, val_df)
    train_mae, train_rmse = _errors(y_train, train_pred)
    val_mae, val_rmse = _errors(y_val, val_pred)
    val_mean = float(np.mean(y_val))
    signed = val_pred - y_val
    abs_error = np.abs(signed)
    score = FoldScore(
        fold_number=window.fold_number,
        train_rows=len(train_df),
        val_rows=len(val_df),
        train_start=month_label(train_df["month"].iloc[0]),
        train_end=month_label(train_df["month"].iloc[-1]),
        val_start=month_label(val_df["month"].iloc[0]),
        val_end=month_label(val_df["month"].iloc[-1]),
        train_mae=train_mae,
        train_rmse=train_rmse,
        val_mae=val_mae,
        val_rmse=val_rmse,
        val_mean_revenue=val_mean,
        scaler_rows=seen,
    )
    return score, float(signed.sum()), float(abs_error[signed > 0].sum()), float(abs_error.sum())


def learning_curve_points(raw_train: pd.DataFrame, ready: pd.DataFrame) -> tuple[list[CurvePoint], FoldWindow]:
    """Grow the earliest training months against the last fold's validation block.

    The validation block never enters a training prefix. The scaler is refit
    on each prefix. 2024–2025 are not in ``ready``.
    """
    windows = fold_windows(len(ready))
    assert_windows_chronological(windows, list(ready["month"]))
    holdout = windows[-1]
    pool = holdout.val_positions[0]
    if pool < MIN_STABLE_TRAIN_MONTHS:
        raise FoldOrderError("The learning-curve pool is shorter than four seasonal cycles.")
    sizes: list[int] = []
    for fraction in (0.4, 0.55, 0.7, 0.85, 1.0):
        size = min(pool, max(24, int(round(pool * fraction))))
        if size not in sizes:
            sizes.append(size)
    if sizes[-1] != pool:
        sizes.append(pool)
    last_month = ready.iloc[holdout.val_positions[-1]]["month"]
    prefix = features_through(raw_train, last_month)
    val_df = prefix.iloc[list(holdout.val_positions)]
    baseline = float(val_df[TARGET_COLUMN].mean())
    if baseline <= 0:
        raise FoldLeakError("Validation revenue must stay positive.")
    points: list[CurvePoint] = []
    for size in sizes:
        train_df = prefix.iloc[:size]
        if as_month(train_df["month"].iloc[-1]) >= as_month(val_df["month"].iloc[0]):
            raise FoldOrderError("A learning-curve prefix reaches the validation block.")
        y_train, train_pred, y_val, val_pred, _seen = _fit_fold(train_df, val_df)
        train_mae, train_rmse = _errors(y_train, train_pred)
        val_mae, val_rmse = _errors(y_val, val_pred)
        points.append(
            CurvePoint(
                train_rows=size,
                train_mae=train_mae,
                train_rmse=train_rmse,
                val_mae=val_mae,
                val_rmse=val_rmse,
                train_rmse_pct=(train_rmse / baseline) * 100.0,
                val_rmse_pct=(val_rmse / baseline) * 100.0,
            )
        )
    return points, holdout


def sample_spread(values: list[float]) -> Spread:
    if len(values) < 2:
        raise FoldOrderError("Need at least two folds to report a standard deviation.")
    return Spread(mean=float(statistics.mean(values)), std=float(statistics.stdev(values)))


def classify_fit(points: list[CurvePoint]) -> str:
    """Label the largest training prefix. Short folds do not cast this vote."""
    if len(points) < 2:
        raise FoldOrderError("Learning curve needs at least two training sizes.")
    last = points[-1]
    gap = last.val_rmse_pct - last.train_rmse_pct
    train_low = last.train_rmse_pct < ORDINARY_BAND_PCT
    val_low = last.val_rmse_pct < ORDINARY_BAND_PCT
    if train_low and val_low and abs(gap) < WIDE_GAP_PCT:
        return "well fitted"
    if train_low and (last.val_rmse_pct >= ORDINARY_BAND_PCT or gap >= WIDE_GAP_PCT):
        return "overfitting"
    return "underfitting"


def corrective_action(
    label: str,
    *,
    stable: bool,
    peak: float,
    months_above: list[str],
) -> str:
    """One next step. It matches the fit label and does not retune the forest here."""
    if label == "overfitting":
        return (
            "Training RMSE stays on the floor of the curve at every prefix. That is the "
            "leaf rule in `make_model()`: `min_samples_leaf=1` and `max_depth=None` let "
            "one training month occupy a leaf. Validation RMSE falls as the prefix grows, "
            "then flattens while the gap is still wide, so another slice of the same "
            "history is not the first fix. Set `min_samples_leaf=3` and `max_depth=6`, "
            "keep `n_estimators=400` and `random_state=42`, and redraw this learning curve "
            "before staging. Keep the tree count at 400. Keep 2024–2025 out of that refit."
        )
    if label == "underfitting":
        return (
            "Training RMSE on the full prefix is still outside the ordinary ±5% band, "
            "so the flu-season and summer shape is not in the fit. Add one causal "
            "feature, `seasonal_index`: for each row, the mean of `revenue_usd / "
            "revenue_lag_12` on that calendar month, using only months strictly earlier "
            "than the row. Retrain this same forest and redraw the curve. Build that "
            "ratio from 2016–2023 only."
        )
    if not stable:
        return (
            "The full training prefix sits inside the ordinary band, so the forest "
            "does not need a deeper tree or a smaller leaf. Validation RMSE moves "
            "because the early TimeSeriesSplit folds train on fewer than 48 months. "
            "For the promotion vote, recompute validation RMSE as mean ± sample "
            "standard deviation on the folds that have at least 48 training months "
            "(four seasonal cycles of `revenue_usd`), and keep the five-fold figure "
            "beside that number. Leave `make_model()` unchanged."
        )
    if months_above:
        listed = ", ".join(months_above)
        return (
            f"The learning curve supports staging this forest. Leave "
            f"`min_samples_leaf` at {EVAL_MIN_SAMPLES_LEAF}, `max_depth` at {EVAL_MAX_DEPTH}, "
            f"and `n_estimators` at {EVAL_TREES}. Before promotion, Tom Callahan reviews "
            f"these 2024–2025 months, whose actual `revenue_usd` exceeds the 2016–2023 "
            f"peak of {peak:,.0f} USD: {listed}. Those months stayed out of the fit."
        )
    return (
        "The learning curve supports staging this forest. No 2024–2025 month exceeds "
        "the 2016–2023 peak of "
        f"{peak:,.0f} USD, so the tree ceiling is not the blocker on this file. "
        "The promotion note for Tom Callahan is validation RMSE as a percent of "
        "average monthly `revenue_usd` on the fixed block inside 2017–2023. Leave "
        "`make_model()` unchanged."
    )


def diagnose(points: list[CurvePoint], val_rmses: list[float], peak: float, months_above: list[str]) -> Diagnosis:
    label = classify_fit(points)
    spread = sample_spread(val_rmses)
    stable = spread.mean == 0 or (spread.std / spread.mean) <= STABILITY_CV
    last = points[-1]
    middle = points[len(points) // 2]
    gap = last.val_rmse_pct - last.train_rmse_pct
    middle_gap = middle.val_rmse_pct - middle.train_rmse_pct
    rationale = (
        f"At {middle.train_rows} training months the gap is {middle_gap:.1f} percentage "
        f"points (validation RMSE {middle.val_rmse_pct:.1f}% of the fixed block's average "
        f"`revenue_usd`, training RMSE {middle.train_rmse_pct:.1f}%). At {last.train_rows} "
        f"training months the gap is {gap:.1f} percentage points (validation "
        f"{last.val_rmse_pct:.1f}%, training {last.train_rmse_pct:.1f}%). The fit call uses "
        f"this largest prefix. The ordinary-band ceiling is {ORDINARY_BAND_PCT:.0f}% and a "
        f"wide gap is {WIDE_GAP_PCT:.0f} points. The five-fold mean is the stability "
        f"number, not a second fit label."
    )
    action = corrective_action(label, stable=stable, peak=peak, months_above=months_above)
    if label == "overfitting":
        previous = points[-2]
        action += (
            f" On this series, validation RMSE is {_usd(previous.val_rmse)} USD at "
            f"{previous.train_rows} training months and {_usd(last.val_rmse)} USD at "
            f"{last.train_rows} training months ({last.val_rmse_pct:.1f}% of the fixed block). "
            f"Training RMSE at that prefix is {_usd(last.train_rmse)} USD "
            f"({last.train_rmse_pct:.1f}%)."
        )
        if last.val_rmse_pct < ORDINARY_BAND_PCT:
            rationale += (
                " Validation RMSE on that prefix is inside the 8% ceiling. The label "
                "stays overfitting because the training line stays near the leaf floor "
                f"and the gap is still at least {WIDE_GAP_PCT:.0f} points."
            )
    return Diagnosis(
        label=label,
        stable=stable,
        rationale=rationale,
        action=action,
        train_rmse_pct=last.train_rmse_pct,
        val_rmse_pct=last.val_rmse_pct,
        gap_pct=gap,
    )


def months_above_training_peak(frame: pd.DataFrame) -> tuple[float, tuple[str, ...]]:
    """Holdout months above the training peak. Used only in the staging note."""
    raw_train, raw_test = split_by_year(frame)
    peak = float(raw_train["revenue_usd"].max())
    above = raw_test.loc[raw_test["revenue_usd"] > peak, "month"]
    labels = tuple(month_label(month) for month in above)
    return peak, labels


def run_evaluation(frame: pd.DataFrame) -> EvaluationResult:
    """Score the five folds and the learning curve. Does not touch 2024–2025."""
    if "visits_count" in FEATURE_COLUMNS or "avg_revenue_per_visit_usd" in FEATURE_COLUMNS:
        raise FoldLeakError("Same-month visits must stay out of the feature list.")
    raw_train, _raw_test = split_by_year(frame)
    raw_train = raw_train.sort_values("month").reset_index(drop=True)
    ready = training_ready_frame(frame)
    if set(ready["region"].astype(str).str.lower()) != {"consolidated"}:
        raise FoldLeakError("Evaluation rows must stay on the consolidated series.")
    if as_month(ready["month"].min()) < pd.Timestamp("2017-01-01"):
        raise FoldLeakError("Lag warmup rows entered cross-validation.")
    if as_month(ready["month"].max()) >= HOLDOUT_START:
        raise FoldLeakError("Cross-validation included a holdout year.")
    windows = fold_windows(len(ready))
    assert_windows_chronological(windows, list(ready["month"]))
    scores: list[FoldScore] = []
    signed_sum = 0.0
    over_abs = 0.0
    total_abs = 0.0
    for window in windows:
        score, signed, over, total = _score_window(raw_train, ready, window)
        if score.scaler_rows != score.train_rows:
            raise FoldLeakError("Scaler row count does not match the training window.")
        scores.append(score)
        signed_sum += signed
        over_abs += over
        total_abs += total
    curve, holdout = learning_curve_points(raw_train, ready)
    last_fold = scores[-1]
    last_point = curve[-1]
    if abs(last_point.val_rmse - last_fold.val_rmse) > 0.05:
        raise FoldOrderError("The full learning-curve prefix does not match the last fold.")
    if total_abs <= 0:
        raise FoldLeakError("Validation absolute error is zero, so the overestimate share is undefined.")
    val_rows = sum(score.val_rows for score in scores)
    peak, above = months_above_training_peak(frame)
    val_rmses = [score.val_rmse for score in scores]
    diagnosis = diagnose(curve, val_rmses, peak, list(above))
    long_scores = [score for score in scores if score.train_rows >= MIN_STABLE_TRAIN_MONTHS]
    long_spread = sample_spread([score.val_rmse for score in long_scores]) if len(long_scores) >= 2 else None
    val_spread = sample_spread(val_rmses)
    return EvaluationResult(
        folds=tuple(scores),
        curve=tuple(curve),
        diagnosis=diagnosis,
        train_mae=sample_spread([score.train_mae for score in scores]),
        train_rmse=sample_spread([score.train_rmse for score in scores]),
        val_mae=sample_spread([score.val_mae for score in scores]),
        val_rmse=val_spread,
        stability_cv=0.0 if val_spread.mean == 0 else val_spread.std / val_spread.mean,
        long_window_rmse=long_spread,
        long_window_folds=tuple(score.fold_number for score in long_scores),
        baseline_revenue_usd=float(ready.iloc[list(holdout.val_positions)][TARGET_COLUMN].mean()),
        validation_mean_signed_error=signed_sum / val_rows,
        overestimate_abs_share=over_abs / total_abs,
        train_peak_usd=peak,
        months_above_peak=above,
        curve_val_start=month_label(ready.iloc[holdout.val_positions[0]]["month"]),
        curve_val_end=month_label(ready.iloc[holdout.val_positions[-1]]["month"]),
    )


def _usd(value: float) -> str:
    return f"{value:,.0f}"


def render_report(result: EvaluationResult) -> str:
    """Technical report for the promotion review. Aggregates only."""
    diagnosis = result.diagnosis
    fold_lines = "\n".join(
        "| {fold} | {train_start}–{train_end} | {val_start}–{val_end} | {train_rows} | "
        "{train_mae} | {train_rmse} | {val_mae} | {val_rmse} | {val_pct:.1f}% |".format(
            fold=score.fold_number,
            train_start=score.train_start,
            train_end=score.train_end,
            val_start=score.val_start,
            val_end=score.val_end,
            train_rows=score.train_rows,
            train_mae=_usd(score.train_mae),
            train_rmse=_usd(score.train_rmse),
            val_mae=_usd(score.val_mae),
            val_rmse=_usd(score.val_rmse),
            val_pct=(score.val_rmse / score.val_mean_revenue) * 100.0,
        )
        for score in result.folds
    )
    curve_lines = "\n".join(
        f"| {point.train_rows} | {_usd(point.train_mae)} | {_usd(point.train_rmse)} | "
        f"{_usd(point.val_mae)} | {_usd(point.val_rmse)} | {point.train_rmse_pct:.1f}% | "
        f"{point.val_rmse_pct:.1f}% |"
        for point in result.curve
    )
    short = min(result.folds, key=lambda score: score.train_rows)
    val_pcts = [(score.val_rmse / score.val_mean_revenue) * 100.0 for score in result.folds]
    val_pct = sample_spread(val_pcts)
    low_rmse = min(score.val_rmse for score in result.folds)
    high_rmse = max(score.val_rmse for score in result.folds)
    if result.long_window_rmse is None:
        long_sentence = (
            f"Fewer than two folds reach {MIN_STABLE_TRAIN_MONTHS} training months, "
            "so the long-window standard deviation is not reported."
        )
    else:
        names = ", ".join(str(number) for number in result.long_window_folds)
        long_sentence = (
            f"Folds with at least {MIN_STABLE_TRAIN_MONTHS} training months "
            f"(folds {names}): validation RMSE "
            f"**{_usd(result.long_window_rmse.mean)} ± {_usd(result.long_window_rmse.std)} USD**."
        )
    stability = "stable" if diagnosis.stable else "not stable"
    if result.validation_mean_signed_error > 0:
        direction = "above"
    elif result.validation_mean_signed_error < 0:
        direction = "below"
    else:
        direction = "on"
    above = ", ".join(result.months_above_peak) if result.months_above_peak else "none"
    label = diagnosis.label
    block_rmse = result.curve[-1].val_rmse
    dollar_delta = PRIOR_VAL_RMSE_MEAN - result.val_rmse.mean
    block_delta = PRIOR_BLOCK_VAL_RMSE - block_rmse
    gap_delta = PRIOR_GAP_PCT - diagnosis.gap_pct
    if label == "well fitted" and dollar_delta > 0 and block_delta > 0 and gap_delta > 0:
        verdict = "This review is **better** than that one."
    elif dollar_delta < 0 and gap_delta < 0:
        verdict = "This review is **worse** than that one."
    else:
        verdict = "This review is **mixed** against that one."
    return f"""# HealthCore consolidated revenue forecast — technical evaluation

Promotion review of the yearly-lift forest before staging. The forest learns `revenue_usd / revenue_lag_12`. The dollar forecast is that lift times `revenue_lag_12`. Settings: `n_estimators={EVAL_TREES}`, `max_depth={EVAL_MAX_DEPTH}`, `min_samples_leaf={EVAL_MIN_SAMPLES_LEAF}`, `random_state={SEED}`. Errors below are USD on `revenue_usd`. The PLAN-095 trainer `make_model()` is a separate dollar forest and is not the model scored here.

Target: `revenue_usd`. Series: `region = consolidated` in `data/raw/healthcore_sales.csv`, columns `month`, `revenue_usd`, `visits_count`, `avg_revenue_per_visit_usd`, and `region`. Same-month `visits_count` and `avg_revenue_per_visit_usd` are not features. Cross-validation and the learning curve use 2016–2023 only, after the 12-month lag warmup (ready months start in 2017). The 2024–2025 holdout stays outside every fold, every scaler, and the curve.

## Metric choice

**Primary metric: RMSE.** The sales briefing asks Tom Callahan and Dr. Sandra Okonkwo to read squared error in USD² and as a percent of average monthly revenue. RMSE is that squared error back in dollars. A flu-season month (October–December, about 15–20% above the year's average) or an atypical drop therefore counts more than an ordinary month, which the briefing puts at about ±5% around the trend.

**Companion metric: MAE.** MAE is the typical absolute miss in USD, so Finance can read an ordinary month without the square.

**Costlier direction: overestimating `revenue_usd`.** The briefing's attention case for Dr. Okonkwo is an atypical drop that looks like a normal low month — August versus a clinical capacity problem Marcus Reid would need to see. That miss is an overestimate of a weak month. It also makes the executive-dashboard decision look funded by cash the month did not produce. Underestimating the October–December lift is a staffing miss, and the squared metric still charges that large miss. The direction named for the go/no-go is the unseen drop.

On the five validation windows pooled together, predicted `revenue_usd` sits **{direction}** actual by **{_usd(abs(result.validation_mean_signed_error))} USD** on average (predicted minus actual: {_usd(result.validation_mean_signed_error)} USD). **{result.overestimate_abs_share * 100:.0f}%** of absolute validation error comes from months the forest set too high.

## Time-aware cross-validation

`TimeSeriesSplit` with 5 folds. The splitter has no shuffle. Each training window starts at the earliest ready month and expands. Each validation window is the next contiguous block. Fold features are rebuilt from raw 2016–2023 months that end on that fold's last validation month, so a later fold is not in the frame. For every training row, `revenue_lag_1`, `revenue_lag_12`, and `revenue_roll_mean_3` use only months before the validation window. A validation row may use an earlier month inside its own window (one-step score). It may not use the next fold. The dollar scaler is fit on that fold's training rows only (`n_samples_seen_` equals the training row count). `revenue_usd` is not scaled.

| Fold | Training months | Validation months | Train rows | Train MAE (USD) | Train RMSE (USD) | Val MAE (USD) | Val RMSE (USD) | Val RMSE vs that window |
|------|-----------------|-------------------|----------:|----------------:|-----------------:|--------------:|---------------:|-----------------------:|
{fold_lines}

Sample standard deviation uses divisor n−1.

| Metric | Training | Validation |
|--------|----------|------------|
| MAE | **{_usd(result.train_mae.mean)} ± {_usd(result.train_mae.std)} USD** | **{_usd(result.val_mae.mean)} ± {_usd(result.val_mae.std)} USD** |
| RMSE | **{_usd(result.train_rmse.mean)} ± {_usd(result.train_rmse.std)} USD** | **{_usd(result.val_rmse.mean)} ± {_usd(result.val_rmse.std)} USD** |

Primary number: validation RMSE **{_usd(result.val_rmse.mean)} ± {_usd(result.val_rmse.std)} USD**.

Stability: validation RMSE runs from **{_usd(low_rmse)} USD** on the lowest fold to **{_usd(high_rmse)} USD** on the highest. The coefficient of variation is **{result.stability_cv:.2f}**. The bar for a stable promotion score is {STABILITY_CV:.2f}, so the five-fold dollar score is **{stability}**. As a percent of each fold's own average validation `revenue_usd`, RMSE is **{val_pct.mean:.1f}% ± {val_pct.std:.1f} points**. The shortest window is fold {short.fold_number}, with {short.train_rows} training months ({short.train_start}–{short.train_end}). {long_sentence}

## Learning curve

Chart: `data/eval/learning_curve.png`. The top panel is RMSE and the bottom panel is MAE. Both panels plot training error and validation error against the number of earliest training months.

The validation block is fixed: **{result.curve_val_start}–{result.curve_val_end}**, the last TimeSeriesSplit fold, still inside 2017–2023. Percents use that block's average actual `revenue_usd` (**{_usd(result.baseline_revenue_usd)} USD**). Each prefix refits the scaler. The full prefix matches the last fold's validation RMSE, which is the check that the curve and the cross-validation share one window.

| Training months | Train MAE | Train RMSE | Val MAE | Val RMSE | Train RMSE % | Val RMSE % |
|----------------:|----------:|-----------:|--------:|---------:|-------------:|-----------:|
{curve_lines}

## Diagnosis

The model is **{label}**.

{diagnosis.rationale}

The chart shows the same pattern: read the two RMSE lines at the right-hand side of `data/eval/learning_curve.png`. Training RMSE there is {diagnosis.train_rmse_pct:.1f}% of the fixed block and validation RMSE is {diagnosis.val_rmse_pct:.1f}%.

## Corrective action

{diagnosis.action}

Months in 2024–2025 whose actual `revenue_usd` exceeds the 2016–2023 peak of {_usd(result.train_peak_usd)} USD: {above}. Those actuals are a staging list. They are not rows in the fit, the folds, or the curve.

## Comparison with the dollar-target evaluation

The previous review scored a dollar-target forest (`max_depth=None`, `min_samples_leaf=1`) on these same folds and this same fixed block. That write-up is `data/eval/evaluation_report_dollar.md`. Its chart is `data/eval/learning_curve_dollar.png`.

{verdict} The fit label moves from **{PRIOR_LABEL}** to **{label}**. The five-fold validation RMSE moves by **{_usd(dollar_delta)} USD** (positive means this run is lower). The fixed-block validation RMSE moves by **{_usd(block_delta)} USD**. The learning-curve gap moves by **{gap_delta:.1f}** points.

| | Dollar target, leaf 1 | Yearly lift, leaf 3, depth 6 |
|--|----------------------:|-----------------------------:|
| Fit label | {PRIOR_LABEL} | {label} |
| Validation RMSE | {_usd(PRIOR_VAL_RMSE_MEAN)} ± {_usd(PRIOR_VAL_RMSE_STD)} USD | {_usd(result.val_rmse.mean)} ± {_usd(result.val_rmse.std)} USD |
| Validation MAE | {_usd(PRIOR_VAL_MAE_MEAN)} ± {_usd(PRIOR_VAL_MAE_STD)} USD | {_usd(result.val_mae.mean)} ± {_usd(result.val_mae.std)} USD |
| Training RMSE | {_usd(PRIOR_TRAIN_RMSE_MEAN)} USD | {_usd(result.train_rmse.mean)} USD |
| Largest prefix, training RMSE | {PRIOR_TRAIN_RMSE_PCT:.1f}% | {diagnosis.train_rmse_pct:.1f}% |
| Largest prefix, validation RMSE | {PRIOR_VAL_RMSE_PCT:.1f}% ({_usd(PRIOR_BLOCK_VAL_RMSE)} USD) | {diagnosis.val_rmse_pct:.1f}% ({_usd(block_rmse)} USD) |
| Gap at the largest prefix | {PRIOR_GAP_PCT:.1f} points | {diagnosis.gap_pct:.1f} points |
| RMSE vs each fold's own window | {PRIOR_FOLD_PCT_MEAN:.1f}% ± {PRIOR_FOLD_PCT_STD:.1f} points | {val_pct.mean:.1f}% ± {val_pct.std:.1f} points |
| Stability coefficient | {PRIOR_STABILITY_CV:.2f} | {result.stability_cv:.2f} |

## What this run kept fixed

The run leaves the PLAN-095 `make_model()` trainer unchanged. It leaves 2024–2025 out of training. It leaves `visits_count` and `avg_revenue_per_visit_usd` out of the features. Months stay in calendar order. The scored target in dollars is still `revenue_usd`. The report uses aggregated revenue only.
"""
