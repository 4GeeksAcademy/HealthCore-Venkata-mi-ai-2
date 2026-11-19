"""Ticket, metadata, and department-section persistence."""

from __future__ import annotations

import threading
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, col, select

from .db import get_engine
from .errors import RfpStorageError
from .models import RfpDepartmentSection, RfpMetadata, RfpTicket
from .paths import relative_pdf_path, sanitize_filename
from .phi import contains_phi

_locks: dict[str, threading.Lock] = {}
_locks_guard = threading.Lock()

PIPELINE_MESSAGES = {
    "conversion_failed": "This PDF could not be converted for review. Try another file.",
    "classifier_unavailable": "The classifier is temporarily unavailable. Retry this ticket.",
    "worker_unavailable": "A department review did not finish. Retry this ticket.",
    "pipeline_crashed": "Analysis stopped before it finished. Retry this ticket.",
    "pipeline_interrupted": "Analysis was interrupted before it finished. Retry this ticket.",
    "storage_failed": "The ticket could not be saved. Try again.",
    "response_interrupted": "Proposal drafting stopped before it finished. The last saved section is kept for review.",
}

DISCARD_MESSAGES = {
    "vendor_pitch": "This document is a vendor pitch to HealthCore, so it is not a client RFP.",
    "patient_record": "This document looks like a patient record. It was discarded and the text was not stored.",
    "not_a_request": "This document does not ask HealthCore for a proposal.",
    "uncertain": "The classifier could not confirm this is a client RFP, so it was discarded. Retry if Sales confirms the request.",
}


def ticket_lock(ticket_id: str) -> threading.Lock:
    with _locks_guard:
        lock = _locks.get(ticket_id)
        if lock is None:
            lock = threading.Lock()
            _locks[ticket_id] = lock
        return lock


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def new_ticket_id() -> str:
    return str(uuid.uuid4())


def _session() -> Session:
    try:
        return Session(get_engine())
    except SQLAlchemyError as exc:
        raise RfpStorageError("rfp_session") from exc


def insert_analyzing(*, ticket_id: str, original_filename: str) -> None:
    now = utcnow()
    row = RfpTicket(
        ticket_id=ticket_id,
        status="analyzing",
        original_filename=sanitize_filename(original_filename),
        raw_pdf_path=relative_pdf_path(ticket_id),
        phi_detected=False,
        handoff_ready=False,
        created_at=now,
        updated_at=now,
    )
    try:
        with _session() as session:
            session.add(row)
            session.commit()
    except SQLAlchemyError as exc:
        raise RfpStorageError("rfp_insert") from exc


def get_ticket(ticket_id: str) -> RfpTicket | None:
    try:
        with _session() as session:
            row = session.get(RfpTicket, ticket_id)
            if row is not None:
                session.expunge(row)
            return row
    except SQLAlchemyError as exc:
        raise RfpStorageError("rfp_read") from exc


def touch(ticket_id: str) -> None:
    with ticket_lock(ticket_id):
        try:
            with _session() as session:
                row = session.get(RfpTicket, ticket_id)
                if row is None or row.status != "analyzing":
                    return
                row.updated_at = utcnow()
                session.add(row)
                session.commit()
        except SQLAlchemyError as exc:
            raise RfpStorageError("rfp_touch") from exc


def mark_failed(ticket_id: str, code: str) -> bool:
    safe = code if code in PIPELINE_MESSAGES else "pipeline_crashed"
    with ticket_lock(ticket_id):
        try:
            with _session() as session:
                row = session.get(RfpTicket, ticket_id)
                if row is None or row.status != "analyzing":
                    return False
                row.status = "failed"
                row.pipeline_error_code = safe
                row.handoff_ready = False
                row.updated_at = utcnow()
                session.add(row)
                session.commit()
                return True
        except SQLAlchemyError as exc:
            raise RfpStorageError("rfp_fail") from exc


def mark_interrupted_if_stale(ticket_id: str, stale_after_seconds: int) -> bool:
    with ticket_lock(ticket_id):
        try:
            with _session() as session:
                row = session.get(RfpTicket, ticket_id)
                if row is None or row.status != "analyzing":
                    return False
                age = utcnow() - _as_utc(row.updated_at)
                if age <= timedelta(seconds=stale_after_seconds):
                    return False
                row.status = "failed"
                row.pipeline_error_code = "pipeline_interrupted"
                row.handoff_ready = False
                row.updated_at = utcnow()
                session.add(row)
                session.commit()
                return True
        except SQLAlchemyError as exc:
            raise RfpStorageError("rfp_stale") from exc


def reset_for_reprocess(ticket_id: str) -> bool:
    with ticket_lock(ticket_id):
        try:
            with _session() as session:
                row = session.get(RfpTicket, ticket_id)
                if row is None or row.status not in {"failed", "discarded"}:
                    return False
                for section in session.exec(
                    select(RfpDepartmentSection).where(
                        RfpDepartmentSection.ticket_id == ticket_id
                    )
                ):
                    session.delete(section)
                meta = session.get(RfpMetadata, ticket_id)
                if meta is not None:
                    session.delete(meta)
                row.status = "analyzing"
                row.discard_reason_code = None
                row.pipeline_error_code = None
                row.phi_detected = False
                row.handoff_ready = False
                row.handoff_json = None
                row.rfp_id = None
                row.updated_at = utcnow()
                session.add(row)
                session.commit()
                return True
        except SQLAlchemyError as exc:
            raise RfpStorageError("rfp_reprocess") from exc


def save_discard(
    ticket_id: str,
    *,
    reason_code: str,
    phi_detected: bool,
    readability: dict[str, Any],
) -> bool:
    with ticket_lock(ticket_id):
        try:
            with _session() as session:
                row = session.get(RfpTicket, ticket_id)
                if row is None or row.status != "analyzing":
                    return False
                _replace_metadata(session, ticket_id, readability, metadata=None, questions=[])
                row.status = "discarded"
                row.discard_reason_code = reason_code
                row.phi_detected = phi_detected
                row.pipeline_error_code = None
                row.handoff_ready = False
                row.handoff_json = None
                row.updated_at = utcnow()
                session.add(row)
                session.commit()
                return True
        except SQLAlchemyError as exc:
            raise RfpStorageError("rfp_discard") from exc


def save_complete(
    ticket_id: str,
    *,
    phi_detected: bool,
    readability: dict[str, Any],
    metadata: dict[str, Any],
    sections: list[dict[str, Any]],
    handoff: dict[str, Any],
) -> bool:
    with ticket_lock(ticket_id):
        try:
            with _session() as session:
                row = session.get(RfpTicket, ticket_id)
                if row is None or row.status != "analyzing":
                    return False
                questions = list(metadata.get("open_questions") or [])
                _replace_metadata(
                    session,
                    ticket_id,
                    readability,
                    metadata=metadata,
                    questions=questions,
                )
                _replace_sections(session, ticket_id, sections)
                row.status = "intake_complete"
                row.rfp_id = f"RFP-{ticket_id[:8]}"
                row.phi_detected = phi_detected
                row.pipeline_error_code = None
                row.discard_reason_code = None
                row.handoff_ready = True
                row.handoff_json = handoff
                row.updated_at = utcnow()
                session.add(row)
                session.commit()
                return True
        except SQLAlchemyError as exc:
            raise RfpStorageError("rfp_complete") from exc


_RESPONSE_FROM = {"intake_complete", "drafting", "under_evaluation"}


def set_response_status(ticket_id: str, status: str) -> bool:
    """Move a Part 2 ticket forward. Parallel workers must not call this."""
    if status not in {"drafting", "under_evaluation", "needs_human_review"}:
        return False
    with ticket_lock(ticket_id):
        try:
            with _session() as session:
                row = session.get(RfpTicket, ticket_id)
                if row is None or row.status not in _RESPONSE_FROM:
                    return False
                if row.status == status:
                    return True
                handoff = dict(row.handoff_json or {})
                trail = list(handoff.get("status_trail") or [])
                trail.append(status)
                handoff["status_trail"] = trail
                row.status = status
                row.handoff_json = handoff
                row.updated_at = utcnow()
                session.add(row)
                session.commit()
                return True
        except SQLAlchemyError as exc:
            raise RfpStorageError("rfp_response_status") from exc


def save_response(
    ticket_id: str,
    *,
    final_status: str,
    part2_outcome: str,
    sections: list[dict[str, Any]],
    iteration_limit: int,
) -> bool:
    """Write drafts and evaluation results. Does not clear the Part 1 handoff."""
    if final_status not in {"under_evaluation", "needs_human_review"}:
        return False
    with ticket_lock(ticket_id):
        try:
            with _session() as session:
                row = session.get(RfpTicket, ticket_id)
                if row is None or row.status not in _RESPONSE_FROM | {"needs_human_review"}:
                    return False
                by_id = {
                    section.department_id: section
                    for section in session.exec(
                        select(RfpDepartmentSection).where(
                            RfpDepartmentSection.ticket_id == ticket_id
                        )
                    )
                }
                for section in sections:
                    current = by_id.get(str(section["department_id"]))
                    if current is None:
                        continue
                    current.draft_content = str(section.get("draft_content") or "")
                    current.evaluation_results = dict(section.get("evaluation_results") or {})
                    if section.get("contains_phi"):
                        current.contains_phi = True
                    session.add(current)
                handoff = dict(row.handoff_json or {})
                trail = list(handoff.get("status_trail") or [])
                if row.status != final_status:
                    trail.append(final_status)
                handoff["status_trail"] = trail
                handoff["part"] = 2
                handoff["next"] = "part3_approval"
                handoff["part2_outcome"] = part2_outcome
                handoff["evaluation_closed"] = True
                handoff["iteration_limit"] = iteration_limit
                handoff["sections"] = list(sections)
                row.handoff_json = handoff
                row.status = final_status
                row.handoff_ready = True
                row.pipeline_error_code = None
                row.updated_at = utcnow()
                session.add(row)
                session.commit()
                return True
        except SQLAlchemyError as exc:
            raise RfpStorageError("rfp_response_save") from exc


def mark_response_needs_review(ticket_id: str) -> bool:
    """Keep the ticket when drafting stops. Do not discard it."""
    with ticket_lock(ticket_id):
        try:
            with _session() as session:
                row = session.get(RfpTicket, ticket_id)
                if row is None or row.status not in _RESPONSE_FROM:
                    return False
                handoff = dict(row.handoff_json or {})
                trail = list(handoff.get("status_trail") or [])
                trail.append("needs_human_review")
                handoff["status_trail"] = trail
                handoff["part"] = 2
                handoff["next"] = "part3_approval"
                handoff["part2_outcome"] = "needs_human_review"
                handoff["evaluation_closed"] = True
                row.handoff_json = handoff
                row.status = "needs_human_review"
                row.handoff_ready = True
                row.pipeline_error_code = "response_interrupted"
                row.updated_at = utcnow()
                session.add(row)
                session.commit()
                return True
        except SQLAlchemyError as exc:
            raise RfpStorageError("rfp_response_review") from exc


def _replace_metadata(
    session: Session,
    ticket_id: str,
    readability: dict[str, Any],
    *,
    metadata: dict[str, Any] | None,
    questions: list[str],
) -> None:
    existing = session.get(RfpMetadata, ticket_id)
    if existing is not None:
        session.delete(existing)
        session.flush()
    meta = metadata or {}
    session.add(
        RfpMetadata(
            ticket_id=ticket_id,
            client_name=str(meta.get("client_name") or ""),
            client_country=str(meta.get("client_country") or ""),
            program_type=str(meta.get("program_type") or ""),
            covered_population=meta.get("covered_population"),
            deadline=str(meta.get("deadline") or ""),
            budget_range=str(meta.get("budget_range") or ""),
            currency=str(meta.get("currency") or ""),
            departments_needed=list(meta.get("departments_needed") or []),
            flesch_reading_ease=readability.get("flesch_reading_ease"),
            flesch_kincaid_grade=readability.get("flesch_kincaid_grade"),
            gunning_fog=readability.get("gunning_fog"),
            word_count=int(readability.get("word_count") or 0),
            estimated_tokens=int(readability.get("estimated_tokens") or 0),
            cost_band=str(readability.get("cost_band") or ""),
            open_questions=questions,
            readability_note=str(readability.get("readability_note") or ""),
        )
    )


def _replace_sections(session: Session, ticket_id: str, sections: list[dict[str, Any]]) -> None:
    for existing in session.exec(
        select(RfpDepartmentSection).where(RfpDepartmentSection.ticket_id == ticket_id)
    ):
        session.delete(existing)
    session.flush()
    for section in sections:
        session.add(
            RfpDepartmentSection(
                ticket_id=ticket_id,
                department_id=str(section["department_id"]),
                owner_name=str(section.get("owner_name") or ""),
                owner_role=str(section.get("owner_role") or ""),
                key_aspects=list(section.get("key_aspects") or []),
                open_questions=list(section.get("open_questions") or []),
                claims=dict(section.get("claims") or {}),
                contains_phi=bool(section.get("contains_phi")),
            )
        )


def _metadata_dict(row: RfpMetadata | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {
        "client_name": row.client_name,
        "client_country": row.client_country,
        "program_type": row.program_type,
        "covered_population": row.covered_population,
        "deadline": row.deadline,
        "budget_range": row.budget_range,
        "currency": row.currency,
        "departments_needed": list(row.departments_needed or []),
        "flesch_reading_ease": row.flesch_reading_ease,
        "flesch_kincaid_grade": row.flesch_kincaid_grade,
        "gunning_fog": row.gunning_fog,
        "word_count": row.word_count,
        "estimated_tokens": row.estimated_tokens,
        "cost_band": row.cost_band,
        "open_questions": list(row.open_questions or []),
        "readability_note": row.readability_note,
    }


def _section_dict(row: RfpDepartmentSection) -> dict[str, Any]:
    evaluation = dict(row.evaluation_results or {})
    draft = str(row.draft_content or "")
    withheld = contains_phi(draft)
    flagged = bool(row.contains_phi or evaluation.get("contains_phi") or withheld)
    return {
        "department_id": row.department_id,
        "owner_name": row.owner_name,
        "owner_role": row.owner_role,
        "key_aspects": list(row.key_aspects or []),
        "open_questions": list(row.open_questions or []),
        "contains_phi": flagged,
        "draft_content": "" if withheld else draft,
        "draft_withheld": withheld,
        "review_state": str(evaluation.get("review_state") or ""),
        "provisional": bool(evaluation.get("provisional")),
        "evaluation": evaluation or None,
    }


def ticket_view(ticket_id: str, *, stale_after_seconds: int) -> dict[str, Any] | None:
    mark_interrupted_if_stale(ticket_id, stale_after_seconds)
    try:
        with _session() as session:
            row = session.get(RfpTicket, ticket_id)
            if row is None:
                return None
            meta = session.get(RfpMetadata, ticket_id)
            sections = session.exec(
                select(RfpDepartmentSection)
                .where(RfpDepartmentSection.ticket_id == ticket_id)
                .order_by(col(RfpDepartmentSection.id))
            ).all()
            return _view(row, meta, sections)
    except SQLAlchemyError as exc:
        raise RfpStorageError("rfp_view") from exc


def list_tickets(*, stale_after_seconds: int) -> list[dict[str, Any]]:
    try:
        with _session() as session:
            rows = session.exec(select(RfpTicket).order_by(col(RfpTicket.created_at).desc())).all()
            ids = [row.ticket_id for row in rows if row.status == "analyzing"]
    except SQLAlchemyError as exc:
        raise RfpStorageError("rfp_list") from exc
    for ticket_id in ids:
        mark_interrupted_if_stale(ticket_id, stale_after_seconds)
    try:
        with _session() as session:
            rows = session.exec(select(RfpTicket).order_by(col(RfpTicket.created_at).desc())).all()
            views = []
            for row in rows:
                meta = session.get(RfpMetadata, row.ticket_id)
                views.append(_summary(row, meta))
            return views
    except SQLAlchemyError as exc:
        raise RfpStorageError("rfp_list") from exc


def _summary(row: RfpTicket, meta: RfpMetadata | None) -> dict[str, Any]:
    return {
        "ticket_id": row.ticket_id,
        "rfp_id": row.rfp_id,
        "status": row.status,
        "original_filename": row.original_filename,
        "phi_detected": row.phi_detected,
        "handoff_ready": row.handoff_ready,
        "discard_reason_code": row.discard_reason_code,
        "discard_message": DISCARD_MESSAGES.get(row.discard_reason_code or "", ""),
        "pipeline_error_code": row.pipeline_error_code,
        "pipeline_message": PIPELINE_MESSAGES.get(row.pipeline_error_code or "", ""),
        "client_name": meta.client_name if meta else "",
        "client_country": meta.client_country if meta else "",
        "part2_outcome": str((row.handoff_json or {}).get("part2_outcome") or ""),
        "created_at": _as_utc(row.created_at).isoformat(),
        "updated_at": _as_utc(row.updated_at).isoformat(),
    }


def _view(
    row: RfpTicket,
    meta: RfpMetadata | None,
    sections: list[RfpDepartmentSection],
) -> dict[str, Any]:
    handoff = row.handoff_json or {}
    body = _summary(row, meta)
    body["pdf_stored"] = bool(row.raw_pdf_path)
    body["metadata"] = _metadata_dict(meta)
    body["sections"] = [_section_dict(section) for section in sections]
    body["sales_summary"] = str(handoff.get("sales_summary") or "")
    body["conflicts"] = list(handoff.get("conflicts") or [])
    body["part2_guard"] = str(handoff.get("part2_guard") or "")
    body["part2_outcome"] = str(handoff.get("part2_outcome") or "")
    body["evaluation_closed"] = bool(handoff.get("evaluation_closed"))
    body["status_trail"] = list(handoff.get("status_trail") or [])
    return body
