"""Load CONTEXT seed suppliers into TinyDB and inventory into the active backend."""

from __future__ import annotations

import sys

from app.core.config import get_settings
from app.core.errors import StorageError
from app.database import init_dual_stores
from app.inventory.repo import seed_inventory
from app.suppliers_store import seed_suppliers


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
    return 0


if __name__ == "__main__":
    sys.exit(main())
