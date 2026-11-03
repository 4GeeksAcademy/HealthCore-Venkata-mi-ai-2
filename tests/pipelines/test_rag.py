"""Unit tests for the HealthCore coordinator knowledge base (Milestone 7 RAG).

No live Qdrant, embeddings, or generation model: every external call is a stub.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from data.pipelines import rag as pipeline  # noqa: E402
from data.process import rag as process  # noqa: E402


# ---------------------------------------------------------------------------
# Stubs
# ---------------------------------------------------------------------------


@dataclass
class _Point:
    score: float
    payload: dict[str, Any]


@dataclass
class FakeQdrant:
    """Stand-in for QdrantClient.query_points: returns canned hits, ranked by score."""

    hits: list[_Point]
    calls: list[dict[str, Any]] = field(default_factory=list)

    def query_points(self, *, collection_name: str, query: list[float], limit: int, with_payload: bool):
        self.calls.append({"collection_name": collection_name, "query": query, "limit": limit})
        ranked = sorted(self.hits, key=lambda p: p.score, reverse=True)[:limit]
        return SimpleNamespace(points=ranked)


def _payload(source: str, index: int, text: str, section: str = "Section") -> dict[str, Any]:
    return {
        "company": "healthcore",
        "source_document": source,
        "section": section,
        "language": "en",
        "chunk_index": index,
        "text": text,
    }


def _fake_embed(text: str) -> list[float]:
    return [0.1, 0.2, 0.3]


class FakeLLM:
    """Records chat.completions.create calls and returns a fixed generated answer."""

    def __init__(self, answer: str) -> None:
        self.answer = answer
        self.calls: list[dict[str, Any]] = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        message = SimpleNamespace(content=self.answer)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


CANCELLATION_TEXT = (
    "Cancellation policy:\n- Cancelling more than 24 hours in advance: no charge."
)


# ---------------------------------------------------------------------------
# retrieve()
# ---------------------------------------------------------------------------


def test_retrieve_excludes_hits_below_min_score() -> None:
    client = FakeQdrant(
        hits=[
            _Point(0.82, _payload("appointment-policy", 1, CANCELLATION_TEXT)),
            _Point(0.55, _payload("appointment-policy", 2, "Automated reminders: ...")),
            _Point(0.31, _payload("referral-process", 3, "Outside network ...")),
            _Point(0.12, _payload("insurance-coverage", 0, "United States ...")),
        ]
    )

    results = pipeline.retrieve(
        "cancellation fee?", k=5, min_score=0.5, client=client, embed_fn=_fake_embed
    )

    assert [r["score"] for r in results] == [0.82, 0.55]
    assert all(r["score"] >= 0.5 for r in results)


def test_retrieve_can_return_fewer_than_k_or_zero() -> None:
    client = FakeQdrant(
        hits=[
            _Point(0.61, _payload("new-patient-checklist", 1, "Documents the patient should bring ...")),
            _Point(0.20, _payload("referral-process", 0, "When a primary care physician ...")),
        ]
    )

    some = pipeline.retrieve("what to bring?", k=3, min_score=0.4, client=client, embed_fn=_fake_embed)
    none = pipeline.retrieve("weather in London?", k=3, min_score=0.9, client=client, embed_fn=_fake_embed)

    assert len(some) == 1 < 3
    assert none == []


def test_retrieve_returns_plain_payload_dicts_and_queries_collection() -> None:
    client = FakeQdrant(hits=[_Point(0.7, _payload("appointment-policy", 1, CANCELLATION_TEXT, "Cancellation policy"))])

    results = pipeline.retrieve("cancel?", k=4, min_score=0.4, client=client, embed_fn=_fake_embed)

    assert client.calls == [
        {"collection_name": "healthcore_knowledge", "query": [0.1, 0.2, 0.3], "limit": 4}
    ]
    assert isinstance(results[0], dict)
    assert results[0]["source_document"] == "appointment-policy"
    assert results[0]["section"] == "Cancellation policy"
    assert results[0]["text"] == CANCELLATION_TEXT


def test_retrieve_wraps_vector_store_failure() -> None:
    class BrokenQdrant:
        def query_points(self, **_kwargs: Any) -> Any:
            raise ConnectionError("qdrant down")

    with pytest.raises(pipeline.KnowledgeBaseUnavailable):
        pipeline.retrieve("cancel?", min_score=0.4, client=BrokenQdrant(), embed_fn=_fake_embed)


# ---------------------------------------------------------------------------
# query() / generate_answer()
# ---------------------------------------------------------------------------


def test_query_returns_generated_answer_not_raw_chunk(monkeypatch: pytest.MonkeyPatch) -> None:
    context = [{**_payload("appointment-policy", 1, CANCELLATION_TEXT, "Cancellation policy"), "score": 0.8}]
    generated = (
        "No charge if the patient cancels more than 24 hours ahead.\n"
        "Source: appointment-policy › Cancellation policy"
    )
    llm = FakeLLM(generated)
    retrieve_calls: list[str] = []

    def fake_retrieve(question: str, **_kwargs: Any) -> list[dict[str, Any]]:
        retrieve_calls.append(question)
        return context

    monkeypatch.setattr(pipeline, "retrieve", fake_retrieve)
    monkeypatch.setattr(pipeline, "get_llm_client", lambda: llm)

    answer = pipeline.query("Is there a fee for cancelling 30 hours ahead?")

    assert answer == generated
    assert answer != CANCELLATION_TEXT
    assert CANCELLATION_TEXT not in answer
    assert retrieve_calls == ["Is there a fee for cancelling 30 hours ahead?"]
    assert len(llm.calls) == 1
    user_message = llm.calls[0]["messages"][-1]["content"]
    assert CANCELLATION_TEXT in user_message


def test_query_with_no_context_still_goes_through_model(monkeypatch: pytest.MonkeyPatch) -> None:
    llm = FakeLLM(pipeline.NO_CONTEXT_SENTENCE)
    monkeypatch.setattr(pipeline, "retrieve", lambda question, **_kw: [])
    monkeypatch.setattr(pipeline, "get_llm_client", lambda: llm)

    answer = pipeline.query("What is the parking fee in Manchester?")

    assert answer == pipeline.NO_CONTEXT_SENTENCE
    assert len(llm.calls) == 1
    user_message = llm.calls[0]["messages"][-1]["content"]
    assert "no relevant passages" in user_message


def test_generation_uses_generation_model_not_embedding_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RAG_EMBEDDING_MODEL", "embed-model-a")
    monkeypatch.setenv("RAG_GENERATION_MODEL", "chat-model-b")
    llm = FakeLLM("ok")

    pipeline.generate_answer("q", [], llm_client=llm)

    assert llm.calls[0]["model"] == "chat-model-b"


def test_same_model_for_embed_and_generation_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RAG_EMBEDDING_MODEL", "same-model")
    monkeypatch.setenv("RAG_GENERATION_MODEL", "same-model")

    with pytest.raises(ValueError):
        pipeline.generate_answer("q", [], llm_client=FakeLLM("ok"))


def test_system_prompt_sets_coordinator_voice_and_briefing_rules() -> None:
    messages = pipeline.build_prompt("Do you take Humana?", [])
    system = messages[0]["content"]

    assert "patient coordinator" in system
    assert "best service salesperson" in system
    assert "ONLY" in system
    assert "United States and the United Kingdom" in system
    assert "Tom Callahan" in system
    assert "Medicare or Medicaid" in system
    assert pipeline.NO_CONTEXT_SENTENCE in system


# ---------------------------------------------------------------------------
# setup() / chunking on the real corpus
# ---------------------------------------------------------------------------

BRIEFING_DOCUMENTS = {
    "insurance-coverage",
    "appointment-policy",
    "referral-process",
    "new-patient-checklist",
}


def test_corpus_has_the_four_briefing_documents_with_at_least_three_chunks() -> None:
    chunks = process.build_chunks()
    per_doc: dict[str, int] = {}
    for chunk in chunks:
        per_doc[chunk.source_document] = per_doc.get(chunk.source_document, 0) + 1

    assert set(per_doc) == BRIEFING_DOCUMENTS
    assert all(count >= 3 for count in per_doc.values()), per_doc


def test_chunks_keep_every_source_line_whole() -> None:
    """No bullet, numbered step, or wrapped sentence is cut across chunks."""
    for source, markdown in process.load_documents().items():
        chunk_texts = [c.text for c in process.chunk_document(source, markdown)]
        body_blocks = markdown.strip().split("\n\n")[1:]
        for block in body_blocks:
            for logical_line in process._logical_lines(block):
                owners = [t for t in chunk_texts if logical_line in t]
                assert len(owners) == 1, (source, logical_line)


def test_payload_has_briefing_fields_and_deterministic_ids() -> None:
    chunks = process.build_chunks()
    for chunk in chunks:
        payload = chunk.payload()
        assert set(payload) == {"company", "source_document", "section", "language", "chunk_index", "text"}
        assert payload["company"] == "healthcore"
        assert payload["language"] == "en"
        assert payload["section"]
    assert len({c.point_id() for c in chunks}) == len(chunks)
    assert [c.point_id() for c in process.build_chunks()] == [c.point_id() for c in chunks]


def test_setup_is_idempotent_on_in_memory_qdrant() -> None:
    from qdrant_client import QdrantClient

    client = QdrantClient(":memory:")

    first = process.setup(client=client, embed_fn=lambda text: [float(len(text) % 7 + 1), 1.0, 0.5])
    second = process.setup(client=client, embed_fn=lambda text: [float(len(text) % 7 + 1), 1.0, 0.5])

    assert first == second
    assert client.count("healthcore_knowledge").count == first
