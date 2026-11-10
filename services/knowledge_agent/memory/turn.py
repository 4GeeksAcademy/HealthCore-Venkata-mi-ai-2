"""One turn of desk memory around the existing graph run.

This is the same coordinator agent. The graph still answers from the knowledge
base and the live tools. Memory adds one structured assessment and, when a
proposal is already waiting, one structured decision. There is no second agent.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

import sqlite3

from .assess import MemoryProposal, assess_message, clean_fact, is_remember_request, match_proposal, policy_conflict
from .classify import CONFIDENCE_THRESHOLD, classify_decision
from .phi import phi_scan, redact
from .store import MemoryStore, PendingProposal, _iso

logger = logging.getLogger(__name__)

PHI_REFUSAL = (
    "I can't remember that. It looks like patient information, which HealthCore does not "
    "store in agent memory under HIPAA or UK GDPR. I have not saved it."
)
POLICY_REFUSAL = (
    "I can't store that as desk memory. It conflicts with published HealthCore policy, "
    "and policy changes go through compliance review. I have not saved it."
)
APPROVE_LEAD = "Saved. I'll use that on a later question until it expires."
EDIT_LEAD = "Saved the edited wording. I'll use that until it expires."
REJECT_LEAD = "I won't remember that."
AMBIGUOUS_LEAD = "I didn't get a clear yes or no, so I discarded that memory proposal."
EXPIRED_LEAD = "The earlier memory proposal expired without a clear answer, so I discarded it."
UNAVAILABLE = "I couldn't use desk memory just now. Please try again in a moment."
PROPOSAL_PREFIX = "Want me to remember this for next time?"
MEMORY_HEADER = "Approved desk memory (not a substitute for published policy):"

_CONVERSATION = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_ACTOR = re.compile(r"^staff:\d+$")


class MemoryUnavailable(RuntimeError):
    """The memory file could not be read or written. The desk answer can still proceed."""


def normalize_conversation_id(value: str | None) -> str:
    if value and _CONVERSATION.fullmatch(value):
        return value
    return uuid4().hex


def normalize_actor(value: str | None) -> str:
    if value and _ACTOR.fullmatch(value):
        return value
    return "staff:unknown"


def join_parts(*parts: str) -> str:
    return "\n\n".join(part.strip() for part in parts if part and part.strip())


def render_memory(facts: list) -> str:
    if not facts:
        return ""
    lines = [MEMORY_HEADER]
    lines.extend(f"- {fact.scope}: {fact.text}" for fact in facts)
    return "\n".join(lines)


@dataclass(frozen=True)
class TurnPrelude:
    conversation_id: str
    memory_event: str
    lead: str = ""
    locked_suffix: str = ""
    graph_question: str | None = None
    final_answer: str | None = None
    block_proposal: bool = False
    trace_question: str = ""


@dataclass(frozen=True)
class TurnEnding:
    suffix: str
    memory_event: str


class MemoryCoordinator:
    def __init__(self, store: MemoryStore, clock: Callable[[], datetime] | None = None) -> None:
        self.store = store
        self._clock = clock or (lambda: datetime.now(UTC))

    def close(self) -> None:
        self.store.close()

    def _now(self) -> datetime:
        moment = self._clock()
        if moment.tzinfo is None:
            moment = moment.replace(tzinfo=UTC)
        return moment

    def prepare(self, conversation_id: str, message: str, actor_id: str) -> TurnPrelude:
        now = self._now()
        scan = phi_scan(message)
        if scan.hit:
            try:
                self.store.audit(
                    conversation_id=conversation_id,
                    actor_id=actor_id,
                    event="phi_blocked",
                    proposal_text="[redacted]",
                    outcome="rejected",
                    originating_message=redact(message, scan),
                    detail="HIPAA and UK GDPR " + ",".join(scan.rules),
                    now=now,
                )
            except sqlite3.Error:
                logger.error("agent memory audit failed (%s)", "sqlite3.Error")
            return TurnPrelude(
                conversation_id=conversation_id,
                memory_event="phi_blocked",
                final_answer=PHI_REFUSAL,
                trace_question="[redacted]",
            )

        try:
            return self._prepare_clean(conversation_id, message, actor_id, now)
        except sqlite3.Error as exc:
            raise MemoryUnavailable from exc

    def _prepare_clean(
        self, conversation_id: str, message: str, actor_id: str, now: datetime
    ) -> TurnPrelude:
        expired = self.store.expire_pending(now)
        lead = EXPIRED_LEAD if conversation_id in expired else ""
        event = "expired" if conversation_id in expired else "none"
        pending = self.store.get_pending(conversation_id)
        graph_question: str | None = message
        final_answer: str | None = None
        block = False
        locked = ""

        if pending is not None:
            decision = classify_decision(pending.text, message)
            if decision.confidence < CONFIDENCE_THRESHOLD or decision.label == "ambiguous":
                self._reject(pending, actor_id, message, now, "ambiguous_rejected", "ambiguous")
                lead = join_parts(lead, AMBIGUOUS_LEAD)
                event = "ambiguous_rejected"
            elif decision.label == "reject":
                self._reject(pending, actor_id, message, now, "rejected", "rejected")
                lead = join_parts(lead, REJECT_LEAD)
                event = "rejected"
                graph_question = decision.follow_up
                final_answer = lead if decision.follow_up is None else None
            elif decision.label == "edit":
                return self._apply_edit(pending, decision.edited_fact or "", message, actor_id, now, lead)
            else:
                fact = self.store.commit_approved(
                    pending,
                    actor_id=actor_id,
                    text=pending.text,
                    event="approved",
                    originating_message=message,
                    detail=f"label=approve confidence={decision.confidence:.2f}",
                    now=now,
                )
                lead = join_parts(lead, APPROVE_LEAD if fact else PHI_REFUSAL)
                event = "approved" if fact else "phi_blocked"
                graph_question = decision.follow_up
                final_answer = None if decision.follow_up else lead

        if (
            final_answer is None
            and graph_question
            and _store_attempt_conflicts(graph_question)
        ):
            self.store.audit(
                conversation_id=conversation_id,
                actor_id=actor_id,
                event="policy_blocked",
                proposal_text=clean_fact(graph_question)[:500],
                outcome="rejected",
                originating_message=message[:1000],
                detail="published policy conflict",
                now=now,
            )
            block = True
            locked = POLICY_REFUSAL
            if event == "none":
                event = "policy_blocked"

        return TurnPrelude(
            conversation_id=conversation_id,
            memory_event=event,
            lead="" if final_answer else lead,
            locked_suffix=locked,
            graph_question=graph_question,
            final_answer=final_answer,
            block_proposal=block,
            trace_question=graph_question or "[decision]",
        )

    def _apply_edit(
        self,
        pending: PendingProposal,
        edited: str,
        message: str,
        actor_id: str,
        now: datetime,
        lead: str,
    ) -> TurnPrelude:
        edit_scan = phi_scan(edited)
        if edit_scan.hit or policy_conflict(edited):
            blocked = "phi_blocked" if edit_scan.hit else "policy_blocked"
            self.store.reject_pending(
                pending,
                actor_id=actor_id,
                event=blocked,
                outcome="rejected",
                originating_message=redact(message, edit_scan) if edit_scan.hit else message[:1000],
                detail=blocked,
                now=now,
                proposal_text="[redacted]" if edit_scan.hit else pending.text,
            )
            return TurnPrelude(
                conversation_id=pending.conversation_id,
                memory_event=blocked,
                final_answer=PHI_REFUSAL if edit_scan.hit else POLICY_REFUSAL,
                trace_question="[redacted]" if edit_scan.hit else "[decision]",
            )
        fact = self.store.commit_approved(
            pending,
            actor_id=actor_id,
            text=edited,
            event="edited",
            originating_message=message,
            detail="label=edit confidence=0.92",
            now=now,
        )
        saved = EDIT_LEAD if fact else PHI_REFUSAL
        return TurnPrelude(
            conversation_id=pending.conversation_id,
            memory_event="edited" if fact else "phi_blocked",
            final_answer=join_parts(lead, saved),
            trace_question="[decision]",
        )

    def _reject(
        self,
        pending: PendingProposal,
        actor_id: str,
        message: str,
        now: datetime,
        event: str,
        detail: str,
    ) -> None:
        self.store.reject_pending(
            pending,
            actor_id=actor_id,
            event=event,
            outcome="rejected",
            originating_message=message[:1000],
            detail=detail,
            now=now,
        )

    def finish(
        self,
        conversation_id: str,
        graph_question: str,
        actor_id: str,
        *,
        block_proposal: bool,
        locked_suffix: str,
    ) -> TurnEnding:
        try:
            return self._finish(
                conversation_id,
                graph_question,
                actor_id,
                block_proposal,
                locked_suffix,
                self._now(),
            )
        except sqlite3.Error as exc:
            raise MemoryUnavailable from exc

    def _finish(
        self,
        conversation_id: str,
        graph_question: str,
        actor_id: str,
        block_proposal: bool,
        locked_suffix: str,
        now: datetime,
    ) -> TurnEnding:
        proposal_line = ""
        event = "none"
        if not block_proposal and self.store.get_pending(conversation_id) is None:
            assessment = assess_message(
                graph_question,
                already_stored=self.store.has_active_text(clean_fact(graph_question), now),
            )
            if assessment.blocked == "phi":
                self.store.audit(
                    conversation_id=conversation_id,
                    actor_id=actor_id,
                    event="phi_blocked",
                    proposal_text="[redacted]",
                    outcome="rejected",
                    originating_message=redact(graph_question, phi_scan(graph_question)),
                    detail="HIPAA and UK GDPR",
                    now=now,
                )
                return TurnEnding(suffix=PHI_REFUSAL, memory_event="phi_blocked")
            if assessment.blocked == "policy":
                self.store.audit(
                    conversation_id=conversation_id,
                    actor_id=actor_id,
                    event="policy_blocked",
                    proposal_text=clean_fact(graph_question)[:500],
                    outcome="rejected",
                    originating_message=graph_question[:1000],
                    detail="published policy conflict",
                    now=now,
                )
                locked_suffix = join_parts(locked_suffix, POLICY_REFUSAL)
                event = "policy_blocked"
            elif assessment.memory_proposal is not None:
                self._propose(conversation_id, assessment.memory_proposal, actor_id, graph_question, now)
                proposal_line = f"{PROPOSAL_PREFIX}\n{assessment.memory_proposal.fact}"
                event = "proposed"
        remembered = render_memory(self.store.read_matching(graph_question, now))
        return TurnEnding(suffix=join_parts(remembered, locked_suffix, proposal_line), memory_event=event)

    def _propose(
        self,
        conversation_id: str,
        proposal: MemoryProposal,
        actor_id: str,
        message: str,
        now: datetime,
    ) -> None:
        self.store.put_pending(
            PendingProposal(
                conversation_id=conversation_id,
                kind=proposal.kind,
                scope=proposal.scope,
                text=proposal.fact,
                why=proposal.why,
                proposed_by=actor_id,
                proposed_at=_iso(now),
                originating_message=message[:1000],
            )
        )
        self.store.audit(
            conversation_id=conversation_id,
            actor_id=actor_id,
            event="proposed",
            proposal_text=proposal.fact,
            outcome="pending",
            originating_message=message[:1000],
            detail=f"kind={proposal.kind} scope={proposal.scope}",
            now=now,
        )


def _store_attempt_conflicts(text: str) -> bool:
    if policy_conflict(text) and (is_remember_request(text) or match_proposal(text) is not None):
        return True
    return False
