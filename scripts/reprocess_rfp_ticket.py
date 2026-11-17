"""Re-run intake for one ticket. Usage: uv run python scripts/reprocess_rfp_ticket.py TICKET_ID"""

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
from data.pipelines.rfp_intake.runner import execute_ticket  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Re-run HealthCore RFP intake for one ticket.")
    parser.add_argument("ticket_id")
    args = parser.parse_args()
    service.init_schema()
    from data.pipelines.rfp_intake import store

    ticket = store.get_ticket(args.ticket_id)
    if ticket is None:
        print("ticket not found")
        return 1
    if ticket.status not in {"failed", "discarded"}:
        print("ticket cannot be reprocessed from its current status")
        return 1
    if not store.reset_for_reprocess(args.ticket_id):
        print("ticket cannot be reprocessed from its current status")
        return 1
    status = execute_ticket(args.ticket_id)
    print(f"ticket_id={args.ticket_id} status={status}")
    return 0 if status in {"intake_complete", "discarded"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
