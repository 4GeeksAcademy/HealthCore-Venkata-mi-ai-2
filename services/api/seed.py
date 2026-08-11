"""Load CONTEXT seed suppliers into TinyDB without creating duplicates."""

from __future__ import annotations

from app.suppliers_store import seed_suppliers


def main() -> None:
    inserted = seed_suppliers()
    print(f"Inserted {inserted} supplier(s).")


if __name__ == "__main__":
    main()
