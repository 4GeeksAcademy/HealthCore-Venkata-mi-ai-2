"""LangGraph nodes for RFP intake. The knowledge-agent graph is not imported."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from . import store
from .agents import (
    CompleteJson,
    classify_document,
    default_complete_json,
    extract_metadata,
    find_conflicts,
    run_worker,
    synthesize,
)
from .convert import convert_pdf
from .departments import DEPARTMENT_IDS, UNKNOWN_DEPARTMENT_CUES
from .errors import ModelUnavailable
from .extracts import department_extract, unknown_departments
from .metrics import measure
from .phi import redact
from .state import RfpState

_UNKNOWN_LABELS = dict(UNKNOWN_DEPARTMENT_CUES)


@dataclass
class RfpDeps:
    convert_pdf: Callable[[str], str] = convert_pdf
    measure: Callable[[str], dict] = measure
    complete_json: CompleteJson = default_complete_json


def convert_node(deps: RfpDeps) -> Callable[[RfpState], dict]:
    def _node(state: RfpState) -> dict:
        store.touch(state["ticket_id"])
        markdown = deps.convert_pdf(state["ticket_id"])
        return {"markdown": markdown}

    return _node


def readability_node(deps: RfpDeps) -> Callable[[RfpState], dict]:
    def _node(state: RfpState) -> dict:
        store.touch(state["ticket_id"])
        return {"readability": deps.measure(state.get("markdown") or "")}

    return _node


def screen_phi_node(state: RfpState) -> dict:
    store.touch(state["ticket_id"])
    redacted, found = redact(state.get("markdown") or "")
    return {"redacted_markdown": redacted, "phi_detected": found}


def classify_node(deps: RfpDeps) -> Callable[[RfpState], dict]:
    def _node(state: RfpState) -> dict:
        store.touch(state["ticket_id"])
        try:
            is_rfp, reason = classify_document(
                state.get("redacted_markdown") or "",
                complete=deps.complete_json,
            )
        except ModelUnavailable as exc:
            raise ModelUnavailable("classifier_unavailable") from exc
        return {"is_rfp": is_rfp, "discard_reason_code": reason}

    return _node


def route_after_classify(state: RfpState) -> str:
    if state.get("is_rfp"):
        return "extract_metadata"
    return "persist_discard"


def extract_metadata_node(deps: RfpDeps) -> Callable[[RfpState], dict]:
    def _node(state: RfpState) -> dict:
        store.touch(state["ticket_id"])
        try:
            metadata = extract_metadata(
                state.get("redacted_markdown") or "",
                complete=deps.complete_json,
            )
        except ModelUnavailable as exc:
            raise ModelUnavailable("worker_unavailable") from exc
        return {"metadata": metadata}

    return _node


def orchestrate_node(state: RfpState) -> dict:
    store.touch(state["ticket_id"])
    redacted = state.get("redacted_markdown") or ""
    metadata = dict(state.get("metadata") or {})
    questions = list(metadata.get("open_questions") or [])
    unknown = unknown_departments(redacted)
    for department_id in unknown:
        label = _UNKNOWN_LABELS.get(department_id, department_id)
        questions.append(
            f"The RFP mentions {label}, which is not a proposal department. No worker was assigned."
        )
    metadata["open_questions"] = questions
    metadata["departments_needed"] = list(DEPARTMENT_IDS)
    work_items = [
        {
            "department_id": department_id,
            "metadata": metadata,
            "extract": department_extract(redacted, department_id),
        }
        for department_id in DEPARTMENT_IDS
    ]
    return {
        "metadata": metadata,
        "unknown_departments": unknown,
        "work_items": work_items,
        "markdown": "",
        "redacted_markdown": "",
    }


def fan_out(state: RfpState) -> list[Any]:
    from langgraph.types import Send

    return [
        Send(
            "department_worker",
            {
                "ticket_id": state["ticket_id"],
                "work_item": item,
            },
        )
        for item in state.get("work_items") or []
    ]


def department_worker_node(deps: RfpDeps) -> Callable[[RfpState], dict]:
    def _node(state: RfpState) -> dict:
        item = state.get("work_item") or {}
        department_id = str(item.get("department_id") or "")
        store.touch(state["ticket_id"])
        try:
            section = run_worker(
                department_id,
                dict(item.get("metadata") or {}),
                str(item.get("extract") or ""),
                complete=deps.complete_json,
            )
        except ModelUnavailable as exc:
            raise ModelUnavailable("worker_unavailable") from exc
        return {"section_results": [section]}

    return _node


def synthesize_node(deps: RfpDeps) -> Callable[[RfpState], dict]:
    def _node(state: RfpState) -> dict:
        store.touch(state["ticket_id"])
        sections = list(state.get("section_results") or [])
        order = {department_id: index for index, department_id in enumerate(DEPARTMENT_IDS)}
        sections.sort(key=lambda section: order.get(str(section.get("department_id")), 99))
        conflicts = find_conflicts(sections)
        summary, source = synthesize(
            dict(state.get("metadata") or {}),
            sections,
            conflicts,
            phi_detected=bool(state.get("phi_detected")),
            complete=deps.complete_json,
        )
        return {
            "conflicts": conflicts,
            "sales_summary": summary,
            "summary_source": source,
            "_ordered_sections": sections,
        }

    return _node


def _handoff(state: RfpState, sections: list[dict]) -> dict[str, Any]:
    phi = bool(state.get("phi_detected")) or any(section.get("contains_phi") for section in sections)
    return {
        "ticket_id": state["ticket_id"],
        "part": 1,
        "next": "part2_drafting",
        "phi_detected": phi,
        "part2_guard": "phi_review_required" if phi else "",
        "metadata": state.get("metadata") or {},
        "sections": sections,
        "conflicts": state.get("conflicts") or [],
        "sales_summary": state.get("sales_summary") or "",
        "summary_source": state.get("summary_source") or "structured",
    }


def persist_discard_node(state: RfpState) -> dict:
    saved = store.save_discard(
        state["ticket_id"],
        reason_code=str(state.get("discard_reason_code") or "uncertain"),
        phi_detected=bool(state.get("phi_detected")),
        readability=dict(state.get("readability") or {}),
    )
    return {
        "status": "discarded" if saved else state.get("status") or "analyzing",
        "markdown": "",
        "redacted_markdown": "",
    }


def persist_complete_node(state: RfpState) -> dict:
    sections = list(state.get("_ordered_sections") or [])
    if not sections:
        sections = list(state.get("section_results") or [])
    order = {department_id: index for index, department_id in enumerate(DEPARTMENT_IDS)}
    sections.sort(key=lambda section: order.get(str(section.get("department_id")), 99))
    handoff = _handoff(state, sections)
    phi = bool(handoff["phi_detected"])
    saved = store.save_complete(
        state["ticket_id"],
        phi_detected=phi,
        readability=dict(state.get("readability") or {}),
        metadata=dict(state.get("metadata") or {}),
        sections=sections,
        handoff=handoff,
    )
    return {
        "status": "intake_complete" if saved else state.get("status") or "analyzing",
        "handoff": handoff if saved else {},
        "markdown": "",
        "redacted_markdown": "",
        "_ordered_sections": [],
    }
