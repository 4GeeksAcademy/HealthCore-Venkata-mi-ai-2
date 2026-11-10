"""Compiles the graph once, then runs, traces, checkpoints, and resumes it."""

from __future__ import annotations

import logging
import os
import sqlite3
import time
import uuid
from dataclasses import dataclass, replace
from functools import lru_cache
from pathlib import Path
from typing import Any

from langgraph.checkpoint.sqlite import SqliteSaver

from .graph import GRAPH_NAME, GRAPH_VERSION, GraphSpec, compile_agent_graph
from .memory.store import MemoryStore
from .memory.turn import (
    UNAVAILABLE,
    MemoryCoordinator,
    MemoryUnavailable,
    TurnEnding,
    TurnPrelude,
    join_parts,
    normalize_actor,
    normalize_conversation_id,
)
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
    sources: tuple[str, ...] = ()
    conversation_id: str = ""
    memory_event: str = "none"


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
    if "plan" in update:
        plan = update["plan"]
        summary["sources"] = list(plan["sources"])
        summary["planner"] = plan["planner"]
        if plan.get("ticket_input") is not None:
            summary["ticket_input"] = plan["ticket_input"]
        if plan.get("inventory_input") is not None and store_text:
            summary["inventory_input"] = plan["inventory_input"]
        if plan.get("knowledge_question"):
            summary["knowledge_question_chars"] = len(plan["knowledge_question"])
            if store_text:
                summary["knowledge_question"] = plan["knowledge_question"]
    if update.get("tool_results"):
        summary["tool_call"] = _summarize_tool_call(update["tool_results"][-1], store_text=store_text)
    if update.get("fallbacks"):
        note = update["fallbacks"][-1]
        summary["fallback"] = {"tool": note["tool"], "reason": note["reason"]}
    return summary


def _summarize_tool_call(result: dict[str, Any], *, store_text: bool) -> dict[str, Any]:
    """Which service was called, how, and what came back — ids and figures, never patient data."""
    output = result["output"]
    call: dict[str, Any] = {
        "tool": result["tool"],
        "status": result["status"],
        "method": "GET" if output.get("endpoint") else None,
        "endpoint": output.get("endpoint"),
        "http_status": output.get("http_status"),
        "latency_ms": output.get("latency_ms"),
    }
    if result["tool"] == "ticket_lookup":
        call["input"] = result["input"]
        call["total"] = output.get("total", 0)
        call["tickets"] = [
            {"incident_id": t["incident_id"], "status": t["status"], "category": t["category"]}
            for t in output.get("tickets", [])
        ]
    else:
        if store_text:
            call["input"] = result["input"]
        call["products"] = [
            {"sku": p["sku"], "current_stock": p["current_stock"], "threshold": p["threshold"]}
            for p in output.get("products", [])
        ]
    return call


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
        memory: MemoryCoordinator | None = None,
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
        self.memory = memory if memory is not None else MemoryCoordinator(
            MemoryStore(directory / "agent_memory.sqlite")
        )
        self.store_text = _env_flag("AGENT_TRACE_STORE_TEXT") if store_text is None else store_text
        self.mode = mode
        self.graph = compile_agent_graph(spec, deps=deps, checkpointer=checkpointer)

    def close(self) -> None:
        self.memory.close()
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

    def run(
        self,
        question: str,
        *,
        labels: dict[str, Any] | None = None,
        conversation_id: str | None = None,
        actor_id: str = "staff:unknown",
    ) -> AgentResult:
        """Answer one desk turn. Memory is decided here; the graph is unchanged."""
        conversation_id = normalize_conversation_id(conversation_id)
        actor_id = normalize_actor(actor_id)
        try:
            prelude = self.memory.prepare(conversation_id, question, actor_id)
        except MemoryUnavailable:
            logger.error("agent memory unavailable (%s)", "sqlite3.Error")
            prelude = TurnPrelude(
                conversation_id=conversation_id,
                memory_event="none",
                graph_question=question,
                locked_suffix=UNAVAILABLE,
                block_proposal=True,
                trace_question=question,
            )
        if prelude.final_answer is not None:
            return self._memory_only(prelude, labels)

        result = self._run_graph(prelude.graph_question or question, labels)
        if result.outcome == "invalid_question":
            return replace(result, conversation_id=conversation_id, memory_event="none")
        try:
            ending = self.memory.finish(
                conversation_id,
                prelude.graph_question or question,
                actor_id,
                block_proposal=prelude.block_proposal,
                locked_suffix=prelude.locked_suffix,
            )
        except MemoryUnavailable:
            logger.error("agent memory unavailable (%s)", "sqlite3.Error")
            ending = TurnEnding(suffix=UNAVAILABLE, memory_event="none")
        if ending.memory_event == "proposed":
            event = "proposed"
        elif prelude.memory_event != "none":
            event = prelude.memory_event
        else:
            event = ending.memory_event
        return replace(
            result,
            answer=join_parts(prelude.lead, result.answer, ending.suffix),
            conversation_id=conversation_id,
            memory_event=event,
        )

    def _memory_only(self, prelude: TurnPrelude, labels: dict[str, Any] | None) -> AgentResult:
        run_id = uuid.uuid4().hex
        traced = prelude.trace_question or "[decision]"
        self.traces.start_run(
            run_id,
            question=traced,
            graph_version=GRAPH_VERSION,
            mode=self.mode,
            labels=labels,
            store_text=self.store_text and traced != "[redacted]",
        )
        self.traces.record_step(
            run_id,
            "memory_decision",
            status="completed",
            duration_ms=0,
            output={"memory_event": prelude.memory_event},
        )
        answer = prelude.final_answer or ""
        self.traces.finish_run(
            run_id,
            status="completed",
            outcome="answered",
            answer=answer if self.store_text and traced != "[redacted]" else None,
        )
        return AgentResult(
            run_id=run_id,
            answer=answer,
            outcome="answered",
            conversation_id=prelude.conversation_id,
            memory_event=prelude.memory_event,
        )

    def _run_graph(self, question: str, labels: dict[str, Any] | None) -> AgentResult:
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
        return AgentResult(
            run_id=run_id,
            answer=answer,
            outcome=outcome,
            sources=tuple(self.traces.source_sequence(run_id)),
        )


@lru_cache
def get_agent_runner() -> AgentRunner:
    """Process-wide runner; compiling here is what makes the API fail fast at startup."""
    return AgentRunner()
