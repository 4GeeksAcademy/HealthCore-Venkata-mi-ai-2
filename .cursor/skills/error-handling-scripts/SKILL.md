---
name: error-handling-scripts
description: >-
  Harden Python scripts and seed jobs with scoped I/O error handling and
  non-zero exit codes. Use when editing seed.py, pipelines, CLI scripts,
  CSV/file parsing, or when a script fails but still exits 0. Also use to
  review console.error / print statements that may leak internals.
---

# Script error handling

Read first:

- [policy.context.md](../error-handling-audit/policy.context.md)
- [findings-taxonomy.context.md](../error-handling-audit/findings-taxonomy.context.md)

## Scripts (Python)

- Wrap file I/O and CSV parsing operations in try/except blocks with informative error messages printed to stderr.
- Ensure scripts exit with a non-zero code (`sys.exit(1)`) when a critical error occurs.
- Add defensive checks for missing or malformed input data before processing begins.

On the backend and scripts, exceptions must be caught at the right scope — not with a single try/catch wrapping the entire function.

## General

Review the codebase for any `console.error` or `print` statements that expose sensitive internal information and remove or replace them.

⚠ IMPORTANT: Do not introduce new features or refactor code unrelated to error handling.

## HealthCore repo notes

- Includes `services/api` seed/jobs and other Python scripts in the repo.
- Catch the I/O or parse operation, not the entire script body.
- Print operator-facing messages to stderr. Do not dump stack traces that include secrets, connection strings, internal paths, or personal data.
- Critical failure must not exit 0.
- HealthCore sample data remains synthetic; still never print real-looking PHI.
