---
issue: 5
repo: test
created: 2026-05-02
last_updated: 2026-05-02
stages_logged: [1]
verdict_summary: bullet-prefix legacy field format fixture for #469 strict-mode gate
topic_keywords: [test, broken, bullet-prefix, legacy-format]
reconstructed_stages: []
---

## Stage 1 — Research

- model: opus-4-7-1m
- worked: legacy bullet-prefix fields like this no longer parse
- didnt: (none)
- why: bullet-prefix-with-no-bold form
- improvement: assert fail
- improvement_status: pending
- evidence: run.sh
- friction: none
- rule_self_caught: AP 19
- rule_user_caught: none
