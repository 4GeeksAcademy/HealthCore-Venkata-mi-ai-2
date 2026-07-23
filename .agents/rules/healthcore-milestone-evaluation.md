# HealthCore milestone evaluation rule

**Scope:** always active for this repository.

## Enforce

1. Every HealthCore milestone (`MS2`, `MS3`, `MS4`, …) must have a project evaluation file when its scoped work is complete:

   `memory-bank/evaluations/MS{N}_Project_Eval.md`

2. Maintain [`memory-bank/evaluations/INDEX.md`](../../memory-bank/evaluations/INDEX.md) as the ordered registry.
3. Evaluation files must include: objectives, delivered, verification, gaps/deferred, scorecard, and `## Agent instructions`.
4. After writing/updating a milestone eval, update `memory-bank/progress.md` to reference it.
5. Do **not** close a milestone in `progress.md` as complete without a matching eval entry (status `complete`).
6. Do **not** delete prior milestone evals without explicit human confirmation.
7. Plan stamps for a milestone must include the milestone token in the filename (see plan-archive rule): `HC-MS{N}-PLAN-{NNN}-...`.
8. When starting work, if the user names a milestone, read that milestone’s eval (if present) before changing related files.

This rule exists so HealthCore Digital agents record acceptance outcomes per milestone and do not silently skip evaluation.
