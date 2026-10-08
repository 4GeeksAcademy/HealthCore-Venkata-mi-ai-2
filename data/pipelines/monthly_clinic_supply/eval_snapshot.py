"""Optional non-critical eval snapshot writer for data/eval/."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from .db import repo_root


def write_eval_snapshot(rows: list[dict[str, Any]], month_start: date) -> str:
    """Write KPI snapshot for validation. Failures must not stop the main ETL."""
    out_dir = repo_root() / "data" / "eval"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"monthly_clinic_supply_{month_start.isoformat()}.json"
    # Force a controlled failure path when env asks for it (tests / demos).
    if Path(str(path) + ".force_fail").exists():
        raise RuntimeError("eval_snapshot_forced_failure")
    payload = {
        "month_start": month_start.isoformat(),
        "clinic_count": len(rows),
        "clinics": rows,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return str(path)
