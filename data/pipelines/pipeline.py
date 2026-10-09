"""
HealthCore business performance pipeline — main flow + CLI entry.

Schedule (from PIPELINE_DESIGN.md): 06:00 UTC on the 1st of each month for the
previous UTC month (Monthly Clinic Supply Performance Report).

Run command:
  python data/pipelines/pipeline.py
  python data/pipelines/pipeline.py --month-start 2026-09-01
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import date
from pathlib import Path
from typing import Any

# Allow `python data/pipelines/pipeline.py` from the repo root.
_PACKAGE_DIR = Path(__file__).resolve().parent
if str(_PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(_PACKAGE_DIR))

from prefect import flow  # noqa: E402

from monthly_clinic_supply.clinics import CLINIC_ALLOWLIST, FLOW_NAME  # noqa: E402
from monthly_clinic_supply.dates import parse_month_start  # noqa: E402
from monthly_clinic_supply.db import get_engine, init_reporting_schema  # noqa: E402
from monthly_clinic_supply.runs import begin_run, finish_run, update_run  # noqa: E402
from monthly_clinic_supply.subflows import (  # noqa: E402
    extract_clinic_supply_telemetry,
    load_monthly_clinic_supply_performance_subflow,
    snapshot_monthly_clinic_supply_eval,
    transform_monthly_clinic_supply_kpis,
)
from monthly_clinic_supply.transform import transform_stats  # noqa: E402

logger = logging.getLogger("healthcore.pipeline.monthly_clinic_supply")


@flow(name=FLOW_NAME)
def monthly_clinic_supply_performance(
    month_start: str | date | None = None,
    trigger: str = "schedule",
) -> dict[str, Any]:
    """Main ETL: extract → transform → load subflows. Optional eval cannot stop the flow."""
    target = parse_month_start(month_start)
    init_reporting_schema(get_engine())
    run_id = begin_run(target, trigger=trigger, engine=get_engine())

    try:
        update_run(run_id, {"phase": "extract"})
        extracted = extract_clinic_supply_telemetry(target)
        update_run(
            run_id,
            {
                "phase": "transform",
                "records_extracted": extracted["records_extracted"],
                "records_deduped": extracted["records_deduped"],
                "duplicate_event_id_count": extracted["duplicate_event_id_count"],
                "records_rejected": extracted["records_rejected"],
                "source": extracted["source"],
            },
        )

        rows = transform_monthly_clinic_supply_kpis(extracted, target)
        stats = transform_stats(extracted.get("events") or [])
        update_run(
            run_id,
            {
                "phase": "load",
                "distinct_clinic_count": stats["distinct_clinic_count"],
                "distinct_session_count": stats["distinct_session_count"],
                "distinct_request_id_count": stats["distinct_request_id_count"],
            },
        )

        loaded = load_monthly_clinic_supply_performance_subflow(rows)

        # Optional / non-critical: failure is logged; ETL still Completes.
        snapshot_state = snapshot_monthly_clinic_supply_eval(
            rows, target, return_state=True
        )
        if snapshot_state.is_failed():
            logger.warning(
                "optional snapshot_monthly_clinic_supply_eval failed run_id=%s month_start=%s",
                run_id,
                target.isoformat(),
            )

        finish_run(
            run_id,
            status="Completed",
            phase="load",
            records_extracted=extracted["records_extracted"],
            records_deduped=extracted["records_deduped"],
            duplicate_event_id_count=extracted["duplicate_event_id_count"],
            records_rejected=extracted["records_rejected"],
            records_loaded=loaded,
            distinct_clinic_count=stats["distinct_clinic_count"],
            distinct_session_count=stats["distinct_session_count"],
            distinct_request_id_count=stats["distinct_request_id_count"],
            source=extracted["source"],
        )
        return {
            "run_id": run_id,
            "month_start": target.isoformat(),
            "status": "Completed",
            "records_loaded": loaded,
            "clinic_count": len(CLINIC_ALLOWLIST),
            "source": extracted["source"],
        }
    except Exception as exc:
        finish_run(
            run_id,
            status="Failed",
            phase="load",
            error_message=str(exc)[:500],
        )
        raise


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
