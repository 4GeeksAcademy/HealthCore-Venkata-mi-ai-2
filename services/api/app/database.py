"""Dual-store connections: TinyDB (auth) + SQLModel engine (inventory / Supabase)."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import NullPool, StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.core.config import get_settings
from app.core.errors import StorageError
from app.stores import auth_store

_engine: Engine | None = None


def get_engine() -> Engine:
    """Return the SQLModel engine for inventory (Supabase or test SQLite). Not a session."""
    global _engine
    if _engine is None:
        url = get_settings().database_url
        kwargs: dict = {}
        if url.startswith("sqlite"):
            kwargs["connect_args"] = {"check_same_thread": False}
            if url in {"sqlite://", "sqlite:///:memory:"}:
                kwargs["poolclass"] = StaticPool
        elif "pooler.supabase.com" in url:
            kwargs["poolclass"] = NullPool
        try:
            _engine = create_engine(url, **kwargs)
        except SQLAlchemyError as exc:
            raise StorageError("Unable to access inventory data store") from exc
    return _engine


def reset_engine() -> None:
    """Dispose the cached engine (tests only). Does not keep a Session."""
    global _engine
    if _engine is not None:
        _engine.dispose()
        _engine = None


def _postgres_table_exists(conn, name: str) -> bool:
    row = conn.execute(
        text(
            "select 1 from information_schema.tables "
            "where table_schema = 'public' and table_name = :name"
        ),
        {"name": name},
    ).first()
    return row is not None


def _postgres_columns(conn, table: str) -> set[str]:
    rows = conn.execute(
        text(
            "select column_name from information_schema.columns "
            "where table_schema = 'public' and table_name = :table"
        ),
        {"table": table},
    )
    return {str(row[0]) for row in rows}


def _postgres_row_count(conn, name: str) -> int:
    value = conn.execute(text(f'SELECT COUNT(*) FROM "{name}"')).scalar()
    return int(value or 0)


def _adopt_readable_table(conn, old: str, new: str) -> None:
    """Rename mashed SQLModel names. If create_all already made empty snake_case tables, drop those and keep the data."""
    old_exists = _postgres_table_exists(conn, old)
    new_exists = _postgres_table_exists(conn, new)
    if old_exists and not new_exists:
        conn.execute(text(f'ALTER TABLE "{old}" RENAME TO "{new}"'))
        return
    if old_exists and new_exists:
        old_n = _postgres_row_count(conn, old)
        new_n = _postgres_row_count(conn, new)
        if new_n == 0:
            conn.execute(text(f'DROP TABLE "{new}" CASCADE'))
            conn.execute(text(f'ALTER TABLE "{old}" RENAME TO "{new}"'))
        elif old_n == 0:
            conn.execute(text(f'DROP TABLE "{old}" CASCADE'))


def migrate_postgres_inventory(engine: Engine) -> None:
    """Rename mashed SQLModel names and add product labels so Table Editor matches the UI."""
    with engine.begin() as conn:
        # Children first so DROP CASCADE on an empty parent cannot remove order tables.
        for old, new in (
            ("inboundorder", "inbound_order"),
            ("outboundorder", "outbound_order"),
            ("medicalsupply", "medical_supply"),
        ):
            _adopt_readable_table(conn, old, new)

        for table in ("inbound_order", "outbound_order"):
            if not _postgres_table_exists(conn, table):
                continue
            cols = _postgres_columns(conn, table)
            if "product_name" not in cols:
                conn.execute(
                    text(f'ALTER TABLE "{table}" ADD COLUMN product_name VARCHAR NOT NULL DEFAULT \'\'' )
                )
            if "sku" not in cols:
                conn.execute(
                    text(f'ALTER TABLE "{table}" ADD COLUMN sku VARCHAR NOT NULL DEFAULT \'\'' )
                )

        if _postgres_table_exists(conn, "inbound_order") and _postgres_table_exists(
            conn, "medical_supply"
        ):
            conn.execute(
                text(
                    "UPDATE inbound_order AS o "
                    "SET product_name = s.name, sku = s.sku "
                    "FROM medical_supply AS s "
                    "WHERE o.product_id = s.id"
                )
            )
        if _postgres_table_exists(conn, "outbound_order") and _postgres_table_exists(
            conn, "medical_supply"
        ):
            conn.execute(
                text(
                    "UPDATE outbound_order AS o "
                    "SET product_name = s.name, sku = s.sku "
                    "FROM medical_supply AS s "
                    "WHERE o.product_id = s.id"
                )
            )

        if _postgres_table_exists(conn, "inbound_order") and _postgres_table_exists(
            conn, "outbound_order"
        ):
            conn.execute(
                text(
                    "CREATE OR REPLACE VIEW inventory_order AS "
                    "SELECT id, product_id, product_name, sku, quantity, notes, "
                    "created_at, user_uuid, 'inbound'::varchar AS type "
                    "FROM inbound_order "
                    "UNION ALL "
                    "SELECT id, product_id, product_name, sku, quantity, notes, "
                    "created_at, user_uuid, 'outbound'::varchar AS type "
                    "FROM outbound_order"
                )
            )


def init_inventory_schema() -> None:
    """Create inventory tables in Supabase / SQLModel metadata.create_all(engine)."""
    from app.inventory import models as _inventory_models  # noqa: F401

    engine = get_engine()
    try:
        if engine.dialect.name == "postgresql":
            migrate_postgres_inventory(engine)
        SQLModel.metadata.create_all(engine)
    except SQLAlchemyError as exc:
        raise StorageError("Unable to access inventory data store") from exc


def init_dual_stores() -> None:
    """Confirm TinyDB auth store and SQLModel inventory engine both initialize."""
    auth_store.get_user_by_id(0)
    init_inventory_schema()


def get_db() -> Generator[Session, None, None]:
    """Yield a SQLModel session per request. No global Session variable."""
    session = Session(get_engine())
    try:
        yield session
    except SQLAlchemyError as exc:
        session.rollback()
        raise StorageError("Unable to access inventory data store") from exc
    finally:
        session.close()
