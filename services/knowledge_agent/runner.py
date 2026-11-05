"""Compiles the graph once, then runs, traces, checkpoints, and resumes it."""

from __future__ import annotations

import logging
import os
import sqlite3
import time
import uuid
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from langgraph.checkpoint.sqlite import SqliteSaver

from .graph import GRAPH_NAME, GRAPH_VERSION, GraphSpec, compile_agent_graph
from .nodes import AgentDependencies, rag
from .state import AgentState
from .trace_store import TraceStore

logger = logging.getLogger(__name__)

DEFAULT_STATE_DIR = Path(__file__).resolve().parent / ".state"


@dataclass(frozen=True)
class AgentResult:
    run_id: str
    answer: str
    outcome: str


class AgentRunFailed(RuntimeError):
    """A node raised. Carries only what is safe to surface: run id, node, error type."""

    def __init__(self, run_id: str, node: str | None, cause: BaseException) -> None:
        super().__init__(f"agent run {run_id} failed at node {node!r} ({type(cause).__name__})")
        self.run_id = run_id
        self.node = node
        self.error_type = type(cause).__name__
        self.service_unavailable = isinstance(cause, rag.KnowledgeBaseUnavailable)


def _source_line(answer: str) -> str | None:
    for line in reversed(answer.splitlines()):
        if line.strip().startswith("Source:"):
            return line.strip()
    return None


def summarize_update(node: str, update: AgentState, *, store_text: bool) -> dict[str, Any]:
    """What a node produced, for the trace. Text only when ``store_text``."""
    summary: dict[str, Any] = {"keys": sorted(update)}
    if "question" in update:
        summary["question_chars"] = len(update["question"])
        if store_text:
            summary["question"] = update["question"]
    if "context" in update:
        summary["hits"] = [
            {
                "source_document": chunk["source_document"],
                "chunk_index": chunk["chunk_index"],
                "section": chunk["section"],
                "score": round(chunk["score"], 4),
            }
            for chunk in update["context"]
        ]
    if "answer" in update:
        summary["answer_chars"] = len(update["answer"])
        summary["source_line"] = _source_line(update["answer"])
        if store_text:
            summary["answer"] = update["answer"]
    if "outcome" in update:
        summary["outcome"] = update["outcome"]
    return summary


def _env_flag(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes"}


class AgentRunner:
    def __init__(
        self,
        *,
        deps: AgentDependencies | None = None,
        spec: GraphSpec | None = None,
        state_dir: str | Path | None = None,
        checkpointer: Any | None = None,
        trace_store: TraceStore | None = None,
        store_text: bool | None = None,
        mode: str = "live",
    ) -> None:
        directory = Path(state_dir or os.getenv("AGENT_STATE_DIR") or DEFAULT_STATE_DIR)
        self._checkpoint_conn: sqlite3.Connection | None = None
        if checkpointer is None:
            directory.mkdir(parents=True, exist_ok=True)
            self._checkpoint_conn = sqlite3.connect(
                directory / "checkpoints.sqlite", check_same_thread=False
            )
            checkpointer = SqliteSaver(self._checkpoint_conn)
        self.traces = trace_store or TraceStore(directory / "traces.sqlite")
        self.store_text = _env_flag("AGENT_TRACE_STORE_TEXT") if store_text is None else store_text
        self.mode = mode
        self.graph = compile_agent_graph(spec, deps=deps, checkpointer=checkpointer)

    def close(self) -> None:
        self.traces.close()
        if self._checkpoint_conn is not None:
            self._checkpoint_conn.close()

    @staticmethod
    def _config(run_id: str) -> dict[str, Any]:
        return {
            "configurable": {"thread_id": run_id},
            "run_name": GRAPH_NAME,
            "metadata": {"run_id": run_id, "graph_version": GRAPH_VERSION},
        }

    def run(self, question: str, *, labels: dict[str, Any] | None = None) -> AgentResult:
        run_id = uuid.uuid4().hex
        self.traces.start_run(
            run_id,
            question=question,
            graph_version=GRAPH_VERSION,
            mode=self.mode,
            labels=labels,
            store_text=self.store_text,
        )
        return self._drive(run_id, {"question": question})

    def resume(self, run_id: str) -> AgentResult:
        """Continue a failed run from its last checkpoint; completed nodes do not re-run."""
        self.traces.mark_resumed(run_id)
        return self._drive(run_id, None)

    def checkpoints(self, run_id: str) -> list[dict[str, Any]]:
        """Checkpoint history for a run, oldest first."""
        history = list(self.graph.get_state_history(self._config(run_id)))
        return [
            {
                "checkpoint_id": snapshot.config["configurable"]["checkpoint_id"],
                "step": snapshot.metadata.get("step"),
                "next": list(snapshot.next),
                "state_keys": sorted(snapshot.values),
            }
            for snapshot in reversed(history)
        ]

    def _drive(self, run_id: str, payload: AgentState | None) -> AgentResult:
        config = self._config(run_id)
        last = time.perf_counter()
        try:
            for chunk in self.graph.stream(payload, config, stream_mode="updates"):
                now = time.perf_counter()
                for node, update in chunk.items():
                    self.traces.record_step(
                        run_id,
                        node,
                        status="completed",
                        duration_ms=(now - last) * 1000,
                        output=summarize_update(node, update or {}, store_text=self.store_text),
                    )
                last = now
        except Exception as exc:
            pending = self.graph.get_state(config).next
            failed_node = pending[0] if pending else None
            self.traces.record_step(
                run_id,
                failed_node or "unknown",
                status="failed",
                duration_ms=(time.perf_counter() - last) * 1000,
                output={"error_type": type(exc).__name__},
            )
            self.traces.finish_run(
                run_id, status="failed", failed_node=failed_node, error_type=type(exc).__name__
            )
            logger.error("agent run %s failed at %s (%s)", run_id, failed_node, type(exc).__name__)
            raise AgentRunFailed(run_id, failed_node, exc) from exc

        values = self.graph.get_state(config).values
        answer = values.get("answer", "")
        outcome = values.get("outcome", "")
        self.traces.finish_run(
            run_id,
            status="completed",
            outcome=outcome,
            answer=answer if self.store_text else None,
        )
        return AgentResult(run_id=run_id, answer=answer, outcome=outcome)


@lru_cache
def get_agent_runner() -> AgentRunner:
    """Process-wide runner; compiling here is what makes the API fail fast at startup."""
    return AgentRunner()
