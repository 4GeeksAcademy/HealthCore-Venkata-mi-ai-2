"""Domain errors for HealthCore API persistence."""

from __future__ import annotations


class StorageError(Exception):
    """TinyDB, SQLModel, or filesystem failure that must not leak internals to clients."""
