---
issue: 1
repo: test
created: 2026-05-16
last_updated: 2026-05-16
stages_logged: [1]
verdict_summary: canonical clean fixture for #486 commit-gate regression
topic_keywords: [test, golden, commit-gate, regression]
reconstructed_stages: []
---

## Stage 1 — Research

**model**: opus-4-7-1m

**worked**: golden fixture exercises the #486 strict commit-gate PASS path

**didnt**: (none observed)

**why**: golden fixture per Issue #486

**improvement**: keep the commit-gate hard-fail decoupled from advisory DRIFT

**improvement_status**: pending

**evidence**: Issue #486 commit-gate regression fixture

**friction**: none

**rule_self_caught**: AP #19 carve-out applied (graph_applicable=false)

**rule_user_caught**: none
