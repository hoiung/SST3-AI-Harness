---
issue: 4
repo: test
created: 2026-05-02
last_updated: 2026-05-02
stages_logged: [1]
verdict_summary: forward-preference fixture for #469 strict-mode regression gate
topic_keywords: [test, broken, forward-preference, channel-separation]
reconstructed_stages: []
---

## Stage 1 — Research

**model**: opus-4-7-1m

**worked**: this fixture trips forward-preference blocklist via the word always

**didnt**: (none observed)

**why**: validates channel-separation rule enforcement

**improvement**: sample regression detection for the forward-pref class

**improvement_status**: pending

**evidence**: run.sh asserts schema_violation stub + exit 1

**friction**: none

**rule_self_caught**: AP #19

**rule_user_caught**: none
