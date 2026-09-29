"""Telemetry persistence: schema init + single bulk insert per batch."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import NullPool, StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.core.config import get_settings
from app.core.errors import StorageError
from app.models.telemetry import TelemetryEvent
from app.telemetry.models import TelemetryEventRow

_engine: Engine | None = None

_ERROR_TYPES = frozenset({"api_request_failed", "frontend_error_captured"})
_WARN_TYPES = frozenset(
    {
        "login_failed",
        "password_reset_failed",
        "password_change_failed",
        "order_validation_failed",
        "direct_stock_edit_rejected",
        "session_expired",
    }
)


def telemetry_sql_url() -> str:
    settings = get_settings()
    if settings.supabase_database_url:
        return settings.supabase_database_url
    return settings.database_url


def get_telemetry_engine() -> Engine:
    global _engine
    if _engine is None:
        url = telemetry_sql_url()
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
            raise StorageError("Unable to access telemetry data store") from exc
    return _engine


def reset_telemetry_engine() -> None:
    global _engine
    if _engine is not None:
        _engine.dispose()
        _engine = None


def _ensure_postgres_indexes(engine: Engine) -> None:
    with engine.begin() as conn:
        # SQLModel/create_all may emit JSON; GIN requires JSONB.
        conn.execute(
            text(
                "ALTER TABLE telemetry_events "
                "ALTER COLUMN tags TYPE jsonb USING COALESCE(tags::jsonb, '{}'::jsonb)"
            )
        )
        conn.execute(
            text(
                "ALTER TABLE telemetry_events "
                "ALTER COLUMN tags SET DEFAULT '{}'::jsonb"
            )
        )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_telemetry_events_timestamp "
                "ON telemetry_events (timestamp)"
            )
        )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_telemetry_events_event_type "
                "ON telemetry_events (event_type)"
            )
        )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_telemetry_events_tags_gin "
                "ON telemetry_events USING GIN (tags)"
            )
        )


def init_telemetry_schema() -> None:
    """Create telemetry_events + indexes. No UPDATE/DELETE helpers exist for this table."""
    from app.telemetry import models as _telemetry_models  # noqa: F401

    engine = get_telemetry_engine()
    try:
        SQLModel.metadata.create_all(engine, tables=[TelemetryEventRow.__table__])
        if engine.dialect.name == "postgresql":
            _ensure_postgres_indexes(engine)
    except SQLAlchemyError as exc:
        raise StorageError("Unable to access telemetry data store") from exc


def derive_level(event_type: str) -> str:
    if event_type in _ERROR_TYPES:
        return "error"
    if event_type in _WARN_TYPES:
        return "warn"
    return "info"


def _optional_numeric(properties: dict[str, Any]) -> Decimal | None:
    for key in ("value", "duration_ms", "latency_ms"):
        raw = properties.get(key)
        if raw is None:
            continue
        try:
            return Decimal(str(raw))
        except (InvalidOperation, ValueError):
            continue
    return None


def _parse_timestamp(raw: str) -> datetime:
    normalized = raw.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def event_to_row(event: TelemetryEvent) -> TelemetryEventRow:
    properties = dict(event.properties or {})
    tags: dict[str, Any] = {
        **properties,
        "eventId": event.eventId,
        "sessionId": event.sessionId,
        "userId": event.userId,
        "schemaVersion": event.schemaVersion,
        "requestId": event.requestId,
    }
    return TelemetryEventRow(
        timestamp=_parse_timestamp(event.timestamp),
        service="backoffice",
        event_type=event.event_type,
        level=derive_level(event.event_type),
        value=_optional_numeric(properties),
        message=None,
        tags=tags,
    )


def validate_and_partition(
    raw_events: list[Any],
) -> tuple[list[TelemetryEventRow], int]:
    """Return (valid rows, rejected_count)."""
    rows: list[TelemetryEventRow] = []
    rejected = 0
    for raw in raw_events:
        if not isinstance(raw, dict):
            rejected += 1
            continue
        try:
            event = TelemetryEvent.model_validate(raw)
            rows.append(event_to_row(event))
        except (ValidationError, ValueError, TypeError):
            rejected += 1
    return rows, rejected


def bulk_insert_events(rows: list[TelemetryEventRow]) -> int:
    """Insert all rows in one transaction. Returns number stored."""
    if not rows:
        return 0
    engine = get_telemetry_engine()
    try:
        with Session(engine) as session:
            session.add_all(rows)
            session.commit()
            return len(rows)
    except SQLAlchemyError as exc:
        raise StorageError("Unable to access telemetry data store") from exc
