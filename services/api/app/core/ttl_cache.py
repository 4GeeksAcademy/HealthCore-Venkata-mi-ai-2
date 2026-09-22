"""In-process dictionary cache with TTL expiry and prefix invalidation."""

from __future__ import annotations

import threading
import time
from typing import Any


class TtlCache:
    """Thread-safe in-memory cache. Expired keys are dropped on read."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._store: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Any | None:
        now = time.monotonic()
        with self._lock:
            item = self._store.get(key)
            if item is None:
                return None
            expires_at, value = item
            if expires_at <= now:
                del self._store[key]
                return None
            return value

    def set(self, key: str, value: Any, ttl_seconds: float) -> None:
        expires_at = time.monotonic() + ttl_seconds
        with self._lock:
            self._store[key] = (expires_at, value)

    def invalidate_prefix(self, prefix: str) -> None:
        with self._lock:
            keys = [key for key in self._store if key.startswith(prefix)]
            for key in keys:
                del self._store[key]

    def clear(self) -> None:
        with self._lock:
            self._store.clear()
