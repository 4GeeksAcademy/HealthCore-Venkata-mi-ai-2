# HealthCore plan archival rule

**Scope:** always active for this repository.

## Enforce

1. At session start, read `memory-bank/plans/INDEX.md` and the latest stamp before scaffolding or migrating HealthCore apps.
2. After every implementation that ships files, stamp-save a new plan under `memory-bank/plans/` using:

   `HC-MS{N}-PLAN-{NNN}-{YYYYMMDD}-{short-slug}.md`

   The milestone token (`MS4`, `MS5`, …) is **required** in the filename and in frontmatter field `milestone`.

3. Required frontmatter: `stamp`, `sequence`, `milestone`, `date`, `title`, `status`, `phase`, `summary`, `related_paths`, `do_not_repeat`.
4. Required body section: `## Agent instructions` with imperative bullets for future agents.
5. Append the stamp to `INDEX.md` and update `memory-bank/progress.md`.
6. **Never** delete, renumber, or rewrite prior stamps without explicit human confirmation.
7. **Never** redo work listed in an `implemented` stamp’s `do_not_repeat`.
8. Sequence numbers are global and monotonic starting at `001`.
9. Legacy stamps `HC-PLAN-001` / `HC-PLAN-002` (no MS token) are historical MS4 stamps — leave them as-is; do not rename.
10. When a milestone’s scoped work is complete, also follow `.agents/rules/healthcore-milestone-evaluation.md`.

This rule exists so HealthCore Digital agents do not reverse Phase decisions, lose milestone context, or duplicate UI migrations.
