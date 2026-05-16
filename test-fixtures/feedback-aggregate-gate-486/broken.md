---
issue: 2
repo: test
created: 2026-05-16
last_updated: 2026-05-16
stages_logged: [1]
topic_keywords: [test, broken, commit-gate, regression]
reconstructed_stages: []
---

## Stage 1 — Research

**model**: opus-4-7-1m

**worked**: deliberately broken in-scope feedback file — FM is missing the
required `verdict_summary` field, so feedback_parser.py hard-fails it. A
conforming filename (feedback-test-2.md) means this MUST block the commit
gate (#486 AC5). If the gate ever lets this through, that is the silent-rot
regression returning.

**didnt**: n/a

**why**: regression fixture per Issue #486

**improvement**: n/a

**improvement_status**: pending

**evidence**: Issue #486

**friction**: none

**rule_self_caught**: none

**rule_user_caught**: none
