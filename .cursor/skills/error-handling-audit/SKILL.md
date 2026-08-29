---
name: error-handling-audit
description: >-
  Audit the entire HealthCore repository for error-handling gaps across
  frontend, backend, and scripts, then report findings by the required
  taxonomy. Use before making error-handling changes, or when the user asks
  to scan try/catch, silent failures, raw error exposure, missing loading/error
  UI, or sys.exit on script failure.
---

# Error handling audit

Read first:

- [policy.context.md](policy.context.md)
- [findings-taxonomy.context.md](findings-taxonomy.context.md)

## Requirement

Audit the entire existing Repository.

Before making any changes manually, use your coding agent to scan the codebase and surface the most critical gaps.

For each file or module you review, identify and report using the categories and report format in [findings-taxonomy.context.md](findings-taxonomy.context.md).

Do not introduce new features or refactor code unrelated to error handling. The scope of this project is strictly the resilience and error communication of existing code.

## HealthCore repo notes

Known layers in this repo (scan these, and do not skip the rest of the repository):

- Frontend: `uis/healthcore`, `uis/backoffice`
- Backend: `services/api`
- Scripts: Python seed/jobs and other scripts (including `services/api` seed)

Procedure:

1. Scan the entire repository for the eight taxonomy categories.
2. Also review `console.error` and `print` statements across the codebase (General rule).
3. Do not invent findings.
4. Rank by user impact: crash / undefined UI and sensitive leaks first, then missing CTA / loading states, then script exit codes.
5. Suggested fixes stay brief. Implementation is the developer's responsibility unless the user asks to apply fixes.

Report each finding as:

```markdown
### [CATEGORY] `path/to/file` L12–L40

Problem: <one line>
Suggested fix: <brief>
```

End with a short summary: counts by category, and the highest-priority files to fix first.

Do not implement fixes in this skill unless the user explicitly asks to apply them after the report.
