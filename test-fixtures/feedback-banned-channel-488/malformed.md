---
issue: 1
repo: test
created: 2026-05-17
last_updated: 2026-05-17
stages_logged: [1]
verdict_summary: governance fixture asset — bare malformed stage heading (the dotfiles#486/#488 halt class)
topic_keywords: [test, malformed-heading, governance, regression]
reconstructed_stages: []
---

## Stage 1

**model**: opus-4-7-1m

**worked**: the stage heading above is the bare `## Stage 1` form (no em-dash title) — STAGE_HEADING_RE must reject it

**didnt**: (none observed)

**why**: governance fixture per Issue #488 AC 5.3(a) — a structurally malformed file STILL fails its own author's commit post-fix

**improvement**: keep the strict STAGE_HEADING_RE so the write-time template stays load-bearing

**improvement_status**: pending

**evidence**: Issue #488 malformed-heading regression fixture

**friction**: none

**rule_self_caught**: none

**rule_user_caught**: none
