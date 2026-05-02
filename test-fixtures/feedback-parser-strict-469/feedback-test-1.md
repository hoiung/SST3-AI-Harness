---
issue: 1
repo: test
created: 2026-05-02
last_updated: 2026-05-02
stages_logged: [1]
verdict_summary: canonical clean fixture for #469 strict-mode regression gate
topic_keywords: [test, golden, strict-mode, regression]
reconstructed_stages: []
---

## Stage 1 — Research

**model**: opus-4-7-1m

**worked**: golden fixture exercises strict-mode emit-ndjson PASS path

**didnt**: (none observed)

**why**: golden fixture per Issue #469 Phase 5

**improvement**: keep the strict-mode codepath single (validate-then-emit)

**improvement_status**: pending

**evidence**: Issue #469 Phase 5 fixture set

**friction**: none

**rule_self_caught**: AP #19 carve-out applied (graph_applicable=false)

**rule_user_caught**: none
