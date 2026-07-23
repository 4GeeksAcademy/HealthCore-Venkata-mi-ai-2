# HealthCore stamped plans — agent README

This folder is the **append-only archive** of HealthCore implementation plans. Future agents must treat it as the source of truth for what was already decided and shipped.

## Mandatory session behaviour

1. Read [`INDEX.md`](./INDEX.md) first.
2. Open the **highest sequence** stamp listed as `implemented` (or the latest entry if still `planned`).
3. Obey that stamp’s `do_not_repeat` and `## Agent instructions` before creating or migrating files.
4. Never rewrite or delete prior stamp files without explicit human confirmation.
5. Read [`../evaluations/INDEX.md`](../evaluations/INDEX.md) when closing or reviewing a milestone.

## Filename convention (required)

```text
HC-MS{N}-PLAN-{NNN}-{YYYYMMDD}-{short-slug}.md
```

Examples:

- `HC-MS4-PLAN-003-20260722-eval-and-naming.md`
- `HC-MS5-PLAN-001-20260801-ops-dashboards.md`

| Token | Meaning |
|-------|---------|
| `MS{N}` | Milestone id (MS4, MS5, …) — **required in every new stamp name** |
| `{NNN}` | Global monotonic sequence across the repo (`001`, `002`, …) — never reuse |
| `{YYYYMMDD}` | Stamp date |
| `{short-slug}` | kebab-case summary |

**Legacy note:** `HC-PLAN-001` and `HC-PLAN-002` were created before this convention. They remain valid MS4 history and must not be renamed. All **new** stamps must include `MS{N}`.

## After every implementation

1. Read `INDEX.md` and allocate the next sequence number. Never reuse or renumber.
2. Write a new file using the convention above.
3. Include YAML frontmatter with at least: `stamp`, `sequence`, `milestone`, `date`, `title`, `status`, `phase`, `summary`, `related_paths`, `do_not_repeat`.
4. Include a `## Agent instructions` section with imperative bullets for future agents.
5. Append a row to `INDEX.md`.
6. Update [`../progress.md`](../progress.md) to reference the new stamp.
7. If the milestone’s scoped work is now complete, write/update `../evaluations/MS{N}_Project_Eval.md` (see evaluations README).

## Status values

| Status | Meaning |
|--------|---------|
| `planned` | Documented but not yet implemented |
| `implemented` | Files shipped; agents must not redo listed work |
| `superseded` | Replaced by a later stamp (record in INDEX; prefer not rewriting the old file body) |

## Why this exists

HealthCore Digital agents must not re-scaffold memory bank / UIs, re-migrate the hiring tracker, or contradict locked public-vs-backoffice isolation. Milestone-prefixed stamps keep MS4/MS5 history unambiguous.
