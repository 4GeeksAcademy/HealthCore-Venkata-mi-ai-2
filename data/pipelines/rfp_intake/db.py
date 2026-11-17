"""SQLModel engine for RFP tickets. Tests inject SQLite; runtime uses Supabase."""

from __future__ import annotations

import os

from sqlalchemy.engine import Engine
from sqlalchemy.pool import NullPool, StaticPool
from sqlmodel import SQLModel, create_engine

from .errors import RfpDatabaseUnconfigured, RfpStorageError

_engine: Engine | None = None


def resolve_url() -> str:
    explicit = os.getenv("RFP_DATABASE_URL", "").strip()
    if explicit:
        return explicit
    try:
        from app.core.config import get_settings

        settings = get_settings()
        if settings.supabase_database_url:
            return settings.supabase_database_url
        database_url = settings.database_url or ""
        if settings.inventory_backend == "supabase" and database_url.startswith("postgres"):
            return database_url
    except Exception:
        pass
    database_url = os.getenv("DATABASE_URL", "").strip()
    if database_url.startswith("postgres"):
        return database_url
    raise RfpDatabaseUnconfigured("rfp_database_unconfigured")


def configure_engine(engine: Engine | None) -> None:
    global _engine
    _engine = engine


def reset_engine() -> None:
    global _engine
    if _engine is not None:
        _engine.dispose()
    _engine = None


def get_engine() -> Engine:
    global _engine
    if _engine is not None:
        return _engine
    try:
        url = resolve_url()
    except RfpDatabaseUnconfigured:
        raise
    kwargs: dict = {}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
        if url in {"sqlite://", "sqlite:///:memory:"} or ":memory:" in url:
            kwargs["poolclass"] = StaticPool
    elif "pooler.supabase.com" in url:
        kwargs["poolclass"] = NullPool
    try:
        _engine = create_engine(url, **kwargs)
    except Exception as exc:
        raise RfpStorageError("rfp_engine") from exc
    return _engine


def init_schema() -> None:
    from .models import RfpDepartmentSection, RfpMetadata, RfpTicket

    engine = get_engine()
    try:
        SQLModel.metadata.create_all(
            engine,
            tables=[
                RfpTicket.__table__,
                RfpMetadata.__table__,
                RfpDepartmentSection.__table__,
            ],
        )
    except RfpDatabaseUnconfigured:
        raise
    except Exception as exc:
        raise RfpStorageError("rfp_schema") from exc
