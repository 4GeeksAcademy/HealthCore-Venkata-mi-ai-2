"""
HealthCore business performance pipeline — CLI entry.

Schedule (from PIPELINE_DESIGN.md): 06:00 UTC on the 1st of each month for the
previous UTC month (Monthly Clinic Supply Performance Report).

Run command:
  python data/pipelines/pipeline.py
  python data/pipelines/pipeline.py --month-start 2026-09-01
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow `python data/pipelines/pipeline.py` from the repo root.
_PACKAGE_DIR = Path(__file__).resolve().parent
if str(_PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(_PACKAGE_DIR))

from monthly_clinic_supply.flow import (  # noqa: E402
    monthly_clinic_supply_performance,
    parse_month_start,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the monthly clinic supply performance Prefect flow."
    )
    parser.add_argument(
        "--month-start",
        default=None,
        help="UTC month to recompute (YYYY-MM-DD). Default: previous UTC month.",
    )
    args = parser.parse_args(argv)
    month = parse_month_start(args.month_start)
    result = monthly_clinic_supply_performance(
        month_start=month,
        trigger="schedule" if args.month_start is None else "manual",
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
