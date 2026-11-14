#!/usr/bin/env python3
"""Load historical HealthCore incidents into the centralized incident manager.

Reads the official analyzer CSV, validates with shared logic, applies BRIEFING
transforms, and inserts with origin=customer. Idempotent on source_key
(CSV incident_id). Never prints patient_id values.

Usage:
  python scripts/seed_incidents.py
  python scripts/seed_incidents.py scripts/samples/incidents-healthcore.csv
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "services" / "api"
SHARED = ROOT / "packages" / "shared"
for path in (str(API_ROOT), str(SHARED)):
    if path not in sys.path:
        sys.path.insert(0, path)

from healthcore_incidents import (  # noqa: E402
    AnalysisError,
    parse_csv_rows,
    transform_valid_rows,
)

from app import incidents_store  # noqa: E402


DEFAULT_CSV = ROOT / "scripts" / "samples" / "incidents-healthcore.csv"


def main(argv: list[str]) -> int:
    csv_path = Path(argv[1]) if len(argv) > 1 else DEFAULT_CSV
    if not csv_path.is_file():
        print("File not found.", file=sys.stderr)
        return 1

    try:
        text = csv_path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        print(f"Could not read CSV: {exc}", file=sys.stderr)
        return 1
    except UnicodeDecodeError:
        print("Incorrect format: file must be UTF-8 encoded CSV.", file=sys.stderr)
        return 1

    try:
        rows = parse_csv_rows(text)
    except AnalysisError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    transformed, rejected = transform_valid_rows(rows)
    inserted = 0
    skipped = 0

    try:
        for payload in transformed:
            outcome = incidents_store.seed_incident(payload)
            if outcome == "inserted":
                inserted += 1
            else:
                skipped += 1
    except Exception as exc:  # noqa: BLE001 — surface storage failure, exit non-zero
        print(f"Unable to write incidents: {type(exc).__name__}", file=sys.stderr)
        return 1

    reason_counts: Counter[str] = Counter()
    for item in rejected:
        for reason in item["reason"].split(","):
            reason_counts[reason] += 1

    print("=" * 56)
    print("HealthCore incident seed")
    print("=" * 56)
    print(f"Source CSV ............... {csv_path.name}")
    print(f"Rows read ................ {len(rows)}")
    print(f"Valid transformed ........ {len(transformed)}")
    print(f"Rejected / invalid ....... {len(rejected)}")
    print(f"Inserted ................. {inserted}")
    print(f"Skipped (already present)  {skipped}")
    print("-" * 56)
    print("Rejected by reason (no PHI values):")
    if not reason_counts:
        print("  (none)")
    else:
        for reason, count in sorted(reason_counts.items()):
            print(f"  {reason:<36} {count:>6}")
            matching = [r["incident_id"] for r in rejected if reason in r["reason"]]
            if matching:
                print(f"    ids: {', '.join(matching[:12])}" + ("…" if len(matching) > 12 else ""))
    print("=" * 56)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
