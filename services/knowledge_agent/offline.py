"""Eval-only doubles for recording traces without the 4Geeks gateway or a Qdrant server.

The real ``setup()``, ``retrieve()``, ``build_prompt()``, and ``generate_answer()``
still run. Only their injectable clients change: an in-memory Qdrant, a
deterministic lexical embedding, and an extractive stand-in for the chat model
that can only quote the CONTEXT block it was given. Never used by the API.
"""

from __future__ import annotations

import hashlib
import math
import re
from functools import partial
from types import SimpleNamespace
from typing import Any

from .nodes import AgentDependencies, rag

OFFLINE_DIMENSION = 1024
OFFLINE_MIN_SCORE = 0.25

_STOPWORDS = frozenset(
    "a an and are as at be by can do does for from has have i if in is it its me my of on or our"
    " the their there this to us was we what when where which who will with you your".split()
)
_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _stem(token: str) -> str:
    for suffix in ("ing", "ed", "es", "s"):
        if token.endswith(suffix) and len(token) - len(suffix) >= 3:
            return token[: -len(suffix)]
    return token


def lexical_embed(text: str) -> list[float]:
    """Hashed bag-of-stems, L2-normalised. Deterministic across processes."""
    vector = [0.0] * OFFLINE_DIMENSION
    for token in _TOKEN_RE.findall(text.lower()):
        if token in _STOPWORDS:
            continue
        digest = hashlib.sha256(_stem(token).encode("utf-8")).digest()
        vector[int.from_bytes(digest[:4], "big") % OFFLINE_DIMENSION] += 1.0
    norm = math.sqrt(sum(v * v for v in vector)) or 1.0
    return [v / norm for v in vector]


_BLOCK_RE = re.compile(r"^\[(\d+)\] (?P<doc>[^\n]+?) › (?P<section>[^\n]*)\n", re.MULTILINE)


class ExtractiveLLM:
    """Answers with the top-ranked CONTEXT passage verbatim plus its Source line."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        user = kwargs["messages"][-1]["content"]
        context = user.split("CONTEXT:\n", 1)[1].split("\n\nCOORDINATOR QUESTION:", 1)[0]
        blocks = list(_BLOCK_RE.finditer(context))
        if not blocks:
            content = rag.NO_CONTEXT_SENTENCE
        else:
            first = blocks[0]
            end = blocks[1].start() if len(blocks) > 1 else len(context)
            passage = context[first.end() : end].strip()
            content = f"{passage}\nSource: {first.group('doc')} › {first.group('section')}"
        message = SimpleNamespace(content=content)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def build_offline_dependencies(min_score: float = OFFLINE_MIN_SCORE) -> AgentDependencies:
    from qdrant_client import QdrantClient

    from data.process import rag as process

    client = QdrantClient(":memory:")
    process.setup(client=client, embed_fn=lexical_embed)
    return AgentDependencies(
        retrieve=partial(rag.retrieve, client=client, embed_fn=lexical_embed, min_score=min_score),
        generate_answer=partial(rag.generate_answer, llm_client=ExtractiveLLM()),
    )
