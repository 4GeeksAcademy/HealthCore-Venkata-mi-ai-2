"""SQLite read/write store for approved desk memory and the decision audit.

The file is ``agent_memory.sqlite`` inside the agent state directory, separate
from the company knowledge collection and from the task broker. Rejected
proposals are audit rows only. Facts are inserted from ``commit_approved``.
"""

from __future__ import annotations

import re
import sqlite3
import threading
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from .phi import PhiScan, phi_scan, redact

TTL_DAYS = {
    "clinic_protocol": 90,
    "incident_pattern": 90,
    "staff_preference": 180,
    "admin_exception": 365,
}
PENDING_TTL = timedelta(hours=24)
MAX_ACTIVE = 40

_SCHEMA = """
CREATE TABLE IF NOT EXISTS memory_facts (
    id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    scope TEXT NOT NULL,
    text TEXT NOT NULL,
    text_norm TEXT NOT NULL,
    why TEXT NOT NULL,
    approved_by TEXT NOT NULL,
    approved_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    use_count INTEGER NOT NULL DEFAULT 0,
    active INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS memory_pending (
    conversation_id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    scope TEXT NOT NULL,
    text TEXT NOT NULL,
    why TEXT NOT NULL,
    proposed_by TEXT NOT NULL,
    proposed_at TEXT NOT NULL,
    originating_message TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS memory_audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    conversation_id TEXT NOT NULL,
    actor_id TEXT NOT NULL,
    event TEXT NOT NULL,
    proposal_text TEXT NOT NULL,
    outcome TEXT NOT NULL,
    originating_message TEXT NOT NULL,
    detail TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_memory_facts_active ON memory_facts(active, expires_at);
CREATE INDEX IF NOT EXISTS idx_memory_audit_conversation ON memory_audit(conversation_id, id);
"""

_STOP = frozenset(
    """
    about after again before being clinic could from have healthcore internal
    just last more only over should than that their there these those through
    under were what when where which with would your
    """.split()
)


class PendingExists(RuntimeError):
    """This conversation already has an unresolved proposal."""


def _iso(moment: datetime) -> str:
    if moment.tzinfo is None:
        raise ValueError("memory timestamps need a timezone")
    return moment.astimezone(UTC).isoformat(timespec="seconds")


def _norm(text: str) -> str:
    return " ".join(text.lower().split())


@dataclass(frozen=True)
class MemoryFact:
    id: str
    kind: str
    scope: str
    text: str
    why: str
    approved_by: str
    approved_at: str
    expires_at: str
    use_count: int
    active: bool


@dataclass(frozen=True)
class PendingProposal:
    conversation_id: str
    kind: str
    scope: str
    text: str
    why: str
    proposed_by: str
    proposed_at: str
    originating_message: str


@dataclass(frozen=True)
class AuditRow:
    id: int
    ts: str
    conversation_id: str
    actor_id: str
    event: str
    proposal_text: str
    outcome: str
    originating_message: str
    detail: str


@dataclass(frozen=True)
class ConsolidationReport:
    expired: int
    duplicates: int
    phi_removed: int
    capped: int


def _fact(row: sqlite3.Row) -> MemoryFact:
    return MemoryFact(
        id=row["id"],
        kind=row["kind"],
        scope=row["scope"],
        text=row["text"],
        why=row["why"],
        approved_by=row["approved_by"],
        approved_at=row["approved_at"],
        expires_at=row["expires_at"],
        use_count=row["use_count"],
        active=bool(row["active"]),
    )


def _pending(row: sqlite3.Row) -> PendingProposal:
    return PendingProposal(
        conversation_id=row["conversation_id"],
        kind=row["kind"],
        scope=row["scope"],
        text=row["text"],
        why=row["why"],
        proposed_by=row["proposed_by"],
        proposed_at=row["proposed_at"],
        originating_message=row["originating_message"],
    )


class MemoryStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        if str(self.path) != ":memory:":
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        with self._lock, self._conn:
            self._conn.executescript(_SCHEMA)

    def close(self) -> None:
        self._conn.close()

    def audit(
        self,
        *,
        conversation_id: str,
        actor_id: str,
        event: str,
        proposal_text: str,
        outcome: str,
        originating_message: str,
        detail: str,
        now: datetime,
    ) -> None:
        with self._lock, self._conn:
            self._audit_tx(
                self._conn,
                conversation_id=conversation_id,
                actor_id=actor_id,
                event=event,
                proposal_text=proposal_text,
                outcome=outcome,
                originating_message=originating_message,
                detail=detail,
                now=now,
            )

    def _audit_tx(self, conn: sqlite3.Connection, **kwargs: str | datetime) -> None:
        now = kwargs["now"]
        assert isinstance(now, datetime)
        conn.execute(
            "INSERT INTO memory_audit (ts, conversation_id, actor_id, event, proposal_text,"
            " outcome, originating_message, detail) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                _iso(now),
                kwargs["conversation_id"],
                kwargs["actor_id"],
                kwargs["event"],
                str(kwargs["proposal_text"])[:500],
                kwargs["outcome"],
                str(kwargs["originating_message"])[:1000],
                str(kwargs["detail"])[:300],
            ),
        )

    def get_pending(self, conversation_id: str) -> PendingProposal | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM memory_pending WHERE conversation_id=?", (conversation_id,)
            ).fetchone()
        return _pending(row) if row else None

    def put_pending(self, pending: PendingProposal) -> None:
        with self._lock, self._conn:
            try:
                self._conn.execute(
                    "INSERT INTO memory_pending (conversation_id, kind, scope, text, why,"
                    " proposed_by, proposed_at, originating_message) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        pending.conversation_id,
                        pending.kind,
                        pending.scope,
                        pending.text,
                        pending.why,
                        pending.proposed_by,
                        pending.proposed_at,
                        pending.originating_message[:1000],
                    ),
                )
            except sqlite3.IntegrityError as exc:
                raise PendingExists(pending.conversation_id) from exc

    def has_active_text(self, text: str, now: datetime) -> bool:
        with self._lock:
            row = self._conn.execute(
                "SELECT 1 FROM memory_facts WHERE active=1 AND text_norm=? AND expires_at>?",
                (_norm(text), _iso(now)),
            ).fetchone()
        return row is not None

    def list_facts(self, *, active_only: bool = True) -> list[MemoryFact]:
        sql = "SELECT * FROM memory_facts"
        if active_only:
            sql += " WHERE active=1"
        sql += " ORDER BY approved_at, id"
        with self._lock:
            return [_fact(row) for row in self._conn.execute(sql)]

    def list_audit(self, conversation_id: str | None = None) -> list[AuditRow]:
        sql = "SELECT * FROM memory_audit"
        params: tuple[str, ...] = ()
        if conversation_id is not None:
            sql += " WHERE conversation_id=?"
            params = (conversation_id,)
        sql += " ORDER BY id"
        with self._lock:
            rows = self._conn.execute(sql, params).fetchall()
        return [
            AuditRow(
                id=row["id"],
                ts=row["ts"],
                conversation_id=row["conversation_id"],
                actor_id=row["actor_id"],
                event=row["event"],
                proposal_text=row["proposal_text"],
                outcome=row["outcome"],
                originating_message=row["originating_message"],
                detail=row["detail"],
            )
            for row in rows
        ]

    def expire_pending(self, now: datetime) -> set[str]:
        cutoff = _iso(now - PENDING_TTL)
        with self._lock, self._conn:
            rows = self._conn.execute(
                "SELECT * FROM memory_pending WHERE proposed_at<=?", (cutoff,)
            ).fetchall()
            closed: set[str] = set()
            for row in rows:
                self._audit_tx(
                    self._conn,
                    conversation_id=row["conversation_id"],
                    actor_id=row["proposed_by"],
                    event="expired",
                    proposal_text=row["text"],
                    outcome="rejected",
                    originating_message="[no reply]",
                    detail="pending older than 24h",
                    now=now,
                )
                self._conn.execute(
                    "DELETE FROM memory_pending WHERE conversation_id=?", (row["conversation_id"],)
                )
                closed.add(row["conversation_id"])
        return closed

    def reject_pending(
        self,
        pending: PendingProposal,
        *,
        actor_id: str,
        event: str,
        outcome: str,
        originating_message: str,
        detail: str,
        now: datetime,
        proposal_text: str | None = None,
    ) -> None:
        with self._lock, self._conn:
            self._audit_tx(
                self._conn,
                conversation_id=pending.conversation_id,
                actor_id=actor_id,
                event=event,
                proposal_text=proposal_text if proposal_text is not None else pending.text,
                outcome=outcome,
                originating_message=originating_message,
                detail=detail,
                now=now,
            )
            self._conn.execute(
                "DELETE FROM memory_pending WHERE conversation_id=?", (pending.conversation_id,)
            )

    def commit_approved(
        self,
        pending: PendingProposal,
        *,
        actor_id: str,
        text: str,
        event: str,
        originating_message: str,
        detail: str,
        now: datetime,
    ) -> MemoryFact | None:
        """Write a fact only for an approve or edit that still passes the PHI gate.

        Returns None when the text is no longer safe to store. The pending row
        is cleared either way, and the audit row records the outcome.
        """
        scan = phi_scan(text)
        if scan.hit:
            self.reject_pending(
                pending,
                actor_id=actor_id,
                event="phi_blocked",
                outcome="rejected",
                originating_message=redact(originating_message, scan),
                detail="commit re-check " + ",".join(scan.rules),
                now=now,
                proposal_text="[redacted]",
            )
            return None
        if event not in {"approved", "edited"}:
            raise ValueError("commit_approved requires an approve or edit event")
        expires = _iso(now + timedelta(days=TTL_DAYS[pending.kind]))
        fact_id = uuid.uuid4().hex
        with self._lock, self._conn:
            self._conn.execute(
                "INSERT INTO memory_facts (id, kind, scope, text, text_norm, why, approved_by,"
                " approved_at, expires_at, use_count, active) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 1)",
                (
                    fact_id,
                    pending.kind,
                    pending.scope,
                    text[:500],
                    _norm(text),
                    pending.why,
                    actor_id,
                    _iso(now),
                    expires,
                ),
            )
            self._audit_tx(
                self._conn,
                conversation_id=pending.conversation_id,
                actor_id=actor_id,
                event=event,
                proposal_text=pending.text,
                outcome=text[:500],
                originating_message=originating_message[:1000],
                detail=detail,
                now=now,
            )
            self._conn.execute(
                "DELETE FROM memory_pending WHERE conversation_id=?", (pending.conversation_id,)
            )
        return MemoryFact(
            id=fact_id,
            kind=pending.kind,
            scope=pending.scope,
            text=text[:500],
            why=pending.why,
            approved_by=actor_id,
            approved_at=_iso(now),
            expires_at=expires,
            use_count=0,
            active=True,
        )

    def read_matching(self, question: str, now: datetime) -> list[MemoryFact]:
        chosen = [fact for fact in self._live(now) if _matches(fact, question)]
        if not chosen:
            return []
        with self._lock, self._conn:
            self._conn.executemany(
                "UPDATE memory_facts SET use_count=use_count+1 WHERE id=?",
                [(fact.id,) for fact in chosen],
            )
        return chosen

    def _live(self, now: datetime) -> list[MemoryFact]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM memory_facts WHERE active=1 AND expires_at>? ORDER BY approved_at, id",
                (_iso(now),),
            ).fetchall()
        return [_fact(row) for row in rows]

    def stage_legacy_fact(self, *, text: str, kind: str = "clinic_protocol", scope: str = "Austin") -> None:
        """Insert a row that skipped the proposal gate, so consolidation can re-check it.

        The agent turn never calls this. It exists so a tightened PHI rule still
        has something to remove.
        """
        now = datetime.now(UTC)
        with self._lock, self._conn:
            self._conn.execute(
                "INSERT INTO memory_facts (id, kind, scope, text, text_norm, why, approved_by,"
                " approved_at, expires_at, use_count, active) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 1)",
                (
                    uuid.uuid4().hex,
                    kind,
                    scope,
                    text,
                    _norm(text),
                    "legacy",
                    "staff:0",
                    _iso(now),
                    _iso(now + timedelta(days=30)),
                ),
            )

    def consolidate(self, now: datetime) -> ConsolidationReport:
        expired = duplicates = phi_removed = capped = 0
        with self._lock, self._conn:
            live = [
                _fact(row)
                for row in self._conn.execute("SELECT * FROM memory_facts WHERE active=1").fetchall()
            ]
            for fact in live:
                if fact.expires_at <= _iso(now):
                    self._deactivate(fact, now, reason="expired")
                    expired += 1
            remaining = [
                _fact(row)
                for row in self._conn.execute(
                    "SELECT * FROM memory_facts WHERE active=1 ORDER BY approved_at, id"
                ).fetchall()
            ]
            for fact in remaining:
                scan: PhiScan = phi_scan(fact.text)
                if scan.hit:
                    self._deactivate(fact, now, reason="phi", scan=scan)
                    phi_removed += 1
            remaining = [
                _fact(row)
                for row in self._conn.execute(
                    "SELECT * FROM memory_facts WHERE active=1 ORDER BY approved_at, id"
                ).fetchall()
            ]
            seen: dict[tuple[str, str, str], MemoryFact] = {}
            for fact in remaining:
                key = (fact.kind, fact.scope.lower(), _norm(fact.text))
                previous = seen.get(key)
                if previous is None or fact.approved_at >= previous.approved_at:
                    if previous is not None:
                        self._deactivate(previous, now, reason="duplicate")
                        duplicates += 1
                    seen[key] = fact
                else:
                    self._deactivate(fact, now, reason="duplicate")
                    duplicates += 1
            remaining = [
                _fact(row)
                for row in self._conn.execute(
                    "SELECT * FROM memory_facts WHERE active=1 ORDER BY use_count, approved_at, id"
                ).fetchall()
            ]
            overflow = remaining[:-MAX_ACTIVE] if len(remaining) > MAX_ACTIVE else []
            for fact in overflow:
                self._deactivate(fact, now, reason="cap")
                capped += 1
        return ConsolidationReport(
            expired=expired, duplicates=duplicates, phi_removed=phi_removed, capped=capped
        )

    def _deactivate(self, fact: MemoryFact, now: datetime, *, reason: str, scan: PhiScan | None = None) -> None:
        proposal = "[redacted]" if scan and scan.hit else fact.text
        origin = redact(fact.text, scan) if scan and scan.hit else "[consolidation]"
        self._audit_tx(
            self._conn,
            conversation_id="consolidation",
            actor_id="staff:system",
            event="consolidated_phi" if reason == "phi" else "consolidated_drop",
            proposal_text=proposal,
            outcome="rejected",
            originating_message=origin,
            detail=reason if scan is None else "phi re-check " + ",".join(scan.rules),
            now=now,
        )
        if scan is not None and scan.hit:
            self._conn.execute(
                "UPDATE memory_facts SET active=0, text='[redacted]', text_norm='[redacted]' WHERE id=?",
                (fact.id,),
            )
        else:
            self._conn.execute("UPDATE memory_facts SET active=0 WHERE id=?", (fact.id,))


def _matches(fact: MemoryFact, question: str) -> bool:
    if fact.scope.lower() != "network" and re.search(rf"\b{re.escape(fact.scope)}\b", question, re.IGNORECASE):
        return True
    question_lower = question.lower()
    overlap = 0
    for token in re.findall(r"[a-z]{5,}", fact.text.lower()):
        if token in _STOP:
            continue
        if re.search(rf"\b{re.escape(token)}\b", question_lower):
            overlap += 1
        if overlap >= 2:
            return True
    return False
