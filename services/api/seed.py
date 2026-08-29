"""Load CONTEXT seed suppliers into TinyDB without creating duplicates."""

from __future__ import annotations

import sys

from app.core.errors import StorageError
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
    return 0


if __name__ == "__main__":
    sys.exit(main())
