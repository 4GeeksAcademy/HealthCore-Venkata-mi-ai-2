#!/usr/bin/env python3
"""HealthCore nightly telemetry export + pipeline trigger (Ticket #DEV-53).

Independent of the FastAPI process — do not import app.main or run this on the
API event loop. Status / lock live in `job_runs` via `services.job_runner`.

Target date:
  TARGET_DATE=YYYY-MM-DD   override (UTC calendar day)
  default                  yesterday in UTC

Pipeline subprocess (this monorepo; assignment reference module does not exist):
  python data/pipelines/pipeline.py --month-start YYYY-MM-01

Cron (OS crontab recommended — not FastAPI lifespan / APScheduler), example UTC:
  15 2 * * * cd /path/to/HealthCore && /usr/bin/env python scripts/nightly_export.py >> /var/log/healthcore-nightly.log 2>&1

Optional env:
  NIGHTLY_SKIP_PIPELINE=1   skip subprocess (tests / CSV-only dry run)
  JOB_RUNS_DATABASE_URL     override job_runs store
  TELEMETRY_DATABASE_URL    override telemetry_events read source

Usage:
  python scripts/nightly_export.py
  TARGET_DATE=2026-10-13 python scripts/nightly_export.py
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from services.job_runner import (  # noqa: E402
    JOB_NAME_NIGHTLY_EXPORT,
    create_pending,
    has_completed_for_date,
    has_processing_lock,
    init_job_runs_schema,
    mark_completed,
    mark_failed,
    mark_processing,
)
from services.job_runner.db import get_job_engine, repo_root  # noqa: E402
from services.job_runner.export import export_telemetry_csv  # noqa: E402

JOB_NAME = JOB_NAME_NIGHTLY_EXPORT
LOGGER_NAME = "healthcore.nightly_export"


class _JobLogAdapter(logging.LoggerAdapter):
    """Ensure every line carries job_name + status for observability."""

    def process(self, msg: str, kwargs: dict) -> tuple[str, dict]:
        extra = dict(kwargs.get("extra") or {})
        extra.setdefault("job_name", self.extra.get("job_name", JOB_NAME))
        extra.setdefault("status", self.extra.get("status", "pending"))
        kwargs["extra"] = extra
        return msg, kwargs


def _configure_logging() -> _JobLogAdapter:
    logging.Formatter.converter = time.gmtime
    root = logging.getLogger()
    if not root.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s [%(name)s] job=%(job_name)s status=%(status)s %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%SZ",
            )
        )
        root.addHandler(handler)
        root.setLevel(logging.INFO)
    base = logging.getLogger(LOGGER_NAME)
    return _JobLogAdapter(base, {"job_name": JOB_NAME, "status": "pending"})


def _log(
    logger: _JobLogAdapter,
    level: int,
    message: str,
    *,
    status: str,
    job_name: str = JOB_NAME,
) -> None:
    logger.extra["status"] = status
    logger.extra["job_name"] = job_name
    logger.log(level, message, extra={"job_name": job_name, "status": status})


def resolve_target_date(env: dict[str, str] | None = None) -> date:
    source = env if env is not None else os.environ
    raw = (source.get("TARGET_DATE") or "").strip()
    if raw:
        return date.fromisoformat(raw)
    return datetime.now(timezone.utc).date() - timedelta(days=1)


def _pipeline_command(target_date: date) -> list[str]:
    """Milestone 6 CLI — monthly clinic supply pipeline (not telemetry_kpi_daily)."""
    month_start = target_date.replace(day=1).isoformat()
    script = repo_root() / "data" / "pipelines" / "pipeline.py"
    return [sys.executable, str(script), "--month-start", month_start]


def trigger_pipeline(target_date: date, logger: logging.Logger) -> None:
    if (os.environ.get("NIGHTLY_SKIP_PIPELINE") or "").strip() in {"1", "true", "TRUE", "yes"}:
        _log(logger, logging.INFO, "pipeline subprocess skipped (NIGHTLY_SKIP_PIPELINE)", status="processing")
        return
    cmd = _pipeline_command(target_date)
    _log(
        logger,
        logging.INFO,
        f"triggering pipeline subprocess: {' '.join(cmd)}",
        status="processing",
    )
    result = subprocess.run(
        cmd,
        cwd=str(repo_root()),
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()[:2000]
        raise RuntimeError(f"pipeline_subprocess_failed exit={result.returncode} {detail}")


def run_nightly_export(*, env: dict[str, str] | None = None) -> int:
    """
    Execute one nightly cycle. Returns process exit code (0 = ok / skipped).
    """
    logger = _configure_logging()
    if env is not None:
        for key, value in env.items():
            os.environ[key] = value

    init_job_runs_schema(get_job_engine())
    target = resolve_target_date(env)
    _log(
        logger,
        logging.INFO,
        f"start nightly_export target_date={target.isoformat()}",
        status="pending",
    )

    if has_processing_lock(JOB_NAME):
        _log(
            logger,
            logging.INFO,
            "abort: processing lock held by another nightly_export instance",
            status="processing",
        )
        return 0

    if has_completed_for_date(JOB_NAME, target):
        _log(
            logger,
            logging.INFO,
            f"skipped as duplicate: completed job already exists for {target.isoformat()}",
            status="completed",
        )
        return 0

    run_id = create_pending(JOB_NAME, target)
    mark_processing(run_id)
    _log(logger, logging.INFO, f"acquired processing lock run_id={run_id}", status="processing")

    try:
        path, count, wrote = export_telemetry_csv(target)
        if wrote:
            _log(
                logger,
                logging.INFO,
                f"csv export wrote {count} rows to {path.name}",
                status="processing",
            )
        else:
            _log(
                logger,
                logging.INFO,
                f"csv already exists, skip write: {path.name}",
                status="processing",
            )

        trigger_pipeline(target, logger)
        mark_completed(run_id)
        _log(
            logger,
            logging.INFO,
            f"finish nightly_export run_id={run_id} target_date={target.isoformat()}",
            status="completed",
        )
        return 0
    except Exception as exc:
        mark_failed(run_id, str(exc))
        _log(
            logger,
            logging.ERROR,
            f"nightly_export failed run_id={run_id}: {exc}",
            status="failed",
        )
        return 1


def main() -> None:
    raise SystemExit(run_nightly_export())


if __name__ == "__main__":
    main()
