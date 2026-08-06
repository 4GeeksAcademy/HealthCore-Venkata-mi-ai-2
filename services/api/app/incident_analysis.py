"""Shared incident CSV validation and metrics (CONTEXT: IncidentFileAnalyzer.md)."""

from __future__ import annotations

import csv
import io
from collections import Counter
from dataclasses import asdict, dataclass
from typing import Any

REQUIRED_FIELDS = (
    "incident_id",
    "reported_date",
    "category",
    "status",
    "location_id",
)

ALLOWED_STATUSES = frozenset({"open", "closed", "discarded"})
ALLOWED_CATEGORIES = frozenset(
    {
        "clinical_safety",
        "facilities",
        "it_systems",
        "billing_access",
        "patient_experience",
        "workforce",
    }
)

PROBLEM_MISSING = "missing_required_field"
PROBLEM_STATUS = "status_not_allowed"
PROBLEM_CATEGORY = "category_not_allowed"


@dataclass
class AnalysisResult:
    total_processed: int
    total_valid: int
    total_invalid: int
    invalid_by_type: dict[str, int]
    by_category: dict[str, int]
    by_status: dict[str, int]
    avg_satisfaction_closed: float | None
    closed_with_score_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class AnalysisError(ValueError):
    """Raised when the CSV cannot be analyzed (empty, bad format)."""


def _is_blank(value: str | None) -> bool:
    return value is None or str(value).strip() == ""


def validate_row(row: dict[str, str]) -> list[str]:
    """Return list of problem types for a row (empty => valid)."""
    problems: list[str] = []

    for name in REQUIRED_FIELDS:
        if _is_blank(row.get(name)):
            problems.append(PROBLEM_MISSING)
            break

    status = (row.get("status") or "").strip()
    if status and status not in ALLOWED_STATUSES:
        problems.append(PROBLEM_STATUS)

    category = (row.get("category") or "").strip()
    if category and category not in ALLOWED_CATEGORIES:
        problems.append(PROBLEM_CATEGORY)

    return problems


def analyze_rows(rows: list[dict[str, str]]) -> AnalysisResult:
    invalid_by_type: Counter[str] = Counter()
    by_category: Counter[str] = Counter()
    by_status: Counter[str] = Counter()
    satisfaction_scores: list[float] = []
    valid = 0
    invalid = 0

    for row in rows:
        problems = validate_row(row)
        if problems:
            invalid += 1
            for p in problems:
                invalid_by_type[p] += 1
            continue

        valid += 1
        status = row["status"].strip()
        category = row["category"].strip()
        by_status[status] += 1
        by_category[category] += 1

        if status == "closed":
            raw = (row.get("satisfaction_score") or "").strip()
            if raw != "":
                try:
                    satisfaction_scores.append(float(raw))
                except ValueError:
                    pass

    avg: float | None
    if satisfaction_scores:
        avg = round(sum(satisfaction_scores) / len(satisfaction_scores), 4)
    else:
        avg = None

    return AnalysisResult(
        total_processed=len(rows),
        total_valid=valid,
        total_invalid=invalid,
        invalid_by_type=dict(sorted(invalid_by_type.items())),
        by_category=dict(sorted(by_category.items())),
        by_status=dict(sorted(by_status.items())),
        avg_satisfaction_closed=avg,
        closed_with_score_count=len(satisfaction_scores),
    )


def analyze_csv_text(text: str) -> AnalysisResult:
    if text is None or text.strip() == "":
        raise AnalysisError("File is empty.")

    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise AnalysisError("CSV has no header row.")

    headers = [h.strip() if h else "" for h in reader.fieldnames]
    if not any(headers):
        raise AnalysisError("CSV has no header row.")

    missing_cols = [c for c in REQUIRED_FIELDS if c not in headers]
    if missing_cols:
        raise AnalysisError(
            "Incorrect CSV format: missing required column(s): "
            + ", ".join(missing_cols)
        )

    rows: list[dict[str, str]] = []
    for raw in reader:
        rows.append(
            {(k or "").strip(): (v if v is not None else "") for k, v in raw.items()}
        )

    if not rows:
        raise AnalysisError("CSV contains no data rows.")

    return analyze_rows(rows)


def results_to_metric_rows(result: AnalysisResult) -> list[dict[str, str]]:
    """One row per metric for results.csv export."""
    rows: list[dict[str, str]] = [
        {"metric": "total_processed", "key": "", "value": str(result.total_processed)},
        {"metric": "total_valid", "key": "", "value": str(result.total_valid)},
        {"metric": "total_invalid", "key": "", "value": str(result.total_invalid)},
        {
            "metric": "avg_satisfaction_closed",
            "key": "",
            "value": (
                ""
                if result.avg_satisfaction_closed is None
                else str(result.avg_satisfaction_closed)
            ),
        },
        {
            "metric": "closed_with_score_count",
            "key": "",
            "value": str(result.closed_with_score_count),
        },
    ]
    for key, value in result.invalid_by_type.items():
        rows.append({"metric": "invalid_by_type", "key": key, "value": str(value)})
    for key, value in result.by_category.items():
        rows.append({"metric": "by_category", "key": key, "value": str(value)})
    for key, value in result.by_status.items():
        rows.append({"metric": "by_status", "key": key, "value": str(value)})
    return rows


def results_to_csv_string(result: AnalysisResult) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=["metric", "key", "value"])
    writer.writeheader()
    writer.writerows(results_to_metric_rows(result))
    return buffer.getvalue()
