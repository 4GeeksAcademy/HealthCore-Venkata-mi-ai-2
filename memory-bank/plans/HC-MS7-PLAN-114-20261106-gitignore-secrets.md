---
stamp: HC-MS7-PLAN-114
sequence: 114
milestone: MS7
date: 2026-11-06
title: Ignore secret files before any push
status: implemented
phase: implementation
summary: >
  Widens .gitignore so env files, private keys, and credential JSON cannot
  be committed. .env was already ignored and is not tracked. Does not close
  MS7.
related_paths:
  - .gitignore
do_not_repeat:
  - Commit .env, .env.*, private keys, or credential JSON
  - Force-add an ignored secret file
  - Close MS7
  - Save memory-bank/evaluations/Results/MCPServer-*.md before human approval
---

# HC-MS7-PLAN-114 — Secret files stay untracked

`.gitignore` now covers `.env` and `.env.*` in every directory, private keys (`*.pem`, `*.key`, `*.p12`, `*.pfx`, `id_rsa`), and credential JSON (`credentials.json`, `secrets.json`, service-account files).

`git check-ignore` accepts `.env`, `.env.production`, `services/api/.env`, `id_rsa`, `server.pem`, and `credentials.json`. `git ls-files` shows none of those names as tracked. The only secret file on disk is `.env`, and it stays local.

## Agent instructions

1. Do not `git add -f` any ignored secret file.
2. Real staff passwords and API keys stay in `.env` only.
3. Placeholder strings in tests (`agent-secret`, `choose-a-secret`) are fixtures, not credentials.
4. Do not close MS7. Do not write the MCPServer Results file until the human approves it.
