"""Reporting / telemetry SQL engine helpers for the clinic supply pipeline."""

from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.pool import NullPool, StaticPool

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_SQLITE = _REPO_ROOT / "data" / "process" / "reporting.db"
_engine: Engine | None = None


def repo_root() -> Path:
    return _REPO_ROOT


def _load_dotenv() -> None:
    env_path = _REPO_ROOT / ".env"
    if not env_path.is_file():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def _decode_url(value: str, jwt_secret: str | None) -> str:
    if value.startswith("enc:v1:") and jwt_secret:
        try:
            from cryptography.fernet import Fernet

            digest = hashlib.sha256(jwt_secret.encode("utf-8")).digest()
            fernet = Fernet(base64.urlsafe_b64encode(digest))
            return fernet.decrypt(value[7:].encode("ascii")).decode("utf-8")
        except Exception:
            return value
    if value.startswith("b64:"):
        try:
            return base64.urlsafe_b64decode(value[4:].encode("ascii")).decode("utf-8")
        except Exception:
            return value
    return value


def _sqlite_url() -> str:
    _DEFAULT_SQLITE.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{_DEFAULT_SQLITE.as_posix()}"


def _resolve_url(*keys: str) -> str | None:
    _load_dotenv()
    jwt = os.environ.get("JWT_SECRET_KEY")
    for key in keys:
        raw = (os.environ.get(key) or "").strip()
        if not raw:
            continue
        decoded = _decode_url(raw, jwt)
        if decoded.startswith(("postgresql", "postgres", "sqlite")):
            if decoded in {"sqlite://", "sqlite:///:memory:"}:
                return _sqlite_url()
            return decoded
    return None


def database_url() -> str:
    """Reporting destination. Prefer REPORTING_DATABASE_URL; else local SQLite."""
    return _resolve_url("REPORTING_DATABASE_URL") or _sqlite_url()


def telemetry_database_url() -> str:
    """Read-only source for telemetry_events (Option A). Falls back to reporting URL."""
    return (
        _resolve_url("TELEMETRY_DATABASE_URL", "SUPABASE_DATABASE_URL", "DATABASE_URL")
        or database_url()
    )


def _make_engine(url: str) -> Engine:
    kwargs: dict[str, Any] = {}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
        if ":memory:" in url:
            kwargs["poolclass"] = StaticPool
    elif "pooler.supabase.com" in url:
        kwargs["poolclass"] = NullPool
    return create_engine(url, **kwargs)


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = _make_engine(database_url())
    return _engine


_telemetry_engine: Engine | None = None


def get_telemetry_engine() -> Engine:
    global _telemetry_engine
    if _telemetry_engine is None:
        _telemetry_engine = _make_engine(telemetry_database_url())
    return _telemetry_engine


def reset_engine() -> None:
    global _engine, _telemetry_engine
    if _engine is not None:
        _engine.dispose()
        _engine = None
    if _telemetry_engine is not None:
        _telemetry_engine.dispose()
        _telemetry_engine = None


def is_sqlite(engine: Engine | None = None) -> bool:
    eng = engine or get_engine()
    return eng.dialect.name == "sqlite"


def kpi_table(engine: Engine | None = None) -> str:
    return "monthly_clinic_supply_performance" if is_sqlite(engine) else "reporting.monthly_clinic_supply_performance"


def runs_table(engine: Engine | None = None) -> str:
    return "pipeline_runs" if is_sqlite(engine) else "reporting.pipeline_runs"


def init_reporting_schema(engine: Engine | None = None) -> None:
    eng = engine or get_engine()
    with eng.begin() as conn:
        if not is_sqlite(eng):
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS reporting"))
            conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS reporting.monthly_clinic_supply_performance (
                      id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
                      clinic_id text NOT NULL,
                      country text NOT NULL,
                      month_start date NOT NULL,
                      total_supply_cost numeric NOT NULL DEFAULT 0,
                      supply_consumption_count integer NOT NULL DEFAULT 0,
                      critical_stockout_count integer NOT NULL DEFAULT 0,
                      expiry_risk_count integer NOT NULL DEFAULT 0,
                      currency text NOT NULL,
                      computed_at timestamptz NOT NULL DEFAULT now(),
                      UNIQUE (clinic_id, month_start)
                    )
                    """
                )
            )
            conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS reporting.pipeline_runs (
                      run_id uuid PRIMARY KEY,
                      flow_name text NOT NULL,
                      month_start date NOT NULL,
                      trigger text NOT NULL,
                      started_at timestamptz NOT NULL,
                      ended_at timestamptz,
                      status text NOT NULL,
                      phase text,
                      records_extracted integer NOT NULL DEFAULT 0,
                      records_deduped integer NOT NULL DEFAULT 0,
                      duplicate_event_id_count integer NOT NULL DEFAULT 0,
                      records_rejected integer NOT NULL DEFAULT 0,
                      records_loaded integer NOT NULL DEFAULT 0,
                      distinct_clinic_count integer NOT NULL DEFAULT 0,
                      distinct_session_count integer NOT NULL DEFAULT 0,
                      distinct_request_id_count integer NOT NULL DEFAULT 0,
                      error_message text,
                      source text NOT NULL DEFAULT 'telemetry_events'
                    )
                    """
                )
            )
            return

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS monthly_clinic_supply_performance (
                  id TEXT PRIMARY KEY,
                  clinic_id TEXT NOT NULL,
                  country TEXT NOT NULL,
                  month_start TEXT NOT NULL,
                  total_supply_cost REAL NOT NULL DEFAULT 0,
                  supply_consumption_count INTEGER NOT NULL DEFAULT 0,
                  critical_stockout_count INTEGER NOT NULL DEFAULT 0,
                  expiry_risk_count INTEGER NOT NULL DEFAULT 0,
                  currency TEXT NOT NULL,
                  computed_at TEXT NOT NULL,
                  UNIQUE (clinic_id, month_start)
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS pipeline_runs (
                  run_id TEXT PRIMARY KEY,
                  flow_name TEXT NOT NULL,
                  month_start TEXT NOT NULL,
                  trigger TEXT NOT NULL,
                  started_at TEXT NOT NULL,
                  ended_at TEXT,
                  status TEXT NOT NULL,
                  phase TEXT,
                  records_extracted INTEGER NOT NULL DEFAULT 0,
                  records_deduped INTEGER NOT NULL DEFAULT 0,
                  duplicate_event_id_count INTEGER NOT NULL DEFAULT 0,
                  records_rejected INTEGER NOT NULL DEFAULT 0,
                  records_loaded INTEGER NOT NULL DEFAULT 0,
                  distinct_clinic_count INTEGER NOT NULL DEFAULT 0,
                  distinct_session_count INTEGER NOT NULL DEFAULT 0,
                  distinct_request_id_count INTEGER NOT NULL DEFAULT 0,
                  error_message TEXT,
                  source TEXT NOT NULL DEFAULT 'telemetry_events'
                )
                """
            )
        )


def tags_as_dict(raw: Any) -> dict[str, Any]:
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}
