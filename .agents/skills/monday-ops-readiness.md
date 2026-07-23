# Skill: HealthCore Monday ops readiness

**Scope:** agent-requested / recurring workflow (use before Monday stakeholder review or after ops/UI changes).

## Objective

Verify HealthCore Monday-morning readiness for surfaces that serve Tom Callahan (billing denials), Marcus Reid (no-show costs), Diane Foster (CME compliance and hiring pipeline), and James Osei (CTO) — without introducing PHI risk.

## Required inputs

1. Target branch or commit SHA.
2. List of changed paths under `src/` and/or `uis/`.
3. Explicit confirmation that no real PHI was introduced (synthetic sample IDs only).
4. Path to the latest stamped plan (`memory-bank/plans/HC-MS*-PLAN-*.md` or legacy `HC-PLAN-*.md`) referenced by `INDEX.md`.
5. If a milestone is being closed, path to `memory-bank/evaluations/MS{N}_Project_Eval.md`.

## Procedure

1. Confirm session start docs were read (`projectbrief`, `techContext`, `progress`, latest stamp).
2. Run lint on every touched UI package.
3. Run typecheck for touched packages and root `npm run typecheck` if `src/` changed.
4. If UI apps exist, document smoke paths:
   - Public: `uis/healthcore` (`npm run dev`) — home + one secondary section.
   - Backoffice: `uis/backoffice` (`npm run dev`) — `/` welcome + hiring module if present.
5. Confirm protected zones were not modified without human confirmation.
6. Confirm `progress.md` points at the latest stamp; if implementation shipped without a stamp, create one before finishing.

## Acceptance criteria (verifiable)

- [ ] Lint exits 0 for all touched UI packages.
- [ ] Typecheck exits 0 for applicable packages / root.
- [ ] No real PHI in diffs (synthetic IDs only).
- [ ] Protected zones untouched unless human confirmed.
- [ ] `memory-bank/plans/INDEX.md` lists a stamp whose `status` matches the work just completed (new stamps include `MS{N}` in the name).
- [ ] `memory-bank/progress.md` references that stamp.
- [ ] If the milestone is complete, `memory-bank/evaluations/MS{N}_Project_Eval.md` exists and is listed in evaluations `INDEX.md`.
- [ ] Smoke paths for public vs backoffice are written in the session note when those apps exist.
