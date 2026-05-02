---
issue: 2
repo: test
created: 2026-05-02
last_updated: 2026-05-02
stages_logged: [1]
verdict_summary: broken H1 heading fixture for #469 strict-mode regression gate
topic_keywords: [test, broken, h1-heading, silent-skip-class-b]
reconstructed_stages: []
---

# Stage 1

**model**: opus-4-7-1m

**worked**: this file uses H1 `# Stage 1` instead of canonical H2 `## Stage 1 — Research`

**didnt**: pre-Phase-3 the parser silently emitted 0 lines + exit 0 for this class

**why**: codepath split between validate-mode (strict) and emit-mode (lax)

**improvement**: post-Phase-3 fixture asserts exit non-zero + stub emission

**improvement_status**: pending

**evidence**: see Issue #469 Phase 3 + this fixture's run.sh assertions

**friction**: none

**rule_self_caught**: AP #19 carve-out applied

**rule_user_caught**: none
