"""Load CONTEXT seed suppliers into TinyDB, inventory into the active backend, and the
sample incident CSV through the analyzer's own parse/validate/upsert path."""

from __future__ import annotations

import sys
from pathlib import Path

from app.core.config import get_settings
from app.core.errors import StorageError
from app.database import init_dual_stores
from app.incident_analysis import AnalysisError, parse_csv_rows, valid_rows
from app.incidents_store import upsert_incidents
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
        rows = valid_rows(parse_csv_rows(SAMPLE_INCIDENTS.read_text(encoding="utf-8-sig")))
        stored = upsert_incidents(rows, source_file=SAMPLE_INCIDENTS.name)
    except (OSError, AnalysisError):
        print("Could not read the sample incident CSV.", file=sys.stderr)
        return 1
    except StorageError:
        print("Could not seed incidents. Check that the data directory is writable.", file=sys.stderr)
        return 1
    print(f"Stored {stored} valid incident(s) from {SAMPLE_INCIDENTS.name}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
