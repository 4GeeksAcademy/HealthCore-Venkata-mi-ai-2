"""HealthCore coordinator knowledge base — retrieval and generation.

``query()`` is the only entrypoint external consumers (the FastAPI router, the UI
through it) should call. It is literally ``retrieve()`` + ``generate_answer()`` so
a later agent can run those two steps separately.

Indexing and ``embed()`` live in ``data/process/rag.py``.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Callable

from data.process.rag import (
    COLLECTION_NAME,
    assert_distinct_models,
    embed,
    generation_model,
    get_llm_client,
    get_qdrant_client,
)

logger = logging.getLogger(__name__)

DEFAULT_K = 5
DEFAULT_MIN_SCORE = 0.30



class KnowledgeBaseUnavailable(RuntimeError):
    """Embeddings, Qdrant, or the generation model could not be reached."""


NO_CONTEXT_SENTENCE = (
    "I don't have enough information in the HealthCore knowledge base to answer that."
)

SYSTEM_PROMPT = f"""You are the HealthCore front-desk knowledge assistant for patient coordinators.
HealthCore runs 12 outpatient clinics in the United States (Texas, Florida, Georgia) and the United Kingdom (London, Manchester).

Audience and voice:
- You are speaking to a patient coordinator at the desk or on the phone, not to a patient.
- Answer the way the clinic's best service salesperson would: clear, warm, empathetic, and direct. Lead with the answer, then the conditions that apply.
- Keep it short enough to read aloud to a patient. Use short bullets when there are several conditions.

Hard rules:
1. Use ONLY the facts in the CONTEXT block. Never add coverage, fees, timeframes, or policies that are not written there. Repeat amounts, currencies, hours, and day counts exactly as written.
2. If the CONTEXT block is empty or does not answer the question, reply exactly: "{NO_CONTEXT_SENTENCE}" Then suggest the coordinator check with the relevant team. Do not guess.
3. Insurance: if the question does not say the country, answer separately for the United States and the United Kingdom.
4. Insurance: if an insurer or plan is not listed in the CONTEXT, never confirm it. Say it is not on the documented list and must be verified with the billing team (Tom Callahan) before confirming anything to the patient.
5. No-show and late-cancellation fees never apply to Medicare or Medicaid patients. Say so whenever fees come up and the patient could be on Medicare or Medicaid.
6. Never ask for, repeat, or invent patient names, record numbers, member IDs, or diagnoses.
7. End with one line starting "Source:" listing the document and section you used, e.g. "Source: appointment-policy › Cancellation policy". Omit the Source line when you had no usable context."""


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------


def default_min_score() -> float:
    return float(os.getenv("RAG_MIN_SCORE", str(DEFAULT_MIN_SCORE)))


def retrieve(
    query: str,
    *,
    k: int = DEFAULT_K,
    min_score: float | None = None,
    client: Any | None = None,
    embed_fn: Callable[[str], list[float]] = embed,
) -> list[dict[str, Any]]:
    """Top-k payloads for ``query`` whose cosine similarity is at least ``min_score``.

    Hits below the threshold are dropped, so fewer than ``k`` (or zero) can come
    back. Returns plain payload dicts plus ``score`` — never Qdrant SDK objects.
    """
    threshold = default_min_score() if min_score is None else min_score
    try:
        vector = embed_fn(query)
    except Exception as exc:
        raise KnowledgeBaseUnavailable("embedding model unavailable") from exc
    try:
        qdrant = client or get_qdrant_client()
        response = qdrant.query_points(
            collection_name=COLLECTION_NAME,
            query=vector,
            limit=k,
            with_payload=True,
        )
    except Exception as exc:
        raise KnowledgeBaseUnavailable("vector store unavailable") from exc
    results: list[dict[str, Any]] = []
    for point in response.points:
        if point.score < threshold:
            continue
        results.append({**dict(point.payload or {}), "score": float(point.score)})
    return results


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------


def build_prompt(question: str, context: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Chat messages: coordinator system prompt + numbered context + the question."""
    if context:
        blocks = [
            f"[{n}] {item.get('source_document', 'unknown')} › {item.get('section', '')}\n"
            f"{item.get('text', '')}"
            for n, item in enumerate(context, start=1)
        ]
        context_block = "\n\n".join(blocks)
    else:
        context_block = "(no relevant passages were found in the knowledge base)"
    user_message = f"CONTEXT:\n{context_block}\n\nCOORDINATOR QUESTION:\n{question.strip()}"
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]


def generate_answer(
    question: str,
    context: list[dict[str, Any]],
    *,
    llm_client: Any | None = None,
) -> str:
    """Prompt assembly + generation LLM call. Always goes through the model,
    including when ``context`` is empty (the prompt then forces the
    not-enough-information reply)."""
    assert_distinct_models()
    messages = build_prompt(question, context)
    try:
        client = llm_client or get_llm_client()
        completion = client.chat.completions.create(
            model=generation_model(),
            messages=messages,
            temperature=0,
            max_tokens=500,
        )
    except Exception as exc:
        raise KnowledgeBaseUnavailable("generation model unavailable") from exc
    answer = (completion.choices[0].message.content or "").strip()
    return answer or NO_CONTEXT_SENTENCE


# ---------------------------------------------------------------------------
# Public entrypoint
# ---------------------------------------------------------------------------


def query(question: str) -> str:
    """Answer a coordinator question from the knowledge base. Returns the model's text only."""
    context = retrieve(question)
    # Chunk ids and scores only — the question may contain details typed at the desk.
    logger.info(
        "knowledge retrieve hits=%d %s",
        len(context),
        ", ".join(
            f"{item.get('source_document')}#{item.get('chunk_index')}={item['score']:.3f}"
            for item in context
        ),
    )
    return generate_answer(question, context)
