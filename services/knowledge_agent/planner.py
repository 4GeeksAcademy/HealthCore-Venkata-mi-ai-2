"""Decides which sources a question needs: the knowledge base, a live tool, or both.

``SourcePlanner`` asks the generation model for a JSON plan and validates it.
If the model is unreachable or replies with anything that does not validate,
``rules_plan`` decides instead and the plan records ``rules_fallback``. A ticket
id is only ever taken from the question text, never from the model.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from data.process.rag import generation_model, get_llm_client

from .state import SourceName, SourcePlan

logger = logging.getLogger(__name__)

PLANNER_TIMEOUT_SECONDS = 8.0
PLANNER_MAX_RETRIES = 1
SOURCE_ORDER: tuple[SourceName, ...] = ("ticket", "inventory", "knowledge_base")

_TICKET_ID_RES = (
    re.compile(r"\bINC[-\s#]?(\d{1,6})\b", re.IGNORECASE),
    re.compile(r"\b(?:ticket|incident|case)\s*(?:number|no\.?|id)?\s*#?\s*(\d{1,6})\b", re.IGNORECASE),
)
_TICKET_WORD_RE = re.compile(r"\b(?:tickets?|incidents?)\b", re.IGNORECASE)
_STATUS_RE = re.compile(r"\b(open|in[_\s-]?progress|resolved|discarded|closed)\b", re.IGNORECASE)
_CATEGORY_RES: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\b(?:appointment|patient experience|accessibility)\b", re.IGNORECASE), "patient_experience"),
    (re.compile(r"\bbilling\b", re.IGNORECASE), "billing_error"),
    (re.compile(r"\b(?:clinical equipment|equipment)\b", re.IGNORECASE), "clinical_equipment"),
    (re.compile(r"\b(?:IT|system|ehr|portal)\b", re.IGNORECASE), "it_system"),
    (re.compile(r"\b(?:staff|workforce)\b", re.IGNORECASE), "staff_issue"),
    (re.compile(r"\bfacilit(?:y|ies)\b", re.IGNORECASE), "facility_issue"),
    (re.compile(r"\breferral\b", re.IGNORECASE), "referral_issue"),
    (re.compile(r"\bcompliance\b", re.IGNORECASE), "compliance_breach"),
)
_BRANCH_RE = re.compile(
    r"\b(central|austin_north|dallas_uptown|houston_med_center|san_antonio_west|"
    r"miami_brickell|miami_doral|orlando_east|tampa_bay|atlanta_midtown|savannah|"
    r"london_city|london_west|manchester_central)\b",
    re.IGNORECASE,
)

_STOCK_RE = re.compile(
    r"\b(?:in stock|out of stock|stock (?:of|for|levels?)|inventory|run(?:ning)? out of|how many .{1,60}? left)\b",
    re.IGNORECASE,
)
_WEAK_STOCK_RE = re.compile(r"\bdo we (?:still )?have any\b", re.IGNORECASE)
_INVENTORY_FILLER_RE = re.compile(
    r"\b(?:can you|could you|please|check|tell me|do we (?:still )?have|have we got|is there|are there|"
    r"how many|how much|any|stock levels?|stock of|stock for|in stock|out of stock|inventory(?: of| for)?|"
    r"left|units? of|run(?:ning)? out of|currently|right now|at the moment|today|are|is|we|our|the|of)\b",
    re.IGNORECASE,
)
_POLICY_RE = re.compile(
    r"\b(?:polic(?:y|ies)|fees?|charged?|cost|price|insurance|insurers?|accept(?:ed)?|cover(?:age|ed)?|"
    r"documents?|bring|escalat\w*|referrals?|procedures?|process|rules?|allowed|should i|what do i tell)\b",
    re.IGNORECASE,
)

PLANNER_PROMPT = """You route questions from HealthCore patient coordinators to data sources.

Sources:
- "ticket": the live incident manager. Use it for the status, category, or branch of a support ticket / incident (ids look like INC-0042, a UUID, or "ticket 482"), or to count or list tickets filtered by status (open, in_progress, resolved, discarded), category (billing_error, patient_experience, …), or branch (e.g. houston_med_center).
- "inventory": the live inventory manager. Use it for current stock of a clinic supply product.
- "knowledge_base": HealthCore policies and procedures (fees, cancellations, no-shows, insurance accepted, new-patient documents, referral escalation). Use it for anything that is not live ticket or stock data, and when unsure.

A question may need more than one source. Reply with JSON only, no prose:
{"sources": ["ticket" | "inventory" | "knowledge_base", ...],
 "ticket": {"ticket_id": "INC-0042" or null, "status": null, "category": null, "branch": null} or null,
 "inventory": {"product_query": "product name as written"} or null,
 "knowledge_question": "the policy part of the question as a standalone question" or null}
Only copy a ticket id that is written in the question. Never invent one.
Set knowledge_question only when "knowledge_base" is combined with another source; leave out the ticket or stock part."""


def extract_ticket_id(text: str) -> str | None:
    for pattern in _TICKET_ID_RES:
        found = pattern.search(text or "")
        if found:
            return f"INC-{int(found.group(1)):04d}"
    return None


def _normalize_status(raw: str) -> str:
    value = raw.strip().lower().replace(" ", "_").replace("-", "_")
    if value == "closed":
        return "resolved"
    if value == "inprogress":
        return "in_progress"
    return value


def _ticket_filters(question: str) -> dict[str, Any]:
    filters: dict[str, Any] = {}
    if status := _STATUS_RE.search(question):
        filters["status"] = _normalize_status(status.group(1))
    for pattern, category in _CATEGORY_RES:
        if pattern.search(question):
            filters["category"] = category
            break
    if branch := _BRANCH_RE.search(question):
        filters["branch"] = branch.group(1).lower()
    return filters


def extract_product_query(question: str) -> str | None:
    text = _INVENTORY_FILLER_RE.sub(" ", question)
    text = " ".join(re.sub(r"[^\w\s\-/.]", " ", text).split()).strip(" .-")
    return text if len(text) >= 2 else None


_CLAUSE_SPLIT_RE = re.compile(r"(?<=[.?!])\s+|,\s*(?:and|but)\s+|;\s*")


def extract_policy_question(question: str) -> str | None:
    """The clauses of a mixed question that ask about policy, so the RAG never sees the ticket part."""
    clauses = [c.strip(" ,.?!") for c in _CLAUSE_SPLIT_RE.split(question) if c.strip(" ,.?!")]
    policy = [c for c in clauses if _POLICY_RE.search(c) and not extract_ticket_id(c)]
    if not policy:
        return None
    text = "; ".join(policy)
    return text[0].upper() + text[1:] + "?"


def _plan(
    sources: set[str],
    ticket_input: dict[str, Any] | None,
    inventory_input: dict[str, Any] | None,
    planner: Literal["llm", "rules", "rules_fallback"],
    knowledge_question: str | None = None,
) -> SourcePlan:
    ordered = [s for s in SOURCE_ORDER if s in sources] or ["knowledge_base"]
    mixed = "knowledge_base" in ordered and len(ordered) > 1
    return {
        "sources": ordered,
        "ticket_input": ticket_input if "ticket" in ordered else None,
        "inventory_input": inventory_input if "inventory" in ordered else None,
        "knowledge_question": knowledge_question if mixed else None,
        "planner": planner,
    }


def rules_plan(question: str, *, planner: Literal["rules", "rules_fallback"] = "rules") -> SourcePlan:
    sources: set[str] = set()
    ticket_input: dict[str, Any] | None = None
    inventory_input: dict[str, Any] | None = None

    ticket_id = extract_ticket_id(question)
    filters = _ticket_filters(question)
    if ticket_id:
        sources.add("ticket")
        ticket_input = {"ticket_id": ticket_id}
    elif _TICKET_WORD_RE.search(question) and ("status" in filters or "category" in filters):
        sources.add("ticket")
        ticket_input = filters

    if _STOCK_RE.search(question) or ("ticket" not in sources and _WEAK_STOCK_RE.search(question)):
        sources.add("inventory")
        inventory_input = {"product_query": extract_product_query(question)}

    if not sources or _POLICY_RE.search(question):
        sources.add("knowledge_base")
    return _plan(sources, ticket_input, inventory_input, planner, extract_policy_question(question))


class _TicketRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    ticket_id: str | None = None
    status: str | None = None
    category: str | None = None
    branch: str | None = None


class _InventoryRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    product_query: str | None = None


class _LlmPlan(BaseModel):
    model_config = ConfigDict(extra="ignore")

    sources: list[SourceName] = Field(min_length=1)
    ticket: _TicketRequest | None = None
    inventory: _InventoryRequest | None = None
    knowledge_question: str | None = Field(default=None, max_length=1000)


def _parse_reply(text: str) -> _LlmPlan:
    body = (text or "").strip()
    if body.startswith("```"):
        body = body.strip("`").removeprefix("json").strip()
    start, end = body.find("{"), body.rfind("}")
    if start < 0 or end < start:
        raise ValueError("planner reply has no JSON object")
    return _LlmPlan.model_validate(json.loads(body[start : end + 1]))


def plan_from_llm_reply(question: str, reply: str) -> SourcePlan:
    """Validate the model's plan and ground it in the question. Raises on invalid replies."""
    parsed = _parse_reply(reply)
    sources = set(parsed.sources)

    ticket_input: dict[str, Any] | None = None
    if "ticket" in sources:
        requested = parsed.ticket or _TicketRequest()
        # The id must be written in the question; the model's copy is only a hint.
        ticket_id = extract_ticket_id(question)
        if ticket_id:
            ticket_input = {"ticket_id": ticket_id}
        else:
            ticket_input = {
                key: value
                for key, value in {
                    "status": _normalize_status(requested.status) if requested.status else None,
                    "category": (requested.category or "").lower() or None,
                    "branch": (requested.branch or "").lower() or None,
                }.items()
                if value
            }

    inventory_input: dict[str, Any] | None = None
    if "inventory" in sources:
        query = (parsed.inventory.product_query if parsed.inventory else None) or extract_product_query(question)
        inventory_input = {"product_query": query.strip() if query else None}

    knowledge_question = (parsed.knowledge_question or "").strip() or extract_policy_question(question)
    return _plan(sources, ticket_input, inventory_input, "llm", knowledge_question)


class SourcePlanner:
    """LLM plan first; the rules decide whenever the model cannot."""

    def __init__(self, llm_client: Any | None = None, model: str | None = None) -> None:
        self._llm_client = llm_client
        self._model = model

    def __call__(self, question: str) -> SourcePlan:
        try:
            client = self._llm_client or get_llm_client()
            if hasattr(client, "with_options"):
                client = client.with_options(max_retries=PLANNER_MAX_RETRIES)
            completion = client.chat.completions.create(
                model=self._model or generation_model(),
                messages=[
                    {"role": "system", "content": PLANNER_PROMPT},
                    {"role": "user", "content": question},
                ],
                temperature=0,
                max_tokens=200,
                timeout=PLANNER_TIMEOUT_SECONDS,
            )
            return plan_from_llm_reply(question, completion.choices[0].message.content or "")
        except (ValidationError, ValueError) as exc:
            logger.warning("agent planner reply rejected (%s); using rules", type(exc).__name__)
        except Exception as exc:  # gateway, network, or auth failure: route anyway
            logger.warning("agent planner unavailable (%s); using rules", type(exc).__name__)
        return rules_plan(question, planner="rules_fallback")
