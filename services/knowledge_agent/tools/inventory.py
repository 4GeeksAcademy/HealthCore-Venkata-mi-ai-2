"""Inventory lookup — reads stock from the HealthCore inventory manager. Stock only."""

from __future__ import annotations

import re
import time

from pydantic import ValidationError

from .contracts import InventoryLookupInput, InventoryLookupOutput, ProductStock
from .session import ReadOnlyApiSession, ServiceCredentials, ToolCallError

TOOL_NAME = "inventory_lookup"
PRODUCTS_PATH = "/inventory/products"
MAX_MATCHES = 5

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_IGNORED = frozenset("a an any the of for in on box boxes pack packs some stock supply supplies".split())


def _stem(token: str) -> str:
    return token[:-1] if len(token) > 3 and token.endswith("s") and not token.endswith("ss") else token


def _tokens(text: str) -> set[str]:
    return {_stem(t) for t in _TOKEN_RE.findall(text.lower()) if t not in _IGNORED}


def matches(product_query: str, name: str, sku: str) -> bool:
    """Every meaningful query word is in the product name, or the query is the SKU."""
    if product_query.strip().lower() == sku.lower():
        return True
    wanted = _tokens(product_query)
    return bool(wanted) and wanted <= _tokens(name)


class InventoryLookupTool:
    """``GET /inventory/products``, then match the requested product by name or SKU."""

    name = TOOL_NAME

    def __init__(self, session: ReadOnlyApiSession | None) -> None:
        self.session = session

    @classmethod
    def from_env(cls) -> InventoryLookupTool:
        credentials = ServiceCredentials.from_env()
        return cls(ReadOnlyApiSession(credentials) if credentials else None)

    def __call__(self, request: InventoryLookupInput) -> InventoryLookupOutput:
        if self.session is None:
            return InventoryLookupOutput(status="auth_failed", endpoint=PRODUCTS_PATH)

        started = time.perf_counter()

        def elapsed() -> float:
            return round((time.perf_counter() - started) * 1000, 1)

        try:
            body, http_status = self.session.get_json(PRODUCTS_PATH)
        except ToolCallError as exc:
            return InventoryLookupOutput(
                status=exc.status, http_status=exc.http_status, latency_ms=elapsed(), endpoint=PRODUCTS_PATH
            )
        try:
            products = tuple(
                ProductStock(
                    name=str(row["name"]),
                    sku=str(row["sku"]),
                    category=str(row.get("category") or ""),
                    current_stock=int(row["current_stock"]),
                    threshold=int(row["threshold"]),
                    below_threshold=int(row["current_stock"]) < int(row["threshold"]),
                )
                for row in body
                if matches(request.product_query, str(row["name"]), str(row["sku"]))
            )
        except (ValidationError, KeyError, TypeError, ValueError):
            return InventoryLookupOutput(
                status="bad_response", http_status=http_status, latency_ms=elapsed(), endpoint=PRODUCTS_PATH
            )
        return InventoryLookupOutput(
            status="ok" if products else "not_found",
            products=products[:MAX_MATCHES],
            http_status=http_status,
            latency_ms=elapsed(),
            endpoint=PRODUCTS_PATH,
        )
