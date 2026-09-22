"""Shared GET-response cache for staff-directory payloads (not session data)."""

from __future__ import annotations

from typing import Any

from fastapi import Response

from app.core.ttl_cache import TtlCache

response_cache = TtlCache()

SUPPLIERS_PREFIX = "suppliers:"
PRODUCTS_KEY = "inventory:products"
PRODUCTS_PREFIX = "inventory:products"

# Catalog list: writes invalidate immediately; TTL is a safety net if a write
# is missed (another process, crash after commit). 60s is acceptable for
# procurement browsing.
SUPPLIERS_TTL_SECONDS = 60.0

# Stock is operationally hotter than vendor rates. Writes still invalidate.
# 30s covers a missed invalidation without letting the directory lie for long.
# Outbound quantity checks never read this cache — they query live stock.
PRODUCTS_TTL_SECONDS = 30.0


def suppliers_list_key(country: str | None, category: str | None) -> str:
    return f"{SUPPLIERS_PREFIX}list:{country or '*'}:{category or '*'}"


def read_cached_rows(response: Response, key: str) -> list[dict[str, Any]] | None:
    payload = response_cache.get(key)
    if payload is None:
        response.headers["X-Cache"] = "MISS"
        return None
    response.headers["X-Cache"] = "HIT"
    return payload


def store_cached_rows(key: str, rows: list[dict[str, Any]], ttl_seconds: float) -> None:
    response_cache.set(key, rows, ttl_seconds)


def invalidate_suppliers() -> None:
    response_cache.invalidate_prefix(SUPPLIERS_PREFIX)


def invalidate_products() -> None:
    response_cache.invalidate_prefix(PRODUCTS_PREFIX)
