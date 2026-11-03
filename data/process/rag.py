"""HealthCore coordinator knowledge base — data preparation and indexing.

Responsibilities in this module (each in its own function):

- ``load_documents`` / ``chunk_document``: read and split the policy corpus in
  ``docs/company-knowledge-base/`` into self-contained semantic chunks.
- ``embed``: one text -> one vector, using the dedicated embeddings model.
- ``setup``: recreate the ``healthcore_knowledge`` Qdrant collection and upsert
  every chunk with its source metadata.

Retrieval and generation live in ``data/pipelines/rag.py``.

CLI: ``uv run python -m data.process.rag``
"""

from __future__ import annotations

import logging
import os
import re
import uuid
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE_DIR = REPO_ROOT / "docs" / "company-knowledge-base"
LOCAL_QDRANT_PATH = REPO_ROOT / "data" / "process" / ".qdrant"

COMPANY = "healthcore"
COLLECTION_NAME = "healthcore_knowledge"
LANGUAGE = "en"
EMBEDDING_DIMENSION = 1024

# 4Geeks student gateway model ids (the team allowlist rejects other ids with 403).
DEFAULT_EMBEDDING_MODEL = "downtown-miami/openrouter/perplexity/pplx-embed-v1-0.6b"
DEFAULT_GENERATION_MODEL = "downtown-miami/openrouter/openai/gpt-6-luna"

# uuid5 namespace for deterministic point ids: same document + chunk_index -> same id.
_POINT_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, "https://healthcore.example/knowledge")

_FILENAME_RE = re.compile(r"^healthcore-(?P<slug>[a-z0-9-]+)\.(?P<lang>[a-z]{2})\.md$")
_LIST_ITEM_RE = re.compile(r"^(?:-|\*|\d+\.)\s+")
_LABEL_SENTENCE_RE = re.compile(r"^(?P<label>[A-Z][A-Za-z0-9 ()/'-]{2,48}):\s+\S")

load_dotenv(REPO_ROOT / ".env", override=False)


@dataclass(frozen=True)
class KnowledgeChunk:
    source_document: str
    title: str
    section: str
    chunk_index: int
    text: str

    def payload(self) -> dict[str, Any]:
        return {
            "company": COMPANY,
            "source_document": self.source_document,
            "section": self.section,
            "language": LANGUAGE,
            "chunk_index": self.chunk_index,
            "text": self.text,
        }

    def embedding_text(self) -> str:
        """Topic header + body; short policy chunks lose their subject without it."""
        if self.section == self.title:
            return f"{self.title}\n{self.text}"
        return f"{self.title} — {self.section}\n{self.text}"

    def point_id(self) -> str:
        return str(uuid.uuid5(_POINT_NAMESPACE, f"{self.source_document}:{self.chunk_index}"))


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


def embedding_model() -> str:
    return os.getenv("RAG_EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL).strip()


def generation_model() -> str:
    return os.getenv("RAG_GENERATION_MODEL", DEFAULT_GENERATION_MODEL).strip()


def assert_distinct_models() -> None:
    if embedding_model() == generation_model():
        raise ValueError("RAG_EMBEDDING_MODEL and RAG_GENERATION_MODEL must be different models")


@lru_cache
def get_llm_client() -> Any:
    """OpenAI-compatible client for the 4Geeks gateway (key and base URL from .env)."""
    from openai import OpenAI

    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set; add the 4Geeks key to the local .env")
    base_url = os.getenv("OPENAI_BASE_URL") or None
    return OpenAI(base_url=base_url)


@lru_cache
def get_qdrant_client() -> Any:
    """Qdrant server when QDRANT_URL is set; embedded local storage otherwise."""
    from qdrant_client import QdrantClient

    url = os.getenv("QDRANT_URL", "").strip()
    if url:
        return QdrantClient(url=url, api_key=os.getenv("QDRANT_API_KEY") or None)
    LOCAL_QDRANT_PATH.mkdir(parents=True, exist_ok=True)
    return QdrantClient(path=str(LOCAL_QDRANT_PATH))


# ---------------------------------------------------------------------------
# Parsing and chunking
# ---------------------------------------------------------------------------


def source_slug(path: Path) -> str:
    """``healthcore-insurance-coverage.en.md`` -> ``insurance-coverage``."""
    match = _FILENAME_RE.match(path.name)
    if not match:
        raise ValueError(f"Unexpected knowledge base filename: {path.name}")
    return match.group("slug")


def load_documents(knowledge_dir: Path = KNOWLEDGE_DIR) -> dict[str, str]:
    """Return ``{source_document: markdown}`` for every ``*.{LANGUAGE}.md`` in the folder."""
    paths = sorted(knowledge_dir.glob(f"healthcore-*.{LANGUAGE}.md"))
    if not paths:
        raise FileNotFoundError(f"No .{LANGUAGE}.md documents in {knowledge_dir}")
    return {source_slug(path): path.read_text(encoding="utf-8") for path in paths}


def _logical_lines(block: str) -> list[str]:
    """Unwrap soft line breaks. A new logical line starts only at a list marker."""
    lines: list[str] = []
    for raw in block.splitlines():
        line = raw.strip()
        if not line:
            continue
        if not lines or _LIST_ITEM_RE.match(line):
            lines.append(line)
        else:
            lines[-1] = f"{lines[-1]} {line}"
    return lines


def _is_list_item(line: str) -> bool:
    return bool(_LIST_ITEM_RE.match(line))


def chunk_document(source_document: str, markdown: str) -> list[KnowledgeChunk]:
    """Split one policy document into semantic chunks.

    Rules (never a character count):
    - The ``# `` heading is the document title, not a chunk.
    - A block whose first line ends in ``:`` followed by list items is one chunk;
      the first line (without ``:``) is the section.
    - A single-line lead-in ending in ``:`` merges into the next block.
    - A ``Label: sentence`` paragraph uses the label as section.
    - Any other paragraph is its own chunk; section = document title.
    List items and wrapped sentences are never split across chunks.
    """
    blocks = [b for b in re.split(r"\n\s*\n", markdown.strip()) if b.strip()]
    title = source_document
    if blocks and blocks[0].lstrip().startswith("# "):
        title = blocks.pop(0).strip().lstrip("#").strip()

    units: list[tuple[str, list[str]]] = []
    pending_lead_in: list[str] = []
    for block in blocks:
        lines = _logical_lines(block)
        if not lines:
            continue
        if len(lines) == 1 and lines[0].endswith(":"):
            pending_lead_in.extend(lines)
            continue

        first = lines[0]
        rest = lines[1:]
        if first.endswith(":") and rest and all(_is_list_item(item) for item in rest):
            section = first[:-1].strip()
        elif not _is_list_item(first) and (label := _LABEL_SENTENCE_RE.match(first)):
            section = label.group("label").strip()
        else:
            section = title

        units.append((section, pending_lead_in + lines))
        pending_lead_in = []

    if pending_lead_in:
        units.append((title, pending_lead_in))

    return [
        KnowledgeChunk(
            source_document=source_document,
            title=title,
            section=section,
            chunk_index=index,
            text="\n".join(lines),
        )
        for index, (section, lines) in enumerate(units)
    ]


def build_chunks(knowledge_dir: Path = KNOWLEDGE_DIR) -> list[KnowledgeChunk]:
    chunks: list[KnowledgeChunk] = []
    for source_document, markdown in load_documents(knowledge_dir).items():
        chunks.extend(chunk_document(source_document, markdown))
    return chunks


# ---------------------------------------------------------------------------
# Embedding
# ---------------------------------------------------------------------------


def embed(text: str) -> list[float]:
    """Vector for one text via the dedicated embeddings model (never the chat model).

    Used for chunks at index time and for the coordinator's question at query time.
    """
    assert_distinct_models()
    cleaned = " ".join(text.split())
    if not cleaned:
        raise ValueError("Cannot embed empty text")
    response = get_llm_client().embeddings.create(model=embedding_model(), input=cleaned)
    return list(response.data[0].embedding)


# ---------------------------------------------------------------------------
# Indexing
# ---------------------------------------------------------------------------


def setup(
    knowledge_dir: Path = KNOWLEDGE_DIR,
    *,
    client: Any | None = None,
    embed_fn: Callable[[str], list[float]] = embed,
) -> int:
    """Chunk the corpus and (re)load it into ``healthcore_knowledge``.

    Idempotent by clear-and-reload: the collection is dropped and recreated on every
    run, and point ids are deterministic, so re-running never duplicates points.
    Returns the number of chunks indexed.
    """
    from qdrant_client import models

    chunks = build_chunks(knowledge_dir)
    vectors = [embed_fn(chunk.embedding_text()) for chunk in chunks]
    dimension = len(vectors[0]) if vectors else EMBEDDING_DIMENSION

    qdrant = client or get_qdrant_client()
    if qdrant.collection_exists(COLLECTION_NAME):
        qdrant.delete_collection(COLLECTION_NAME)
    qdrant.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=models.VectorParams(size=dimension, distance=models.Distance.COSINE),
    )
    qdrant.upsert(
        collection_name=COLLECTION_NAME,
        points=[
            models.PointStruct(id=chunk.point_id(), vector=vector, payload=chunk.payload())
            for chunk, vector in zip(chunks, vectors, strict=True)
        ],
        wait=True,
    )
    logger.info("Indexed %d chunks into %s", len(chunks), COLLECTION_NAME)
    return len(chunks)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    try:
        count = setup()
    except Exception as exc:  # noqa: BLE001 - CLI boundary: report and exit non-zero
        logger.error("Knowledge base setup failed (%s): %s", type(exc).__name__, exc)
        return 1
    finally:
        get_qdrant_client().close()
    per_document: dict[str, int] = {}
    for chunk in build_chunks():
        per_document[chunk.source_document] = per_document.get(chunk.source_document, 0) + 1
    print(f"Collection {COLLECTION_NAME}: {count} chunks")
    for source_document, n in sorted(per_document.items()):
        print(f"  {source_document}: {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
