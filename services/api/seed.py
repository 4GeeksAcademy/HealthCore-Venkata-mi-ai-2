"""Load CONTEXT seed suppliers into TinyDB, inventory into the active backend, and
historical incidents through the shared CSV → manager transform path."""

from __future__ import annotations

import sys
from pathlib import Path

_SHARED = Path(__file__).resolve().parents[2] / "packages" / "shared"
if str(_SHARED) not in sys.path:
    sys.path.insert(0, str(_SHARED))

from healthcore_incidents import AnalysisError, parse_csv_rows, transform_valid_rows

from app.core.config import get_settings
from app.core.errors import StorageError
from app.database import init_dual_stores
from app.incidents_store import seed_incident
from app.inventory.repo import seed_inventory
from app.suppliers_store import seed_suppliers

SAMPLE_INCIDENTS = Path(__file__).resolve().parents[2] / "scripts" / "samples" / "incidents-healthcore.csv"


def main() -> int:
    try:
        inserted = seed_suppliers()
    except StorageError:
        print("Could not seed suppliers. Check that the data directory is writable.", file=sys.stderr)
        return 1
    except OSError:
        print("Could not seed suppliers because of a file error.", file=sys.stderr)
        return 1

    print(f"Inserted {inserted} supplier(s).")

    try:
        init_dual_stores()
        inventory_inserted = seed_inventory()
    except StorageError:
        print("Could not seed inventory. Check that the data directory is writable.", file=sys.stderr)
        return 1
    except OSError:
        print("Could not seed inventory because of a file error.", file=sys.stderr)
        return 1

    backend = get_settings().inventory_backend
    print(
        f"Inserted {inventory_inserted} inventory product(s) "
        f"via INVENTORY_BACKEND={backend} (stock from inbound − outbound)."
    )

    try:
        rows = parse_csv_rows(SAMPLE_INCIDENTS.read_text(encoding="utf-8-sig"))
        transformed, rejected = transform_valid_rows(rows)
        stored = 0
        skipped = 0
        for payload in transformed:
            outcome = seed_incident(payload)
            if outcome == "inserted":
                stored += 1
            else:
                skipped += 1
    except (OSError, AnalysisError):
        print("Could not read the sample incident CSV.", file=sys.stderr)
        return 1
    except StorageError:
        print("Could not seed incidents. Check that the data directory is writable.", file=sys.stderr)
        return 1
    print(
        f"Seeded {stored} incident(s) from {SAMPLE_INCIDENTS.name} "
        f"({skipped} skipped, {len(rejected)} rejected)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
