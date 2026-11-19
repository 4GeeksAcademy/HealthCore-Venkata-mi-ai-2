"""Draft proposal sections for one intake-complete ticket.

Usage: uv run python scripts/draft_rfp_ticket.py TICKET_ID
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from dotenv import load_dotenv

load_dotenv(REPO / ".env")

from data.pipelines.rfp_intake import service  # noqa: E402
from data.pipelines.rfp_intake.errors import RfpStorageError  # noqa: E402
from data.pipelines.rfp_response.runner import execute_response  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Draft a HealthCore pricing proposal for one ticket.")
    parser.add_argument("ticket_id")
    args = parser.parse_args()
    try:
        service.init_schema()
    except RfpStorageError:
        print("RFP storage is not available.", file=sys.stderr)
        return 1
    from data.pipelines.rfp_intake import store

    try:
        ticket = store.get_ticket(args.ticket_id)
    except RfpStorageError:
        print("The ticket could not be read.", file=sys.stderr)
        return 1
    if ticket is None:
        print("ticket not found", file=sys.stderr)
        return 1
    if ticket.status != "intake_complete" or not ticket.handoff_ready:
        print("ticket is not ready for a proposal draft", file=sys.stderr)
        return 1
    try:
        status = execute_response(args.ticket_id)
    except RfpStorageError:
        print("The ticket could not be saved.", file=sys.stderr)
        return 1
    print(f"ticket_id={args.ticket_id} status={status}")
    return 0 if status in {"under_evaluation", "needs_human_review"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
