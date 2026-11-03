"""Recall@3 eval for the HealthCore coordinator knowledge base.

Usage (from repo root):

    uv run python scripts/eval_rag_recall.py            # eval the current index
    uv run python scripts/eval_rag_recall.py --setup    # re-index first
    uv run python scripts/eval_rag_recall.py --answers  # also generate sample answers

Writes ``data/eval/rag_recall_report.md``. Needs the 4Geeks key in the local ``.env``.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from data.pipelines.rag import (  # noqa: E402
    default_min_score,
    query,
    retrieve,
)
from data.process.rag import (  # noqa: E402
    COLLECTION_NAME,
    embedding_model,
    generation_model,
    get_qdrant_client,
    setup,
)

QUERIES_PATH = REPO_ROOT / "data" / "eval" / "test-queries.json"
REPORT_PATH = REPO_ROOT / "data" / "eval" / "rag_recall_report.md"
K = 3

SAMPLE_ANSWER_QUESTIONS = [
    "Is there a charge for cancelling 12 hours in advance?",
    "What do I need to bring to my first appointment?",
    "Do you accept Humana?",
    "A Medicaid patient missed their appointment without calling. Do we charge the no-show fee?",
    "What is the Wi-Fi password for the staff network?",
]


def _key(item: dict[str, Any]) -> str:
    return f"{item['source_document']}#{item['chunk_index']}"


def evaluate(min_score: float) -> dict[str, Any]:
    spec = json.loads(QUERIES_PATH.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    for item in spec["queries"]:
        hits = retrieve(item["question"], k=K, min_score=0.0)
        expected = _key(item)
        ranked = [_key(h) for h in hits]
        rank = ranked.index(expected) + 1 if expected in ranked else None
        expected_score = hits[rank - 1]["score"] if rank else None
        rows.append(
            {
                "id": item["id"],
                "expected": expected,
                "rank": rank,
                "expected_score": expected_score,
                "top": [(k, h["score"]) for k, h in zip(ranked, hits)],
                "hit_raw": rank is not None,
                "hit_thresholded": rank is not None and expected_score >= min_score,
            }
        )
    negatives = []
    for item in spec.get("negatives", []):
        hits = retrieve(item["question"], k=1, min_score=0.0)
        top = hits[0] if hits else None
        negatives.append(
            {
                "id": item["id"],
                "top": _key(top) if top else "-",
                "score": top["score"] if top else 0.0,
                "passes_threshold": bool(top and top["score"] >= min_score),
            }
        )
    total = len(rows)
    return {
        "rows": rows,
        "negatives": negatives,
        "total": total,
        "recall_raw": sum(r["hit_raw"] for r in rows) / total,
        "recall_thresholded": sum(r["hit_thresholded"] for r in rows) / total,
        "target": spec.get("target_recall_at_3", 0.8),
        "min_expected_score": min(
            (r["expected_score"] for r in rows if r["expected_score"] is not None), default=0.0
        ),
        "max_negative_score": max((n["score"] for n in negatives), default=0.0),
    }


def render(result: dict[str, Any], min_score: float, chunk_count: int | None, answers: list[tuple[str, str]]) -> str:
    lines = [
        "# HealthCore Knowledge Base — Recall@3 Report",
        "",
        f"- Date: {date.today().isoformat()}",
        f"- Collection: `{COLLECTION_NAME}`" + (f" ({chunk_count} chunks after setup)" if chunk_count else ""),
        f"- Embeddings model: `{embedding_model()}` · Generation model: `{generation_model()}`",
        f"- `min_score` (cosine): **{min_score:.2f}**",
        f"- Questions: {result['total']} (from `data/eval/test-queries.json`)",
        "",
        "| Metric | Value | Target |",
        "|--------|-------|--------|",
        f"| Recall@3 (ranking only) | **{result['recall_raw']:.0%}** | ≥ {result['target']:.0%} |",
        f"| Recall@3 with `min_score` applied | **{result['recall_thresholded']:.0%}** | ≥ {result['target']:.0%} |",
        f"| Lowest score of a correct chunk | {result['min_expected_score']:.3f} | > `min_score` |",
        f"| Highest top-1 score of an off-topic question | {result['max_negative_score']:.3f} | < `min_score` |",
        "",
        "## Per question",
        "",
        "| ID | Expected chunk | Rank | Score | Top 3 retrieved |",
        "|----|----------------|------|-------|-----------------|",
    ]
    for row in result["rows"]:
        top = "<br>".join(f"{k} ({s:.3f})" for k, s in row["top"])
        score = f"{row['expected_score']:.3f}" if row["expected_score"] is not None else "—"
        lines.append(f"| {row['id']} | {row['expected']} | {row['rank'] or 'miss'} | {score} | {top} |")
    lines += [
        "",
        "## Off-topic questions (threshold check)",
        "",
        "| ID | Top-1 chunk | Score | Clears `min_score`? |",
        "|----|-------------|-------|---------------------|",
    ]
    for neg in result["negatives"]:
        lines.append(f"| {neg['id']} | {neg['top']} | {neg['score']:.3f} | {'yes' if neg['passes_threshold'] else 'no'} |")
    if answers:
        lines += ["", "## Sample generated answers (`query()`)", ""]
        for question, answer in answers:
            lines += [f"**Q:** {question}", "", "> " + answer.replace("\n", "\n> "), ""]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--setup", action="store_true", help="re-index the corpus before evaluating")
    parser.add_argument("--answers", action="store_true", help="also generate sample answers via query()")
    parser.add_argument("--min-score", type=float, default=None)
    args = parser.parse_args()

    min_score = default_min_score() if args.min_score is None else args.min_score
    try:
        chunk_count = setup() if args.setup else None
        result = evaluate(min_score)
        answers = [(q, query(q)) for q in SAMPLE_ANSWER_QUESTIONS] if args.answers else []
    except Exception as exc:  # noqa: BLE001 - CLI boundary: report and exit non-zero
        print(f"RAG eval failed ({type(exc).__name__}): {exc}", file=sys.stderr)
        return 1
    finally:
        get_qdrant_client().close()

    REPORT_PATH.write_text(render(result, min_score, chunk_count, answers), encoding="utf-8")
    print(f"Recall@3 ranking only: {result['recall_raw']:.0%}")
    print(f"Recall@3 with min_score={min_score:.2f}: {result['recall_thresholded']:.0%}")
    print(f"Lowest correct-chunk score: {result['min_expected_score']:.3f}")
    print(f"Highest off-topic top-1 score: {result['max_negative_score']:.3f}")
    print(f"Report: {REPORT_PATH.relative_to(REPO_ROOT)}")
    passed = result["recall_thresholded"] >= result["target"]
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
