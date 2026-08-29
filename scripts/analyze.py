#!/usr/bin/env python3
"""CLI entry for HealthCore Incident File Analyzer.

Uses shared validation/metrics from services/api (no duplicated logic).

Usage:
  python scripts/analyze.py scripts/samples/incidents-healthcore.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "services" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.incident_analysis import (  # noqa: E402
    AnalysisError,
    AnalysisResult,
    analyze_csv_text,
    results_to_csv_string,
)


def print_summary(result: AnalysisResult) -> None:
    width = 56
    print("=" * width)
    print("HealthCore Incident Analysis Summary".center(width))
    print("=" * width)
    print(f"{'Total processed':<32} {result.total_processed:>10}")
    print(f"{'Valid':<32} {result.total_valid:>10}")
    print(f"{'Invalid':<32} {result.total_invalid:>10}")
    print("-" * width)

    print("Invalid records by problem type")
    if not result.invalid_by_type:
        print(f"  {'(none)':<30} {0:>10}")
    else:
        for key, value in result.invalid_by_type.items():
            print(f"  {key:<30} {value:>10}")
    print("-" * width)

    print("Breakdown by category (valid only)")
    for key, value in result.by_category.items():
        print(f"  {key:<30} {value:>10}")
    print("-" * width)

    print("Breakdown by status (valid only)")
    for key, value in result.by_status.items():
        print(f"  {key:<30} {value:>10}")
    print("-" * width)

    avg = result.avg_satisfaction_closed
    avg_display = "n/a" if avg is None else f"{avg}"
    print(f"{'Avg satisfaction (closed)':<32} {avg_display:>10}")
    print(
        f"{'Closed cases with score':<32} {result.closed_with_score_count:>10}"
    )
    print("=" * width)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(
            "Usage: python analyze.py <path-to-csv>",
            file=sys.stderr,
        )
        return 1

    path = Path(argv[1])
    if not path.is_file():
        print("File not found.", file=sys.stderr)
        return 1

    try:
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        print("Could not read file: the CSV must be UTF-8 encoded.", file=sys.stderr)
        return 1
    except OSError:
        print("Could not read file.", file=sys.stderr)
        return 1

    try:
        result = analyze_csv_text(text)
    except AnalysisError:
        print("Could not analyze the CSV. Check the file format and try again.", file=sys.stderr)
        return 1

    print_summary(result)

    try:
        answer = input("export results to CSV? (y / n) ").strip().lower()
    except EOFError:
        answer = "n"

    if answer == "y":
        out = Path.cwd() / "results.csv"
        try:
            out.write_text(results_to_csv_string(result), encoding="utf-8")
        except OSError:
            print("Could not write results.csv.", file=sys.stderr)
            return 1
        print(f"Wrote {out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
