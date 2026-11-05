"""Queryable run/step trace for the knowledge agent (SQLite).

One ``agent_runs`` row per run and one ``agent_steps`` row per node update, in
execution order. Question and answer text are stored only when the runner is
created with ``store_text=True`` (eval recordings of synthetic questions).
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
from datetime import UTC, datetime, timezone
from pathlib import Path
from typing import Any

_SCHEMA = """
CREATE TABLE IF NOT EXISTS agent_runs (
    run_id TEXT PRIMARY KEY,
    graph_version TEXT NOT NULL,
    mode TEXT NOT NULL,
    labels TEXT NOT NULL,
    status TEXT NOT NULL,
    outcome TEXT,
    failed_node TEXT,
    error_type TEXT,
    question_sha256 TEXT NOT NULL,
    question_chars INTEGER NOT NULL,
    question_text TEXT,
    answer_text TEXT,
    started_at TEXT NOT NULL,
    finished_at TEXT
);
CREATE TABLE IF NOT EXISTS agent_steps (
    run_id TEXT NOT NULL REFERENCES agent_runs(run_id),
    seq INTEGER NOT NULL,
    node TEXT NOT NULL,
    status TEXT NOT NULL,
    duration_ms REAL NOT NULL,
    output TEXT NOT NULL,
    recorded_at TEXT NOT NULL,
    PRIMARY KEY (run_id, seq)
);
CREATE INDEX IF NOT EXISTS idx_agent_runs_started ON agent_runs(started_at);
CREATE INDEX IF NOT EXISTS idx_agent_steps_node ON agent_steps(node);
"""


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds")


class TraceStore:
    def __init__(self, path: str | Path = ":memory:") -> None:
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        with self._lock, self._conn:
            self._conn.executescript(_SCHEMA)

    def close(self) -> None:
        self._conn.close()

    # -- writes -------------------------------------------------------------

    def start_run(
        self,
        run_id: str,
        *,
        question: str,
        graph_version: str,
        mode: str,
        labels: dict[str, Any] | None,
        store_text: bool,
    ) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                "INSERT INTO agent_runs (run_id, graph_version, mode, labels, status,"
                " question_sha256, question_chars, question_text, started_at)"
                " VALUES (?, ?, ?, ?, 'running', ?, ?, ?, ?)",
                (
                    run_id,
                    graph_version,
                    mode,
                    json.dumps(labels or {}, sort_keys=True),
                    hashlib.sha256(question.encode("utf-8")).hexdigest(),
                    len(question),
                    question if store_text else None,
                    _now(),
                ),
            )

    def mark_resumed(self, run_id: str) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                "UPDATE agent_runs SET status='running', failed_node=NULL, error_type=NULL,"
                " finished_at=NULL WHERE run_id=?",
                (run_id,),
            )

    def record_step(
        self, run_id: str, node: str, *, status: str, duration_ms: float, output: dict[str, Any]
    ) -> None:
        with self._lock, self._conn:
            (seq,) = self._conn.execute(
                "SELECT COALESCE(MAX(seq), 0) + 1 FROM agent_steps WHERE run_id=?", (run_id,)
            ).fetchone()
            self._conn.execute(
                "INSERT INTO agent_steps (run_id, seq, node, status, duration_ms, output, recorded_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (run_id, seq, node, status, round(duration_ms, 3), json.dumps(output, sort_keys=True), _now()),
            )

    def finish_run(
        self,
        run_id: str,
        *,
        status: str,
        outcome: str | None = None,
        answer: str | None = None,
        failed_node: str | None = None,
        error_type: str | None = None,
    ) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                "UPDATE agent_runs SET status=?, outcome=?, answer_text=?, failed_node=?,"
                " error_type=?, finished_at=? WHERE run_id=?",
                (status, outcome, answer, failed_node, error_type, _now(), run_id),
            )

    # -- queries ------------------------------------------------------------

    def _run_dict(self, row: sqlite3.Row) -> dict[str, Any]:
        run = dict(row)
        run["labels"] = json.loads(run["labels"])
        steps = self._conn.execute(
            "SELECT seq, node, status, duration_ms, output FROM agent_steps WHERE run_id=? ORDER BY seq",
            (run["run_id"],),
        ).fetchall()
        run["steps"] = [{**dict(step), "output": json.loads(step["output"])} for step in steps]
        return run

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        with self._lock:
            row = self._conn.execute("SELECT * FROM agent_runs WHERE run_id=?", (run_id,)).fetchone()
            return self._run_dict(row) if row else None

    def list_runs(
        self, *, status: str | None = None, outcome: str | None = None, limit: int = 100
    ) -> list[dict[str, Any]]:
        sql = "SELECT * FROM agent_runs WHERE 1=1"
        params: list[Any] = []
        if status:
            sql += " AND status=?"
            params.append(status)
        if outcome:
            sql += " AND outcome=?"
            params.append(outcome)
        sql += " ORDER BY started_at, rowid LIMIT ?"
        params.append(limit)
        with self._lock:
            return [self._run_dict(row) for row in self._conn.execute(sql, params).fetchall()]

    def node_sequence(self, run_id: str) -> list[str]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT node FROM agent_steps WHERE run_id=? ORDER BY seq", (run_id,)
            ).fetchall()
        return [row["node"] for row in rows]

    def export(self, run_ids: list[str] | None = None) -> list[dict[str, Any]]:
        runs = self.list_runs(limit=10_000)
        if run_ids is not None:
            wanted = set(run_ids)
            runs = [run for run in runs if run["run_id"] in wanted]
        return runs
