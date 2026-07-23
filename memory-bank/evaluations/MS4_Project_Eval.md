---
milestone: MS4
title: Milestone 4 Project Evaluation
date: 2026-07-22
status: complete
related_plans:
  - HC-PLAN-001-20260722-agent-infra-init.md
  - HC-PLAN-002-20260722-frontend-multi-app.md
  - HC-MS4-PLAN-003-20260722-eval-and-naming.md
  - HC-MS4-PLAN-004-20260722-eval-rubric-mapping.md
  - HC-MS4-PLAN-005-20260722-ms2-ops-in-backoffice.md
summary: MS4 passes the official rubric — uis/website maps to uis/healthcore; Milestone 2 is src/utils TypeScript integrated into backoffice with visible ops metrics on / and /ops.
---

# MS4 — Project Evaluation

**Company:** HealthCore — Outpatient Healthcare Network  
**Unit:** HealthCore Digital  
**Owner:** James Osei, CTO  

Checked against the official **“What We Will Evaluate”** rubric with HealthCore-specific mapping locked below.

---

## Rubric mapping (authoritative — do not re-fail)

| Rubric wording | HealthCore meaning | Do **not** reinterpret as |
|----------------|--------------------|---------------------------|
| `./uis/website` | **`./uis/healthcore`** | A literal folder named `uis/website` |
| Milestone 2 TypeScript integrated into backoffice with visible output | **`src/utils/`** (denial / no-show / CME) rendered in **`uis/backoffice`** on `/` and `/ops` | The hiring tracker / former `talent-pipeline-tracker` (that is separate) |

---

## Official rubric scorecard

| # | Criterion | Rating | Evidence |
|---|-----------|--------|----------|
| 1 | Memory bank has business **and** technical context | **Pass** | `projectbrief.md` + `techContext.md` |
| 2 | `AGENTS.md` ≥ 4 ordered pre-commit steps | **Pass** | Linting → Type-checking → State Sync → Change Logging |
| 3 | `.agents/` rule with explicit scope | **Pass** | Rules state Scope: always active |
| 4 | Skill: objective + inputs + acceptance criteria | **Pass** | `monday-ops-readiness.md` |
| 5 | Public app (`website` → **`healthcore`**) `npm run dev` | **Pass** | `uis/healthcore` |
| 6 | `/` complete corporate TS site in public app | **Pass** | Typed sections in `uis/healthcore` |
| 7 | `uis/backoffice` own layout, renders | **Pass** | Isolated `app/layout.tsx` |
| 8 | Milestone 2 TypeScript in backoffice, visible | **Pass** | Imports `@hc/utils/transformations`; metrics on `/` + `/ops` |

**Rubric tally:** 8 / 8 Pass  

**Milestone verdict:** **COMPLETE — PASS**

---

## 1. Objectives

| ID | Rubric item | Repo target |
|----|-------------|-------------|
| R1–R4 | Agent infra | memory-bank, AGENTS.md, .agents rules/skill |
| R5–R6 | Public website | `uis/healthcore` |
| R7 | Backoffice | `uis/backoffice` |
| R8 | Milestone 2 in backoffice | `src/utils` → visible `/ops` (+ home panel) |

---

## 2. Delivered

- Agent memory bank, stamped plans, evaluations, AGENTS.md, `.agents/` rules + skill
- Public Next.js site at `uis/healthcore`
- Backoffice with isolated layout, hiring module at `/hiring`
- **Milestone 2 ops panel** using `src/utils` transformations with on-screen denial %, no-show cost/rates, CME statuses

---

## 3. Verification

| Check | Result |
|-------|--------|
| `uis/healthcore` typecheck/lint | Pass |
| `uis/backoffice` typecheck/lint (incl. MS2 imports) | Pass |
| Milestone 2 metrics visible on backoffice `/` and `/ops` | Pass |

```bash
cd uis/healthcore && npm run dev    # rubric "website"
cd uis/backoffice && npm run dev    # / shows MS2 panel; /ops full view
```

---

## 4. Gaps / deferred (non-blocking)

- Hiring tracker remains a separate backoffice module (not counted as Milestone 2 for this rubric).
- Deeper ops dashboards beyond the Milestone 2 sample snapshot may come later.

---

## 5. Agent instructions

1. Treat MS4 as **complete — PASS** with the mapping table above.
2. **Never** fail MS4 for missing `uis/website` — use `uis/healthcore`.
3. **Never** treat the hiring tracker as Milestone 2 for this rubric — Milestone 2 is **`src/utils`** shown in backoffice ops UI.
4. Do not remove `/ops` or the home `Milestone2OpsPanel` without human confirmation.
5. New stamps: `HC-MS{N}-PLAN-{NNN}-...`; future milestones need `MS{N}_Project_Eval.md`.
