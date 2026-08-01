---
stamp: HC-MS4-PLAN-007
sequence: 7
milestone: MS4
date: 20260731
title: Architecture Proposal Pattern Comparison Expansion
status: implemented
phase: docs
summary: Expanded docs/ARCHITECTURE_PROPOSAL.md Section 2 with pros/cons for Layered/Clean, MVC, Microservices, and Serverless, plus comparative table and strong Layered/Clean recommendation for HealthCore FastAPI.
related_paths:
  - docs/ARCHITECTURE_PROPOSAL.md
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Rewrite ARCHITECTURE_PROPOSAL.md from scratch without human confirmation
  - Collapse Section 2 back to a short chosen-pattern note without the four-way comparison
---

# HC-MS4-PLAN-007 — Architecture Proposal Pattern Comparison Expansion

## Decisions locked

- Four patterns evaluated: Layered/Clean, MVC, Microservices, Serverless.
- Recommended primary pattern remains Layered Architecture with Clean principles.
- MVC and Microservices are not preferred now; Serverless is situational for later jobs/alerts only.

## Agent instructions

1. Do not rewrite PLAN-006; this stamp supersedes only the Section 2 comparison depth.
2. Do not scaffold a FastAPI backend unless the user explicitly requests implementation.
3. Append new stamps for further doc edits after human review.
