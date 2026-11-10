# Agent memory — design

The coordinator agent is unchanged as a graph (`GRAPH_VERSION` stays `knowledge-agent/2`). Desk memory is a turn around that graph: read approved facts, classify a pending decision, and maybe propose one new fact. The same `AgentRunner.run` returns the answer the coordinator sees. There is no second agent and no write into `healthcore_knowledge`.

Plan: [HC-MS8-PLAN-116](../../memory-bank/plans/HC-MS8-PLAN-116-20261109-agent-memory-plan.md). Company rules: [healthcore-memory-BRIEFING.md](../Project_Contexts/healthcore-memory-BRIEFING.md).

## What kind of memory, and what was ruled out

HealthCore's memorable items are a short list of operational records: a clinic protocol, an incident pattern with no patient in it, a staff preference for how a report is laid out, or a country admin exception. Each one needs an author, a timestamp, and an expiry. That is episodic key-value memory.

The store is SQLite, file `agent_memory.sqlite` in the gitignored agent state directory. `MemoryStore.read_matching` is the read. `MemoryStore.commit_approved` is the only write of a fact, and it runs after a classified approve or edit.

Ruled out:

- **The company RAG collection.** `healthcore_knowledge` stays a read-only tool. Mixing approved desk notes into curated policy chunks would break retrieval evals and the poison controls.
- **A vector collection.** A handful of exact facts does not need cosine similarity, and a second Qdrant collection is easy to confuse with the knowledge base.
- **A knowledge graph.** These facts are not a chain of dependencies the agent has to traverse.
- **Fine-tuning.** It cannot drop one fact, and it cannot show who approved it.
- **Redis.** Redis in this repo is the Celery broker (`redis://redis:6379/0`, `noeviction`). Desk memory does not share that keyspace.

## What must never be remembered

The gate in `memory/phi.py` runs before a proposal is shown, again before a commit, and again during consolidation. A hit is an explicit refusal, not a silent skip. The matched characters are not stored. The audit keeps a hash, a length, and rule ids.

The same rules cover both regimes:

- **HIPAA:** patient name, medical record number, date of birth, Social Security number, insurance or member number, diagnosis, and visit content (notes, labs, prescriptions).
- **UK GDPR:** the same health data is special-category data (Article 9), and an NHS number plus any of those identifiers can re-identify a person. One gate, both countries. A US clinic and a UK clinic do not get different exceptions.

A normal policy question such as "Do Medicare patients pay a no-show fee?" is not a memory write. The gate does not hijack that answer.

## What is worth remembering

The criterion is a kind match, not "always". A turn proposes only when the message is a durable operational fact of one of the four kinds, it is not already stored, and both gates pass. The fact text is the user's sentence, not a model paraphrase.

| Memorable | Kind |
|-----------|------|
| Manchester referrals now go through the coordinator before the specialist. | `clinic_protocol` (90 days) |
| The Austin no-show alert was a road closure, not the reminder programme. | `incident_pattern` (90 days) |
| Diane Foster wants vacancies broken down by role. | `staff_preference` (180 days) |

Also memorable: "The referral system fails on Monday mornings because of the overnight batch job."

Not memorable:

| Turn | Why |
|------|-----|
| "What's this week's no-show rate?" | One-off. The figure lives on the dashboard. |
| "Patient Johnson cancelled tomorrow's appointment, note that down." | PHI. The agent says it cannot remember that, and stores nothing. |
| "Thanks, that settles my report." | The conversation is over. |

Ticket lookups, cancellation-fee questions, and "Do you accept Humana?" are also not proposals.

## Proposal, decision, and a single pending item

When the criterion matches, the answer ends with "Want me to remember this for next time?" plus the sentence. Nothing is written yet.

The next message is classified by `classify_decision` into `approve`, `reject`, `edit`, or `ambiguous`, with a confidence score. The threshold is 0.75. The test is a decision word at the start of the message, not `"yes" in message` — that would treat "yesterday" as a yes.

- **Approve** writes the pending sentence and records `staff:{id}` from the JWT.
- **Edit** writes the new wording only after the PHI and policy gates run again.
- **Reject** writes nothing. The audit still records the proposal and the rejection.
- **Ambiguous**, including a topic change, is a rejection. Silence is the same outcome: a pending row older than 24 hours is expired as rejected the next time any turn opens, and that conversation is told the proposal was discarded.

One conversation holds one pending row (`conversation_id` is the primary key). A second insert raises `PendingExists`. A new fact in the same conversation first closes the open proposal as ambiguous, then may propose the new one.

If the same message approves and asks something else ("Yes, remember that. What is the cancellation fee for 12 hours?"), the fact is saved and the graph answers the fee question.

## Forgetting, and poisoning

Consolidation drops expired facts, exact duplicates, and anything the PHI gate now rejects (the stored text is replaced with `[redacted]`). At most 40 active facts remain; the least used, oldest ones go. Rejected proposals are never facts.

A user cannot poison published policy by "correcting" it. A note that Medicare or Medicaid patients pay a no-show fee, or that Humana is accepted, is refused. Desk memory that does get stored is labeled "not a substitute for published policy" when a later answer uses it. The actor id is `staff:` plus the numeric user id. A free-text actor, including a patient name, is stored as `staff:unknown`.

## Why this is not a multi-agent system

Self-evaluation is one `MemoryAssessment` value (`memory_proposal` or null, plus a block reason) produced in the same turn as the graph answer. The decision is one `Decision` value. Both are fields on the turn, filled by the criterion and the classifier. The graph nodes, the knowledge-base prompt, and `GRAPH_VERSION` are untouched, so a second model call is not required to remember a sentence the user already said. A paraphrase call would be a new place for a patient detail to be introduced.

## Evidence cycles

Tests in `tests/pipelines/test_agent_memory.py`:

1. **Approved.** The Manchester referral sentence is proposed and not stored. "Yes, remember that." stores it under `staff:7`. A later question about Manchester referrals includes the sentence under the desk-memory heading.
2. **Rejected.** The Diane Foster preference is proposed. "No, don't remember that." leaves the fact table empty, with audit events `proposed` and `rejected`. A later question does not contain the preference.
