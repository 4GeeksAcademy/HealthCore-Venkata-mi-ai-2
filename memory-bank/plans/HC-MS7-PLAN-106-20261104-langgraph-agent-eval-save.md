---
stamp: HC-MS7-PLAN-106
sequence: 106
milestone: MS7
date: 2026-11-04
title: Save LangGraph Knowledge Agent Rubric Evaluation
status: implemented
phase: docs
summary: >
  Human approved save. Support Agent with LangGraph Part 1 rubric is 11/11 Pass
  for the knowledge agent in PLAN-105. Trace evals 29 passed / 5 skipped against
  an offline-recorded trace; a live re-record is still required before the PR.
  Does not close MS7.
related_paths:
  - memory-bank/evaluations/Results/LangGraphAgent-20261104.md
  - memory-bank/evaluations/INDEX.md
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Append a second 2026-11-04 LangGraphAgent Results file
  - Overwrite earlier Results files
  - Treat this as an MS7 milestone close
  - Rewrite PLAN-104 or PLAN-105
---

# HC-MS7-PLAN-106 — Save LangGraph Knowledge Agent Rubric Evaluation

## Decisions locked

- Canonical eval: [`memory-bank/evaluations/Results/LangGraphAgent-20261104.md`](../evaluations/Results/LangGraphAgent-20261104.md).
- Official rubric score: **11/11 Pass**. Grounding was checked against an offline trace.
- Same-day re-evals overwrite that Results file only.

## Agent instructions

1. The human commits this work. Do not commit on their behalf.
2. Before the PR (label `langgraph-agent-base`), re-record the trace with `--mode live` and re-run the evals. The Humana case must pass, not skip.
3. Part 2 builds on `default_spec()` in `services/knowledge_agent/graph.py`. Do not close MS7 from this stamp.
