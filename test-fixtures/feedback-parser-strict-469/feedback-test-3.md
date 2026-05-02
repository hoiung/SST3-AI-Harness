---
issue: 3
repo: test
created: 2026-05-02
stages_logged: [1]
---

## Stage 1 — Research

**model**: opus-4-7-1m

**worked**: missing FM fields (last_updated, verdict_summary, topic_keywords, reconstructed_stages) — should fail validate

**didnt**: (none observed)

**why**: Phase 3 fixture set

**improvement**: assert fail-loud on missing FM

**improvement_status**: pending

**evidence**: see run.sh

**friction**: none

**rule_self_caught**: AP #19

**rule_user_caught**: none
