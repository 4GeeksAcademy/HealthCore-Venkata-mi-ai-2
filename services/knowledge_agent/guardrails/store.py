"""Append-only guardrail event log for harness observability."""

from __future__ import annotations

import sqlite3
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_SCHEMA = """
CREATE TABLE IF NOT EXISTS guardrail_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    run_id TEXT NOT NULL,
    layer TEXT NOT NULL,
    failure_type TEXT NOT NULL,
    action TEXT NOT NULL,
    rule_id TEXT NOT NULL,
    classification TEXT NOT NULL,
    detail TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_guardrail_events_type ON guardrail_events(failure_type, rule_id);
"""


class GuardrailStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        with self._lock:
            self._conn.executescript(_SCHEMA)
            self._conn.commit()

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def record(
        self,
        *,
        run_id: str,
        layer: str,
        failure_type: str,
        action: str,
        rule_id: str,
        classification: str = "",
        detail: str = "",
    ) -> None:
        """Log a block or redirect. ``detail`` must be redacted (rule ids / hashes only)."""
        ts = datetime.now(UTC).isoformat()
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO guardrail_events
                (ts, run_id, layer, failure_type, action, rule_id, classification, detail)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ts,
                    run_id,
                    layer,
                    failure_type,
                    action,
                    rule_id,
                    classification,
                    detail,
                ),
            )
            self._conn.commit()

    def summary(self) -> dict[str, Any]:
        """Counts by failure type, action, and rule for the current session DB."""
        with self._lock:
            by_type = {
                row["failure_type"]: row["n"]
                for row in self._conn.execute(
                    "SELECT failure_type, COUNT(*) AS n FROM guardrail_events GROUP BY failure_type"
                )
            }
            by_action = {
                row["action"]: row["n"]
                for row in self._conn.execute(
                    "SELECT action, COUNT(*) AS n FROM guardrail_events GROUP BY action"
                )
            }
            by_rule = {
                row["rule_id"]: row["n"]
                for row in self._conn.execute(
                    "SELECT rule_id, COUNT(*) AS n FROM guardrail_events GROUP BY rule_id"
                )
            }
            total = self._conn.execute("SELECT COUNT(*) AS n FROM guardrail_events").fetchone()["n"]
        return {
            "total": total,
            "by_failure_type": by_type,
            "by_action": by_action,
            "by_rule": by_rule,
        }
