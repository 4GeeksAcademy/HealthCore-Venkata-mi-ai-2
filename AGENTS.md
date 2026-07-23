# HealthCore Digital — Agent Operating Manual

This repository serves **HealthCore**, an outpatient healthcare network. Agents must follow this file on every session.

---

## Session Start Workflow

Before any code or documentation changes:

1. Read [`memory-bank/projectbrief.md`](memory-bank/projectbrief.md).
2. Read [`memory-bank/techContext.md`](memory-bank/techContext.md).
3. Read [`memory-bank/progress.md`](memory-bank/progress.md).
4. Read [`memory-bank/plans/INDEX.md`](memory-bank/plans/INDEX.md) and the **latest** stamped plan (highest sequence).
5. If the user names a milestone (e.g. MS4), also read [`memory-bank/evaluations/INDEX.md`](memory-bank/evaluations/INDEX.md) and that milestone’s `MS{N}_Project_Eval.md` when present.
6. Obey `do_not_repeat` and `## Agent instructions` from the latest stamp (and milestone eval if applicable).
7. Only then proceed with the user’s request.

---

## Mandatory Pre-Commit Workflow

Run these **four steps in order** before any Git commit:

1. **Linting** — In every touched UI package under `uis/`, run `npm run lint`. Fix failures before continuing.
2. **Type-checking** — For touched UI packages run `npx tsc --noEmit` (or the package script if present). If `src/` changed, run root `npm run typecheck`.
3. **State Sync** — Update [`memory-bank/progress.md`](memory-bank/progress.md) to match reality. If an implementation phase completed, perform the **Post-Implementation Plan Save** below. If a milestone’s scoped work is complete, also write/update the milestone evaluation.
4. **Change Logging** — Write a PHI-safe commit message (no patient names, member IDs, or clinical free text). Summarize HealthCore business intent (billing, no-shows, CME, hiring, public site, backoffice).

---

## Post-Implementation Plan Save

After every implementation that ships files (including Phase completions):

1. Allocate the next stamp id from [`memory-bank/plans/INDEX.md`](memory-bank/plans/INDEX.md).
2. Create a stamp file named:

   `memory-bank/plans/HC-MS{N}-PLAN-{NNN}-{YYYYMMDD}-{short-slug}.md`

   Include required frontmatter (`stamp`, `sequence`, `milestone`, `date`, `title`, `status`, `phase`, `summary`, `related_paths`, `do_not_repeat`) and a `## Agent instructions` section.
3. Append the stamp to `INDEX.md`.
4. Point `progress.md` at the new stamp.
5. Do **not** rewrite prior stamps (including legacy `HC-PLAN-001` / `HC-PLAN-002`).

See [`.agents/rules/healthcore-plan-archive.md`](.agents/rules/healthcore-plan-archive.md) and [`memory-bank/plans/README.md`](memory-bank/plans/README.md).

---

## Post-Milestone Evaluation Save

When a milestone’s scoped work is complete:

1. Write or update `memory-bank/evaluations/MS{N}_Project_Eval.md` (e.g. `MS4_Project_Eval.md`).
2. Update [`memory-bank/evaluations/INDEX.md`](memory-bank/evaluations/INDEX.md).
3. Reference the eval from `progress.md`.
4. Follow [`.agents/rules/healthcore-milestone-evaluation.md`](.agents/rules/healthcore-milestone-evaluation.md).

Every milestone from MS4 onward **must** have this evaluation before marking the milestone complete.

---

## Protected Zones

Do **not** modify the following without **explicit human-developer confirmation**:

| Zone | Reason |
|------|--------|
| `CONTEXT.md`, `CONTEXT_temp.md` | Canonical assignment / business contract |
| `memory-bank/projectbrief.md`, `memory-bank/techContext.md` | Structural product identity |
| `memory-bank/plans/HC-PLAN-*.md`, `memory-bank/plans/HC-MS*-PLAN-*.md` | Append-only history (no rewrite/delete) |
| `memory-bank/evaluations/MS*_Project_Eval.md` | Milestone acceptance history (no delete; prefer append-only updates only with human confirmation for rewrites) |
| `data/` | Patient-adjacent samples / pipelines / eval |
| `.env*` and credential files | Secrets |
| Production deploy configs / secret stores | Live environment risk |
| Root lockfiles (`package-lock.json`, etc.) | Unless dependency work was explicitly requested |

Allowed without extra confirmation: updating `memory-bank/progress.md`, appending new stamps + `INDEX.md` entries, creating new milestone evals when a milestone completes, and normal feature work outside protected zones.

---

## HealthCore isolation reminders

- Public app: `uis/healthcore` — medical/corporate patient-facing site.
- Internal app: `uis/backoffice` — Digital staff tools (welcome + hiring tracker).
- Never share layouts between public and backoffice.
- Treat sample IDs (`HC-*`, `CLM-*`, …) as synthetic; never invent real PHI.
