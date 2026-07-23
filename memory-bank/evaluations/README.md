# HealthCore milestone evaluations — agent README

This folder stores **per-milestone project evaluations** for HealthCore Digital work. Every completed milestone must have an evaluation file here before the milestone is considered closed.

## Naming

```text
MS{N}_Project_Eval.md
```

Examples: `MS4_Project_Eval.md`, `MS5_Project_Eval.md`

Optional supporting notes: `MS{N}_Project_Eval_notes.md` (rare; prefer one eval file).

## Mandatory behaviour

1. At session start, if the user names a milestone (e.g. MS4), read that milestone’s eval if it exists under this folder and [`INDEX.md`](./INDEX.md).
2. When a milestone’s scoped work is complete (all planned phases shipped and stamped), write or update `MS{N}_Project_Eval.md` with the required sections below.
3. Append/update the row in `INDEX.md`.
4. Point [`../progress.md`](../progress.md) at the latest eval for that milestone.
5. Do **not** delete prior milestone evals without explicit human confirmation.

## Required sections in every `MS{N}_Project_Eval.md`

Use YAML frontmatter plus these body sections:

```yaml
---
milestone: MS4
title: Milestone 4 Project Evaluation
date: YYYY-MM-DD
status: complete   # in_progress | complete
related_plans:
  - HC-MS4-PLAN-001-...
summary: One-line outcome
---
```

1. **Objectives** — what the milestone set out to do for HealthCore  
2. **Delivered** — what shipped (paths, apps, stamps)  
3. **Verification** — lint/typecheck/smoke evidence  
4. **Gaps / deferred** — honest leftovers  
5. **Scorecard** — pass/fail or rating per objective  
6. **Agent instructions** — what future agents must assume is done for this milestone  

## Why this exists

Prevents agents from re-opening finished milestone scope, forgetting acceptance criteria, or starting MS{N+1} without a recorded MS{N} evaluation.
