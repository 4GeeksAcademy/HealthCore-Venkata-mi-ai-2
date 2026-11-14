"""Thin API wrapper over shared HealthCore incident CSV analysis."""

from __future__ import annotations

import sys
from pathlib import Path

_SHARED = Path(__file__).resolve().parents[3] / "packages" / "shared"
if str(_SHARED) not in sys.path:
    sys.path.insert(0, str(_SHARED))

from healthcore_incidents import (  # noqa: E402
    ALLOWED_CSV_CATEGORIES as ALLOWED_CATEGORIES,
    ALLOWED_CSV_STATUSES as ALLOWED_STATUSES,
    CSV_REQUIRED_FIELDS as REQUIRED_FIELDS,
    AnalysisError,
    AnalysisResult,
    analyze_csv_text,
    analyze_rows,
    parse_csv_rows,
    results_to_csv_string,
    results_to_metric_rows,
    validate_csv_row,
    valid_csv_rows,
)

# Backward-compatible alias used by older call sites.
validate_row = validate_csv_row
valid_rows = valid_csv_rows

__all__ = [
    "ALLOWED_CATEGORIES",
    "ALLOWED_STATUSES",
    "REQUIRED_FIELDS",
    "AnalysisError",
    "AnalysisResult",
    "analyze_csv_text",
    "analyze_rows",
    "parse_csv_rows",
    "results_to_csv_string",
    "results_to_metric_rows",
    "validate_csv_row",
    "validate_row",
    "valid_csv_rows",
    "valid_rows",
]
