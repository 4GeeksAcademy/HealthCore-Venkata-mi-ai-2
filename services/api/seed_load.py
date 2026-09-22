"""Grow supplier + inventory tables so cache timing is measurable."""

from __future__ import annotations

import sys

from app.core.errors import StorageError
from app.database import init_dual_stores
from app.load_seed import seed_inventory_load, seed_supplier_load
from app.suppliers_store import seed_suppliers
from app.inventory.service import seed_inventory


def main() -> int:
    try:
        catalog = seed_suppliers()
        extra_vendors = seed_supplier_load()
    except StorageError:
        print("Could not seed suppliers. Check that the data directory is writable.", file=sys.stderr)
        return 1
    except OSError:
        print("Could not seed suppliers because of a file error.", file=sys.stderr)
        return 1

    print(f"Inserted {catalog} CONTEXT supplier(s) and {extra_vendors} load vendor(s).")

    try:
        init_dual_stores()
        catalog_products = seed_inventory()
        extra_products = seed_inventory_load()
    except StorageError:
        print("Could not seed inventory. Check that the data directory is writable.", file=sys.stderr)
        return 1
    except OSError:
        print("Could not seed inventory because of a file error.", file=sys.stderr)
        return 1

    print(
        f"Inserted {catalog_products} CONTEXT product(s) and {extra_products} load product(s)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
