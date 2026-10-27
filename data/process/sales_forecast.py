"""Causal monthly revenue forecast for HealthCore consolidated clinic revenue.

The target is ``revenue_usd`` on the official ``consolidated`` series
(2016-01 through 2025-12). Features use only information known before the
month closes: prior revenue, and the calendar of the month being forecast.
Same-month visits and average revenue per visit are not features — those
figures are not known when Finance asks for a forward number, and using them
would leak the month being predicted.

Algorithm choice — Random Forest, not XGBoost:
- About 120 monthly rows, and roughly 84 left after the 12-month lag warmup.
  That is too small to spend a tuning budget on boosting without memorizing
  the past.
- Tom Callahan (Revenue Cycle) and Dr. Sandra Okonkwo need a feasibility
  answer they can explain: which signals moved the forecast (last month,
  same month last year, flu-season calendar), not a sequential black box.
- Tree-to-tree spread supplies the variability band the ticket asked for,
  without a separate interval model.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import normaltest
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
from sklearn.preprocessing import StandardScaler

SEED = 42
# First calendar year in the official file. Eight train years end before 2024.
TRAIN_YEAR_START = 2016
TEST_YEAR_START = 2024
EXPECTED_COLUMNS = (
    "month",
    "revenue_usd",
    "visits_count",
    "avg_revenue_per_visit_usd",
    "region",
)
FEATURE_COLUMNS = (
    "revenue_lag_1",
    "revenue_lag_12",
    "revenue_roll_mean_3",
    "month_of_year",
    "quarter",
    "month_sin",
    "month_cos",
)
# Dollar lags dwarf month indexes. Scale these only, and only from train rows.
SCALE_COLUMNS = ("revenue_lag_1", "revenue_lag_12", "revenue_roll_mean_3")
TARGET_COLUMN = "revenue_usd"


class SalesDataError(Exception):
    """The official sales file failed a column or continuity check."""


def default_sales_path(repo_root: Path | None = None) -> Path:
    root = repo_root or Path(__file__).resolve().parents[2]
    return root / "data" / "raw" / "healthcore_sales.csv"


def load_sales(path: Path | None = None) -> pd.DataFrame:
    """Load the official consolidated series. Does not invent or alter values."""
    csv_path = path or default_sales_path()
    try:
        frame = pd.read_csv(csv_path)
    except FileNotFoundError:
        raise
    except pd.errors.EmptyDataError as exc:
        raise SalesDataError("Sales file is empty.") from exc
    except pd.errors.ParserError as exc:
        raise SalesDataError("Sales file could not be parsed as CSV.") from exc
    except OSError as exc:
        raise SalesDataError("Sales file could not be read.") from exc

    frame.columns = [str(name).strip() for name in frame.columns]
    missing = [name for name in EXPECTED_COLUMNS if name not in frame.columns]
    if missing:
        raise SalesDataError(
            "Sales file is missing required columns: " + ", ".join(missing)
        )

    frame = frame.loc[:, list(EXPECTED_COLUMNS)].copy()
    if frame[list(EXPECTED_COLUMNS)].isna().any().any():
        raise SalesDataError("Sales file has empty values in required columns.")

    frame["month"] = pd.to_datetime(frame["month"], format="%Y-%m-%d", errors="coerce")
    if frame["month"].isna().any():
        raise SalesDataError("Sales file has a month that is not YYYY-MM-DD.")

    frame["region"] = frame["region"].astype(str).str.strip().str.lower()
    frame = frame.loc[frame["region"] == "consolidated"].copy()
    frame = frame.sort_values("month").drop_duplicates("month").reset_index(drop=True)

    if (frame["revenue_usd"] <= 0).any():
        raise SalesDataError("Revenue must stay positive.")

    expected_months = pd.date_range("2016-01-01", "2025-12-01", freq="MS")
    actual = pd.DatetimeIndex(frame["month"])
    if len(frame) != len(expected_months) or not actual.equals(expected_months):
        raise SalesDataError(
            "Sales file must be one consolidated row per month from 2016-01 to 2025-12."
        )
    return frame


def build_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Lag and rolling features use only earlier rows. Calendar is known ahead."""
    featured = frame.copy()
    revenue = featured["revenue_usd"]
    # shift(1) before rolling so the current month's revenue never enters the window.
    featured["revenue_lag_1"] = revenue.shift(1)
    featured["revenue_lag_12"] = revenue.shift(12)
    featured["revenue_roll_mean_3"] = revenue.shift(1).rolling(window=3, min_periods=3).mean()
    featured["month_of_year"] = featured["month"].dt.month.astype(int)
    featured["quarter"] = featured["month"].dt.quarter.astype(int)
    angle = 2.0 * np.pi * featured["month_of_year"] / 12.0
    featured["month_sin"] = np.sin(angle)
    featured["month_cos"] = np.cos(angle)
    return featured


def split_by_year(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """First 8 years (2016–2023) train. Latest 2 years (2024–2025) test.

    The cut is the calendar, not a random shuffle. Test months never sit in
    the training frame.
    """
    years = frame["month"].dt.year
    train = frame.loc[years < TEST_YEAR_START].copy()
    test = frame.loc[years >= TEST_YEAR_START].copy()
    return train, test


def rows_ready_for_model(frame: pd.DataFrame) -> pd.DataFrame:
    """Drop the lag warmup (early 2016). Does not drop a complete test year."""
    return frame.dropna(subset=list(FEATURE_COLUMNS)).reset_index(drop=True)


def scale_feature_frames(
    train: pd.DataFrame, test: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, StandardScaler]:
    """Fit the scaler on training rows only, then apply it to the test years."""
    scaler = StandardScaler()
    scaler.fit(train.loc[:, list(SCALE_COLUMNS)])
    train_scaled = train.copy()
    test_scaled = test.copy()
    train_scaled.loc[:, list(SCALE_COLUMNS)] = scaler.transform(train.loc[:, list(SCALE_COLUMNS)])
    test_scaled.loc[:, list(SCALE_COLUMNS)] = scaler.transform(test.loc[:, list(SCALE_COLUMNS)])
    return train_scaled, test_scaled, scaler


def make_model() -> RandomForestRegressor:
    """Random Forest for the short monthly series. Seed is fixed.

    Leaves may hold a single training month so the forecast can reach the
    strongest months already seen in 2017-2023. The target stays ``revenue_usd``.
    A tree still cannot print a dollar level above that training peak.
    """
    return RandomForestRegressor(
        n_estimators=400,
        max_depth=None,
        min_samples_leaf=1,
        random_state=SEED,
        n_jobs=1,
    )


def population_stability_index(
    expected: np.ndarray, actual: np.ndarray, bins: int = 10
) -> float:
    """PSI of ``actual`` against equal-width bins from ``expected``.

    Below 0.10 is stable, 0.10-0.25 is a shift worth naming, above 0.25 is a
    large move. The test window is 24 months, so the bin count is capped
    (about four points per bin). Half-count smoothing stops an empty bin from
    looking like a population break. Tails are open so values outside the
    training range still count.
    """
    expected = np.asarray(expected, dtype=float)
    actual = np.asarray(actual, dtype=float)
    bin_count = int(min(bins, max(3, len(actual) // 4)))
    low, high = np.quantile(expected, [0.01, 0.99])
    if not np.isfinite(low) or not np.isfinite(high) or high <= low:
        return 0.0
    inner = np.linspace(low, high, bin_count - 1)
    edges = np.concatenate(([-np.inf], inner, [np.inf]))
    expected_counts = np.histogram(expected, bins=edges)[0].astype(float) + 0.5
    actual_counts = np.histogram(actual, bins=edges)[0].astype(float) + 0.5
    expected_share = expected_counts / expected_counts.sum()
    actual_share = actual_counts / actual_counts.sum()
    return float(np.sum((actual_share - expected_share) * np.log(actual_share / expected_share)))


def normalized_gini(actual: np.ndarray, predicted: np.ndarray) -> float:
    """Ranking power: 1 means the forecast orders months like the actuals.

    Sandra uses this to see whether a quiet August is ranked as a normal low
    season rather than scrambled with a typical month. A low MSE can still
    hide a model that is right on the average and wrong on the order.
    """
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)

    def _raw_gini(values: np.ndarray, order_by: np.ndarray) -> float:
        ranking = np.argsort(-order_by, kind="mergesort")
        ordered = values[ranking]
        total = ordered.sum()
        if total == 0:
            return 0.0
        cumulative = np.cumsum(ordered).sum() / total
        count = len(ordered)
        return (cumulative - (count + 1) / 2.0) / count

    perfect = _raw_gini(actual, actual)
    if perfect == 0:
        return 0.0
    return float(_raw_gini(actual, predicted) / perfect)


@dataclass(frozen=True)
class TestMetrics:
    mse: float
    rmse: float
    rmse_pct_of_avg_revenue: float
    psi: float
    gini: float
    k2_statistic: float
    k2_pvalue: float
    avg_test_revenue_usd: float
    test_rows: int


def evaluate_on_test(
    y_train_reference: np.ndarray,
    y_test: np.ndarray,
    y_test_pred: np.ndarray,
    psi_actual: np.ndarray | None = None,
) -> TestMetrics:
    """MSE, Gini, and K² use 2024-2025 outcomes. PSI compares score distributions.

    ``y_train_reference`` is the training distribution (expected). ``psi_actual``
    is the test distribution. When omitted, the test forecasts themselves are
    the actual distribution.
    """
    y_test = np.asarray(y_test, dtype=float)
    y_test_pred = np.asarray(y_test_pred, dtype=float)
    mse = float(mean_squared_error(y_test, y_test_pred))
    rmse = float(np.sqrt(mse))
    average = float(np.mean(y_test))
    residuals = y_test - y_test_pred
    k2_statistic, k2_pvalue = normaltest(residuals)
    actual_for_psi = y_test_pred if psi_actual is None else np.asarray(psi_actual, dtype=float)
    return TestMetrics(
        mse=mse,
        rmse=rmse,
        rmse_pct_of_avg_revenue=(rmse / average) * 100.0,
        psi=population_stability_index(y_train_reference, actual_for_psi),
        gini=normalized_gini(y_test, y_test_pred),
        k2_statistic=float(k2_statistic),
        k2_pvalue=float(k2_pvalue),
        avg_test_revenue_usd=average,
        test_rows=int(len(y_test)),
    )


def tree_prediction_band(
    model: RandomForestRegressor, features: pd.DataFrame
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Point forecast plus the spread across trees (variability, not one line)."""
    matrix = features.loc[:, list(FEATURE_COLUMNS)].to_numpy()
    per_tree = np.stack([tree.predict(matrix) for tree in model.estimators_])
    center = per_tree.mean(axis=0)
    spread = per_tree.std(axis=0)
    return center, center - spread, center + spread


def seasonality_note(revenue: pd.Series, index: pd.DatetimeIndex) -> str:
    """Diagnostic only. Confirms the briefing's flu-season and summer shape.

    Additive ``seasonal_decompose`` (period 12) is not the forecast. Random
    Forest still produces the number Finance sees. A positive October–December
    seasonal mean and a negative July–August mean match the briefing: flu and
    year-end visits lift revenue 15–20%, summer vacation cuts it 12–18%.
    """
    from statsmodels.tsa.seasonal import seasonal_decompose

    series = pd.Series(revenue.to_numpy(dtype=float), index=index)
    parts = seasonal_decompose(series, model="additive", period=12)
    seasonal = parts.seasonal
    by_month = seasonal.groupby(seasonal.index.month).mean()
    summer = float(by_month.loc[[7, 8]].mean())
    flu_season = float(by_month.loc[[10, 11, 12]].mean())
    trend = parts.trend.dropna()
    grew = float(trend.iloc[-1]) > float(trend.iloc[0])
    matches = summer < 0 and flu_season > 0 and grew
    verdict = "matches" if matches else "does not match"
    return (
        f"Decomposition {verdict} the briefing: "
        f"July-August seasonal mean {summer:,.0f} USD, "
        f"October-December seasonal mean {flu_season:,.0f} USD, "
        f"trend {'rises' if grew else 'does not rise'} from the first fitted year to the last."
    )


def decomposition_frame(frame: pd.DataFrame):
    """Return the statsmodels result so the script can plot it once."""
    from statsmodels.tsa.seasonal import seasonal_decompose

    series = pd.Series(
        frame["revenue_usd"].to_numpy(dtype=float),
        index=pd.DatetimeIndex(frame["month"]),
        name="revenue_usd",
    )
    return seasonal_decompose(series, model="additive", period=12)
