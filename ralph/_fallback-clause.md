# Ralph Review — Shared Fallback Clause Block (#498 Cut #10)

> Canonical block for the retry-aware, evidence-required fallback clause that haiku/sonnet/opus all need. Each tier file points here.

## Fallback Clause (retry-aware, evidence-required)

If the first wrapper-lane call fails, retry once. If the second fails, OR the target language is unsupported by the wrapper, the RESULT block MUST include ONE of:

- **(A) Graph evidence**: `last_updated`, number of results per query, spot-check source file:line; OR
- **(B) Subagent-fallback evidence**: an Explore subagent's RESULT block showing the manual call-graph / orphan / impact / architectural audit was actually performed, referenced in main RESULT as `[subagent fallback: Explore / <subagent-id>]` with concrete findings (e.g. "checked 5 call sites, all compatible" or "Layer 1 subagent verified 3 caller contracts compatible, 2 flagged for semantic review").

Documenting `[graph unavailable]` without EITHER (A) or (B) is a silent skip = **FAIL**. A documented fallback WITH subagent evidence = **PASS**.

This rule is identical across Ralph tiers (haiku surface / sonnet logic / opus architectural); the depth of subagent audit required differs by tier (haiku = call-site spot-check, sonnet = caller-contract trace, opus = architectural impact + dead code + large-function audit).
