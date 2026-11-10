# Agent Memory and Self-Improvement (Part 1) — Evaluation

**Date:** 2026-11-09  
**Rubric:** Agent Memory Part 1 — "What We Will Evaluate" (11 checks)  
**Implementation as of:** [HC-MS8-PLAN-117](../../plans/HC-MS8-PLAN-117-20261109-agent-memory.md)  
**Plan:** [HC-MS8-PLAN-116](../../plans/HC-MS8-PLAN-116-20261109-agent-memory-plan.md)  
**Overall: 11/11 Pass.** This file does not close MS8. Part 2 (the harness) is still out of scope.

| Doc | Path |
|-----|------|
| Challenge | [`docs/Project_Contexts/AgentMemoryPart1.md`](../../../docs/Project_Contexts/AgentMemoryPart1.md) |
| Company briefing | [`docs/Project_Contexts/healthcore-memory-BRIEFING.md`](../../../docs/Project_Contexts/healthcore-memory-BRIEFING.md) |
| Design | [`docs/agent/agent-memory.md`](../../../docs/agent/agent-memory.md) |
| Store and turn | [`services/knowledge_agent/memory/`](../../../services/knowledge_agent/memory/) |
| Runner | [`services/knowledge_agent/runner.py`](../../../services/knowledge_agent/runner.py) |
| API | [`services/api/app/routers/agent.py`](../../../services/api/app/routers/agent.py) |
| Evidence tests | [`tests/pipelines/test_agent_memory.py`](../../../tests/pipelines/test_agent_memory.py) |

Saved after human approval on 2026-11-09. Same-day re-evals overwrite this file only. Does not replace [MCPServer-20261106](./MCPServer-20261106.md).

## Method

- The same coordinator graph answers the desk question. `GRAPH_VERSION` stays `knowledge-agent/2`. Memory is a turn around that graph: read, classify a pending decision, then maybe propose one fact.
- The store is SQLite `agent_memory.sqlite` under the gitignored agent state directory. `read_matching` is the read. `commit_approved` is the only fact write, and it runs after a classified approve or edit that passes the PHI gate again.
- `python -m pytest tests/pipelines/test_agent_memory.py tests/pipelines/test_agent_graph.py tests/pipelines/test_agent_tools.py`: **79 passed**.
- `python -m pytest services/api/tests/test_agent.py tests/pipelines/test_agent_evals.py`: **111 passed, 10 skipped**. The skips are the existing live-trace cases. This run did not re-record traces.
- No browser pass. The desk has no chat page. `POST /agent/query` is the conversation.
- `.env` was not part of the evidence.

## Rubric

| # | Criterion | Result | Evidence |
|---|-----------|--------|----------|
| 1 | The memory architecture is justified and matches what the agent needs to remember | Pass | Episodic key-value for clinic protocols, incident patterns with no patient data, staff presentation preferences, and country admin exceptions. Vector search, a knowledge graph, fine-tuning, and the Celery Redis broker are ruled out in `docs/agent/agent-memory.md`. |
| 2 | Memory writes never target company `*_knowledge` collections | Pass | The memory package does not name `healthcore_knowledge`, Qdrant, or Redis. `test_memory_package_does_not_touch_the_knowledge_collection`. |
| 3 | Explicit read/write interface, not a growing system prompt | Pass | `MemoryStore.read_matching` and `MemoryStore.commit_approved`. Approved facts are appended to a later answer only when they match the question. |
| 4 | Memorable turns are distinguished from non-memorable ones, with at least 3 examples of each | Pass | Memorable: Manchester referral protocol, Austin road-closure no-show alert, Diane Foster's vacancy-by-role preference. Not memorable: "What's this week's no-show rate?", the Patient Johnson note (PHI refusal), "Thanks, that settles my report." `test_criterion_examples_match_the_briefing` and `test_three_non_memorable_turns_do_not_propose`. |
| 5 | The proposal is asked in the same conversation | Pass | The answer ends with "Want me to remember this for next time?" plus the sentence. Nothing is written at that step. |
| 6 | No write without a classified approve or edit | Pass | `classify_decision` returns `approve`, `reject`, `edit`, or `ambiguous` with a confidence score. The threshold is 0.75. "yesterday" contains the letters yes and is ambiguous. `test_yesterday_is_not_an_approval`. |
| 7 | One pending proposal; silence and ambiguity reject | Pass | `conversation_id` is the primary key. A second insert raises `PendingExists`. A topic change logs `ambiguous_rejected`. A pending row older than 24 hours logs `expired` / `rejected` on the next turn. |
| 8 | Every proposal and its outcome are audited | Pass | `memory_audit` records the proposal and the later outcome (`approved`, `rejected`, `edited`, `ambiguous_rejected`, `expired`, `phi_blocked`, `policy_blocked`). PHI rows store a hash and rule ids, not the identifier. |
| 9 | Consolidation is documented and functional | Pass | TTLs are 90, 90, 180, and 365 days by kind. Consolidation drops expired rows, exact duplicates, and PHI, redacts the stored PHI text, and caps active facts at 40. `test_consolidation_expires_dedupes_caps_and_rechecks_phi`. |
| 10 | Two complete evidence cycles | Pass | Approved: Manchester referral is proposed, "Yes, remember that." stores it as `staff:7`, and a later Manchester referral question includes the sentence. Rejected: the Diane Foster preference is proposed, "No, don't remember that." leaves the fact table empty, and a later question does not contain it. |
| 11 | Design decisions cover the briefing, especially what must never be remembered | Pass | `memory/phi.py` rejects a patient name, MRN, date of birth, SSN, insurance or member number, NHS number, diagnosis, and visit content before the proposal is shown, again before commit, and again during consolidation. One gate covers HIPAA identifiers and UK GDPR special-category health data. "Patient Johnson…" is an explicit refusal. The name is absent from the answer and the audit, and the knowledge base is not queried. |

## Design decisions recorded with this save

- **Kind of memory.** Episodic records with an author, a timestamp, and an expiry. Cosine similarity, a dependency graph, and fine-tuning do not fit a short list of auditable desk facts.
- **Never remembered.** Patient identifiers and clinical content. A US clinic and a UK clinic use the same gate.
- **Forgetting.** Kind TTLs, exact-text dedupe, a cap of 40, and a second PHI check. An unanswered proposal is not a fact. The next turn after 24 hours logs it as rejected.
- **Poisoning.** A write requires a classified approve or edit. The edit is gated again. A note that Medicare or Medicaid patients pay a no-show fee, or that Humana is accepted, is refused. Stored notes are labeled as desk memory, not published policy. The actor is `staff:{id}` from the JWT.
- **One agent.** Self-evaluation is a `MemoryAssessment` on the same turn as the graph answer. The decision is a `Decision`. The graph nodes and `GRAPH_VERSION` are unchanged.

## Noted limits (accepted in this save)

1. An unanswered proposal becomes a logged rejection when a later turn opens after 24 hours. There is no separate clock process. Until that turn, the row is pending and is not read as memory.
2. The fact text is the user's sentence. A model paraphrase is not used, so a rewrite cannot introduce a patient detail.
3. Dedup is exact text, not a semantic merge of two wordings of the same protocol.
4. This run did not re-record the LangGraph trace fixture. Recorded evals still match `knowledge-agent/2`.

## Agent instructions

1. Canonical eval: this file. Official rubric score: **11/11 Pass**.
2. Same-day re-evals overwrite this file only. Do not append a second `AgentMemory-20261109` file.
3. Do not treat this as an MS8 milestone close. Part 2 is still out of scope.
4. Do not rewrite PLAN-116 or PLAN-117.
5. The human commits. Do not commit on their behalf. Do not commit `.env`.
