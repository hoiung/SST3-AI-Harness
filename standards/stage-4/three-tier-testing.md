<!-- stages: 4 -->
# Three-Tier Testing Framework — Stage-4 Canonical (#498 AC 4.1)

BUILD-vs-USE testing model: the canonical (BUILD) requires all 3 tiers to EXIST; the per-issue USE clause scope-matches which tier(s) fire on this change. Project test suite ("no regressions") = the union of checked-in Unit + Workflow + E2E tests.

## Tiers

| Tier | Scope | Fire condition |
|------|-------|----------------|
| Unit     | Single function / class / module | Always — every change. |
| Workflow | Cross-module CLI invocation / state propagation | When change affects CLI / pipeline / SL1 / SL2 / cross-module function-arg propagation (AP #18). |
| E2E      | Real-system end-to-end against real DB / real services | When change affects entire system, persistence, or live-trade safety. |

## BUILD vs USE

- **BUILD** (always required): all 3 tiers' tests EXIST in repo. Pre-commit gates verify presence.
- **USE** (scope-matched on this Issue):
  - entire-system change → all 3 tiers fire
  - workflow change → Unit + Workflow tiers fire
  - single-unit change → Unit tier fires
- "Tests pass" means the USE subset PASS, not that all three tiers ran on every change.

## AP #18 sample-invocation = the Workflow Tier USE clause

The Workflow-Tier USE clause is canonically AP #18: real-CLI ≥3-repo-shape invocation, raw-tool counter-query, row-count + downstream-consumer + wrapper-vs-raw-delta verification, exit-0-insufficient, explicit `call_args.kwargs[...]` mock-assertions. Spec lives in `../../standards/STANDARDS.md` "Three-Tier Testing Framework" / "Workflow Validation Gate" + `../../standards/ANTI-PATTERNS.md` AP #18.

## Cross-references

- `../../workflow/WORKFLOW.md` "Verification Loop" canonical tier checkboxes.
- `../../standards/STANDARDS.md` "Three-Tier Testing Framework" subsection.
- `../../standards/ANTI-PATTERNS.md` AP #18 — sample-invocation = Workflow Tier USE clause.
- Per-shape recipes: see ANTI-PATTERNS.md AP #18 "Tier coverage" table.
