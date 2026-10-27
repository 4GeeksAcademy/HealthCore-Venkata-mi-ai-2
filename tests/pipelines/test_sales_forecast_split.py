"""The revenue forecast holds out 2024–2025 and does not mix those months into training."""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from data.process.sales_forecast import (  # noqa: E402
    build_features,
    load_sales,
    rows_ready_for_model,
    split_by_year,
)


def test_split_respects_8_2_rule_and_no_leakage():
    frame = load_sales()
    train, test = split_by_year(frame)

    train_years = set(train["month"].dt.year)
    test_years = set(test["month"].dt.year)

    assert train_years == set(range(2016, 2024))
    assert test_years == {2024, 2025}
    assert len(train_years) == 8
    assert len(test_years) == 2
    assert train_years.isdisjoint(test_years)
    assert max(train_years) < min(test_years)
    assert len(train) == 96
    assert len(test) == 24
    assert set(train["month"]).isdisjoint(set(test["month"]))

    featured = build_features(frame)
    ready_train = rows_ready_for_model(split_by_year(featured)[0])
    ready_test = rows_ready_for_model(split_by_year(featured)[1])
    assert set(ready_train["month"]).isdisjoint(set(ready_test["month"]))
    assert int(ready_train["month"].dt.year.max()) < 2024
    assert set(ready_test["month"].dt.year) == {2024, 2025}
    assert len(ready_test) == 24
