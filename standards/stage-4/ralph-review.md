<!-- stages: 4 -->
# Ralph Review — Stage-4 Canonical (#498 AC 4.1)

Three-tier code-delivery verification: Haiku surface → Sonnet logic → Opus deep. Sequential (not parallel); restart from Tier 1 on any tier FAIL. Runs INSIDE Stage 4 implementation BEFORE the Verification Loop's Gate 1.

## Tier sequence

| Tier | Model | Lens | Canonical checklist |
|------|-------|------|---------------------|
| 1    | `haiku`  | Surface — convention adherence, formatting, no-debug-leftovers | `../../ralph/haiku-review.md` |
| 2    | `sonnet` | Logic — control flow, edge cases, contract adherence, test seam | `../../ralph/sonnet-review.md` |
| 3    | `opus`   | Deep — architecture, cross-cutting, governance drift, wrapper-vs-raw counter-query | `../../ralph/opus-review.md` |

## Shared blocks (#498 Cut #10)

The three checklists `_*.md` shared blocks live in `../../ralph/`:
- `_wrapper-lane-preconditions.md` — wrapper-lane invocability + AP #19 `mcp_graph_available` rule.
- `_bash-output-discipline.md` — `tee-run.sh` wrap checkbox (#406 F4.9).
- `_doc-only-exemption.md` — doc-only PR exemption + #484 W6.3 doc-lane / sync-lane diff-trigger exceptions.
- `_fallback-clause.md` — retry-aware, evidence-required fallback clause.

## On FAIL

Fix → restart from Tier 1 (NOT continue from failed tier). Tier dependencies cascade: a Sonnet fix can re-break a Haiku check (e.g. introducing debug code) so the cheapest way to confirm clean is full re-run.

## On PASS (all 3)

Proceed to Verification Loop (Gate 1). Ralph PASS verifies code DELIVERY against the Issue's Acceptance Criteria; it does NOT substitute for Stage 5 adversarial audit (TB-3 N36 — different lens, different class of findings).

## Tier 3 wrapper-vs-raw counter-query (#447 Phase 5)

When ANY Tier-3 finding depends on `sst3-code-*.sh` wrapper output, Opus MUST dispatch ≥1 raw-tool counter-query subagent on the same target before signing PASS. Recall delta + reconciliation recorded inline in the Tier-3 review comment. Skipping when wrapper output is load-bearing = Tier-3 FAIL.

## Cross-references

- `.claude/commands/Leader.md` Stage 4 step 7 — the operator-facing Ralph trigger.
- `../../ralph/{haiku,sonnet,opus}-review.md` — per-tier canonical checklists.
- `../dotfiles/docs/research/model-selection-haiku-4-5.md` — model-selection rationale.
