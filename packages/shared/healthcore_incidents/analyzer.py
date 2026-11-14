"""Official HealthCore incidents-file-analysis CSV validation and metrics.

Never print, log, or export patient_id values.
"""

from __future__ import annotations

import csv
import io
import re
from collections import Counter
from dataclasses import asdict, dataclass
from typing import Any

CSV_REQUIRED_FIELDS = (
    "incident_id",
    "date",
    "clinic_id",
    "country",
    "category",
    "description",
    "status",
    "patient_id",
)

ALLOWED_CSV_STATUSES = frozenset({"OPEN", "CLOSED", "DISCARDED"})
ALLOWED_CSV_CATEGORIES = frozenset(
    {
        "APPOINTMENT",
        "BILLING",
        "CLINICAL_CARE",
        "ACCESSIBILITY",
        "ADMINISTRATIVE",
    }
)

CLINIC_COUNTRY: dict[str, str] = {
    "US-TX-01": "US",
    "US-TX-02": "US",
    "US-TX-03": "US",
    "US-FL-01": "US",
    "US-FL-02": "US",
    "US-FL-03": "US",
    "US-GA-01": "US",
    "US-GA-02": "US",
    "US-GA-03": "US",
    "UK-LON-01": "UK",
    "UK-LON-02": "UK",
    "UK-MAN-01": "UK",
}

PATIENT_ID_RE = re.compile(r"^PAT-\d{6}$")

PROBLEM_INVALID_CLINIC = "invalid_or_missing_clinic_id"
PROBLEM_COUNTRY_MISMATCH = "country_clinic_mismatch"
PROBLEM_INVALID_CATEGORY = "invalid_or_missing_category"
PROBLEM_EMPTY_DESCRIPTION = "empty_or_short_description"
PROBLEM_MISSING_PATIENT = "missing_patient_id"
PROBLEM_CLOSED_NO_SCORE = "closed_without_satisfaction_score"
PROBLEM_SCORE_RANGE = "satisfaction_score_out_of_range"
PROBLEM_INVALID_STATUS = "status_not_allowed"
PROBLEM_MISSING_FIELD = "missing_required_field"


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


def validate_csv_row(row: dict[str, str]) -> list[str]:
    """Return problem type codes for a CSV row (empty => valid). Never includes PHI values."""
    problems: list[str] = []

    for name in CSV_REQUIRED_FIELDS:
        if name == "patient_id":
            continue
        if _is_blank(row.get(name)):
            if name == "description":
                problems.append(PROBLEM_EMPTY_DESCRIPTION)
            elif name == "clinic_id":
                problems.append(PROBLEM_INVALID_CLINIC)
            elif name == "category":
                problems.append(PROBLEM_INVALID_CATEGORY)
            elif name == "status":
                problems.append(PROBLEM_INVALID_STATUS)
            else:
                problems.append(PROBLEM_MISSING_FIELD)

    clinic_id = (row.get("clinic_id") or "").strip()
    country = (row.get("country") or "").strip()
    if clinic_id and clinic_id not in CLINIC_COUNTRY:
        if PROBLEM_INVALID_CLINIC not in problems:
            problems.append(PROBLEM_INVALID_CLINIC)
    elif clinic_id and country and CLINIC_COUNTRY.get(clinic_id) != country:
        problems.append(PROBLEM_COUNTRY_MISMATCH)

    category = (row.get("category") or "").strip()
    if category and category not in ALLOWED_CSV_CATEGORIES:
        if PROBLEM_INVALID_CATEGORY not in problems:
            problems.append(PROBLEM_INVALID_CATEGORY)

    description = (row.get("description") or "").strip()
    if description and len(description) < 5:
        if PROBLEM_EMPTY_DESCRIPTION not in problems:
            problems.append(PROBLEM_EMPTY_DESCRIPTION)

    status = (row.get("status") or "").strip()
    if status and status not in ALLOWED_CSV_STATUSES:
        if PROBLEM_INVALID_STATUS not in problems:
            problems.append(PROBLEM_INVALID_STATUS)

    patient_raw = (row.get("patient_id") or "").strip()
    if not patient_raw or not PATIENT_ID_RE.match(patient_raw):
        problems.append(PROBLEM_MISSING_PATIENT)

    score_raw = (row.get("satisfaction_score") or "").strip()
    if status == "CLOSED":
        if score_raw == "":
            problems.append(PROBLEM_CLOSED_NO_SCORE)
        else:
            try:
                score = float(score_raw)
                if score != int(score) or not 1 <= int(score) <= 5:
                    problems.append(PROBLEM_SCORE_RANGE)
            except ValueError:
                problems.append(PROBLEM_SCORE_RANGE)
    elif score_raw != "":
        try:
            score = float(score_raw)
            if score != int(score) or not 1 <= int(score) <= 5:
                problems.append(PROBLEM_SCORE_RANGE)
        except ValueError:
            problems.append(PROBLEM_SCORE_RANGE)

    # Deduplicate while preserving order
    seen: set[str] = set()
    ordered: list[str] = []
    for problem in problems:
        if problem not in seen:
            seen.add(problem)
            ordered.append(problem)
    return ordered


def analyze_rows(rows: list[dict[str, str]]) -> AnalysisResult:
    invalid_by_type: Counter[str] = Counter()
    by_category: Counter[str] = Counter()
    by_status: Counter[str] = Counter()
    satisfaction_scores: list[float] = []
    valid = 0
    invalid = 0

    for row in rows:
        problems = validate_csv_row(row)
        if problems:
            invalid += 1
            for problem in problems:
                invalid_by_type[problem] += 1
            continue

        valid += 1
        status = row["status"].strip()
        category = row["category"].strip()
        by_status[status] += 1
        by_category[category] += 1

        if status == "CLOSED":
            raw = (row.get("satisfaction_score") or "").strip()
            satisfaction_scores.append(float(raw))

    avg: float | None
    if satisfaction_scores:
        avg = round(sum(satisfaction_scores) / len(satisfaction_scores), 2)
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


def valid_csv_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [row for row in rows if not validate_csv_row(row)]


def parse_csv_rows(text: str) -> list[dict[str, str]]:
    if text is None or text.strip() == "":
        raise AnalysisError("File is empty.")

    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise AnalysisError("CSV has no header row.")

    headers = [(h or "").strip() for h in reader.fieldnames]
    if not any(headers):
        raise AnalysisError("CSV has no header row.")

    missing_cols = [c for c in CSV_REQUIRED_FIELDS if c not in headers]
    if missing_cols:
        raise AnalysisError(
            "Incorrect CSV format: missing required column(s): " + ", ".join(missing_cols)
        )

    rows: list[dict[str, str]] = []
    for raw in reader:
        rows.append(
            {(k or "").strip(): (v if v is not None else "") for k, v in raw.items()}
        )

    if not rows:
        raise AnalysisError("CSV contains no data rows.")

    return rows


def analyze_csv_text(text: str) -> AnalysisResult:
    return analyze_rows(parse_csv_rows(text))


def results_to_metric_rows(result: AnalysisResult) -> list[dict[str, str]]:
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
