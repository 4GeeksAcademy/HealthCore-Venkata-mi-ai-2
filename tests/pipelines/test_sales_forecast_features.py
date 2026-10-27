"""Lag and rolling revenue features may only see months that already happened."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from data.process.sales_forecast import build_features, load_sales  # noqa: E402


def test_lag_and_rolling_features_are_causal():
    featured = build_features(load_sales())
    revenue = featured["revenue_usd"]
    lag = featured["revenue_lag_1"]

    assert np.isnan(lag.iloc[0])
    for index in range(1, len(featured)):
        assert lag.iloc[index] == revenue.iloc[index - 1]
        assert lag.iloc[index] != revenue.iloc[index] or revenue.iloc[index] == revenue.iloc[index - 1]

    rolling = featured["revenue_roll_mean_3"]
    assert rolling.iloc[:3].isna().all()
    for index in range(3, len(featured)):
        past_only = revenue.iloc[index - 3 : index].mean()
        includes_current = revenue.iloc[index - 2 : index + 1].mean()
        assert rolling.iloc[index] == pytest.approx(past_only)
        if not np.isclose(past_only, includes_current):
            assert rolling.iloc[index] != pytest.approx(includes_current)

    lag_12 = featured["revenue_lag_12"]
    assert lag_12.iloc[:12].isna().all()
    for index in range(12, len(featured)):
        assert lag_12.iloc[index] == revenue.iloc[index - 12]
