---
issue: 1
repo: test
created: 2026-05-17
last_updated: 2026-05-17
stages_logged: [1]
verdict_summary: canonical-valid fixture asset for the #488 per-file-vs-whole-corpus governance proof
topic_keywords: [test, feedback-lane, per-file, whole-corpus, regression]
reconstructed_stages: []
---

## Stage 1 — Research

**model**: opus-4-7-1m

**worked**: golden canonical feedback file — exercises the post-#488 per-file commit-stage validate PASS path

**didnt**: (none observed)

**why**: golden fixture per Issue #488 AC 3.2 / 5.3

**improvement**: keep the per-file commit hook decoupled from the whole-corpus CI catch

**improvement_status**: pending

**evidence**: Issue #488 per-file-vs-corpus regression fixture

**friction**: none

**rule_self_caught**: AP #19 carve-out applied (graph_applicable=false)

**rule_user_caught**: none
