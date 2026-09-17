---
stamp: HC-MS5-PLAN-050
sequence: 50
milestone: MS5
date: 20260916
title: Install Web Performance Skills For Coding Agents
status: implemented
phase: docs
summary: Installed addyosmani core-web-vitals and performance plus Cloudflare web-perf into .cursor/skills, .agents/skills, and .claude/skills. Added HealthCore wrapper skill and AGENTS.md pointers so Cursor and other coding agents can load them.
related_paths:
  - .cursor/skills/core-web-vitals/SKILL.md
  - .cursor/skills/performance/SKILL.md
  - .cursor/skills/web-perf/SKILL.md
  - .cursor/skills/healthcore-web-performance/SKILL.md
  - .agents/skills/core-web-vitals/SKILL.md
  - .agents/skills/performance/SKILL.md
  - .agents/skills/web-perf/SKILL.md
  - .agents/skills/healthcore-web-performance/SKILL.md
  - .agents/skills/web-performance-skills.md
  - .claude/skills/web-perf/SKILL.md
  - AGENTS.md
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Re-download these three upstream skills unless a human asks to refresh them
  - Put copies in ~/.cursor/skills-cursor
---

# HC-MS5-PLAN-050 — Install Web Performance Skills For Coding Agents

## Decisions locked

- Canonical Cursor copies live under `.cursor/skills/`.
- Same files are copied to `.agents/skills/` and `.claude/skills/` so non-Cursor agents can load them.
- HealthCore wrapper is `healthcore-web-performance`.
- Upstream sources remain addyosmani web-quality-skills and Cloudflare web-perf (MIT / their licenses).

## Agent instructions

1. On Lighthouse / Core Web Vitals / page-speed work, read `healthcore-web-performance` then the three upstream skills.
2. Do not invent scores; keep public and backoffice layouts isolated.
3. Append a new stamp for later work; do not rewrite this file.
