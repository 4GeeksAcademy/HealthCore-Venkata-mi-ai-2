"""SQL engine and `job_runs` schema for nightly orchestration."""

from __future__ import annotations

import base64
import hashlib
import os
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.pool import NullPool, StaticPool

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_SQLITE = _REPO_ROOT / "data" / "process" / "job_runs.db"
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
                return decoded
            return decoded
    return None


def job_database_url() -> str:
    """Prefer JOB_RUNS_DATABASE_URL; else same store as telemetry_events."""
    return (
        _resolve_url(
            "JOB_RUNS_DATABASE_URL",
            "TELEMETRY_DATABASE_URL",
            "SUPABASE_DATABASE_URL",
            "DATABASE_URL",
        )
        or _sqlite_url()
    )


def telemetry_database_url() -> str:
    return (
        _resolve_url("TELEMETRY_DATABASE_URL", "SUPABASE_DATABASE_URL", "DATABASE_URL")
        or job_database_url()
    )


def _make_engine(url: str) -> Engine:
    kwargs: dict[str, Any] = {}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
        if ":memory:" in url or url in {"sqlite://", "sqlite:///:memory:"}:
            kwargs["poolclass"] = StaticPool
    elif "pooler.supabase.com" in url:
        kwargs["poolclass"] = NullPool
    return create_engine(url, **kwargs)


def get_job_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = _make_engine(job_database_url())
    return _engine


_telemetry_engine: Engine | None = None


def get_telemetry_engine() -> Engine:
    global _telemetry_engine
    if _telemetry_engine is None:
        _telemetry_engine = _make_engine(telemetry_database_url())
    return _telemetry_engine


def reset_job_engine() -> None:
    global _engine, _telemetry_engine
    if _engine is not None:
        _engine.dispose()
        _engine = None
    if _telemetry_engine is not None:
        _telemetry_engine.dispose()
        _telemetry_engine = None


def is_sqlite(engine: Engine | None = None) -> bool:
    eng = engine or get_job_engine()
    return eng.dialect.name == "sqlite"


def init_job_runs_schema(engine: Engine | None = None) -> None:
    """Create `job_runs` + index on (job_name, target_date). Not merged with pipeline_runs."""
    eng = engine or get_job_engine()
    with eng.begin() as conn:
        if is_sqlite(eng):
            conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS job_runs (
                      id TEXT PRIMARY KEY,
                      job_name TEXT NOT NULL,
                      target_date TEXT NOT NULL,
                      status TEXT NOT NULL,
                      started_at TEXT,
                      finished_at TEXT,
                      error_message TEXT,
                      created_at TEXT NOT NULL
                    )
                    """
                )
            )
            conn.execute(
                text(
                    """
                    CREATE INDEX IF NOT EXISTS ix_job_runs_job_name_target_date
                    ON job_runs (job_name, target_date)
                    """
                )
            )
            return

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS job_runs (
                  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
                  job_name text NOT NULL,
                  target_date date NOT NULL,
                  status text NOT NULL,
                  started_at timestamptz,
                  finished_at timestamptz,
                  error_message text,
                  created_at timestamptz NOT NULL DEFAULT now()
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS ix_job_runs_job_name_target_date
                ON job_runs (job_name, target_date)
                """
            )
        )
