"""Record one traced run of the coordinator knowledge agent per eval case.

Usage (from repo root):

    uv run python scripts/record_agent_traces.py                 # live if OPENAI_API_KEY is set, else offline
    uv run python scripts/record_agent_traces.py --mode live     # real 4Geeks models + Qdrant (.env)
    uv run python scripts/record_agent_traces.py --mode live --setup   # re-index first
    uv run python scripts/record_agent_traces.py --mode offline  # real corpus/setup/retrieve/generate_answer,
                                                                 # in-memory Qdrant, lexical embedding, extractive LLM

Writes the queryable SQLite trace to ``services/knowledge_agent/.state/eval/`` and the
export the evals read to ``tests/pipelines/fixtures/agent_traces.json``.
Exit code 1 if any run failed.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from datetime import UTC, datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from data.pipelines.rag import default_min_score  # noqa: E402
from data.process.rag import embedding_model, generation_model  # noqa: E402
from services.knowledge_agent import GRAPH_VERSION, AgentRunFailed, AgentRunner  # noqa: E402
from services.knowledge_agent.offline import (  # noqa: E402
    OFFLINE_MIN_SCORE,
    build_offline_dependencies,
)

CASES_PATH = REPO_ROOT / "tests" / "pipelines" / "agent_eval_cases.json"
EXPORT_PATH = REPO_ROOT / "tests" / "pipelines" / "fixtures" / "agent_traces.json"
STATE_DIR = REPO_ROOT / "services" / "knowledge_agent" / ".state" / "eval"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--mode", choices=["auto", "live", "offline"], default="auto")
    parser.add_argument("--setup", action="store_true", help="live only: re-index the knowledge base first")
    args = parser.parse_args()

    mode = args.mode
    if mode == "auto":
        mode = "live" if os.getenv("OPENAI_API_KEY") else "offline"

    if mode == "live":
        deps = None
        models = {"embedding": embedding_model(), "generation": generation_model()}
        min_score = default_min_score()
        if args.setup:
            from data.process.rag import setup

            print(f"Indexed {setup()} chunks")
    else:
        deps = build_offline_dependencies()
        models = {"embedding": "offline lexical-hash-1024", "generation": "offline extractive stand-in"}
        min_score = OFFLINE_MIN_SCORE

    shutil.rmtree(STATE_DIR, ignore_errors=True)
    runner = AgentRunner(deps=deps, state_dir=STATE_DIR, store_text=True, mode=mode)
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))["cases"]

    failures = 0
    run_ids: list[str] = []
    print(f"mode={mode} graph={GRAPH_VERSION} min_score={min_score}")
    for case in cases:
        try:
            result = runner.run(case["question"], labels={"case_id": case["id"]})
            run_ids.append(result.run_id)
            path = " -> ".join(runner.traces.node_sequence(result.run_id))
            print(f"  {case['id']:<32} {result.outcome:<17} {path}")
        except AgentRunFailed as exc:
            failures += 1
            run_ids.append(exc.run_id)
            print(f"  {case['id']:<32} FAILED at {exc.node} ({exc.error_type})")

    export = {
        "recorded_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "mode": mode,
        "graph_version": GRAPH_VERSION,
        "models": models,
        "min_score": min_score,
        "graph_mermaid": runner.graph.get_graph().draw_mermaid(),
        "runs": runner.traces.export(run_ids),
    }
    EXPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    EXPORT_PATH.write_text(json.dumps(export, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    runner.close()
    if mode == "live":
        from data.process.rag import get_qdrant_client

        get_qdrant_client().close()
    print(f"Trace store: {STATE_DIR.relative_to(REPO_ROOT) / 'traces.sqlite'}")
    print(f"Export:      {EXPORT_PATH.relative_to(REPO_ROOT)} ({len(run_ids)} runs)")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
