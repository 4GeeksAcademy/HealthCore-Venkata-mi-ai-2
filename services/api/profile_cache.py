"""Measure GET cache miss vs hit on isolated SQLite + TinyDB (no live PHI)."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

# Match pytest isolation so this never touches live stores.
os.environ["JWT_SECRET_KEY"] = "unit-test-jwt-secret-do-not-use-live"
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
os.environ["DATABASE_URL"] = "sqlite://"

from fastapi.testclient import TestClient  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.database import reset_engine  # noqa: E402
from app.load_seed import seed_inventory_load, seed_supplier_load  # noqa: E402
from app.main import app  # noqa: E402
from app.stores import auth_store  # noqa: E402
from app import suppliers_store  # noqa: E402


def _timed_get(client: TestClient, path: str, headers: dict[str, str]) -> tuple[float, str]:
    start = time.perf_counter()
    response = client.get(path, headers=headers)
    elapsed_ms = (time.perf_counter() - start) * 1000
    if response.status_code != 200:
        raise RuntimeError(f"{path} returned {response.status_code}")
    return elapsed_ms, response.headers.get("x-cache", "")


def main() -> int:
    tmp = Path(".profile-cache-tmp")
    try:
        tmp.mkdir(exist_ok=True)
        auth_dir = tmp / "auth"
        suppliers_dir = tmp / "suppliers"
        auth_dir.mkdir(exist_ok=True)
        suppliers_dir.mkdir(exist_ok=True)
        auth_store.DATA_DIR = auth_dir
        auth_store.DB_PATH = auth_dir / "auth.json"
        suppliers_store.DATA_DIR = suppliers_dir
        suppliers_store.DB_PATH = suppliers_dir / "suppliers.json"
        get_settings.cache_clear()
        reset_engine()

        with TestClient(app) as client:
            created = client.post(
                "/users",
                json={
                    "email": "qa.staff@healthcore.example",
                    "password": "StaffPass9",
                    "name": "QA Staff",
                    "phone": "",
                    "address": "",
                },
            )
            if created.status_code != 201:
                print("Could not register profile user for timing.", file=sys.stderr)
                return 1
            token = client.post(
                "/auth/login",
                json={"email": "qa.staff@healthcore.example", "password": "StaffPass9"},
            ).json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            vendor_count = seed_supplier_load(200)
            product_count = seed_inventory_load(40, 20, 12)

            miss_suppliers, miss_flag = _timed_get(client, "/suppliers", headers)
            hit_suppliers, hit_flag = _timed_get(client, "/suppliers", headers)
            miss_products, miss_p_flag = _timed_get(client, "/inventory/products", headers)
            hit_products, hit_p_flag = _timed_get(client, "/inventory/products", headers)

            listed = client.get("/suppliers", headers=headers).json()
            products = client.get("/inventory/products", headers=headers).json()

            print(f"Load vendors inserted: {vendor_count}; listed suppliers: {len(listed)}")
            print(f"Load products inserted: {product_count}; listed products: {len(products)}")
            print(f"GET /suppliers miss {miss_flag}: {miss_suppliers:.1f}ms")
            print(f"GET /suppliers hit  {hit_flag}: {hit_suppliers:.1f}ms")
            print(f"GET /inventory/products miss {miss_p_flag}: {miss_products:.1f}ms")
            print(f"GET /inventory/products hit  {hit_p_flag}: {hit_products:.1f}ms")
        return 0
    except OSError:
        print("Could not write isolated timing files.", file=sys.stderr)
        return 1
    finally:
        reset_engine()
        get_settings.cache_clear()


if __name__ == "__main__":
    sys.exit(main())
