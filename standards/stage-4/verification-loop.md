<!-- stages: 4 -->
# Verification Loop — Stage-4 Canonical (#498 AC 4.1)

The Verification Loop is the iteration block that runs AFTER all phase ACs land + Ralph Review completes, and BEFORE Gate 2 (merge). Loop exits only when EVERY checkbox passes; iterate until clean.

## Loop checkboxes (canonical: `../../workflow/WORKFLOW.md` "Verification Loop")

- Graph-backed diff audit when `graph_applicable=true` (carry-forward from Stage 1 research file; NEVER re-classify).
- Layer 3 Checkbox-MCP coverage gate (AP #20 final check). All Tier-A boxes MCP-ticked with canonical evidence.
- Overengineering / Reuse / Duplication / Fallback-policy / Wiring checks.
- Three-Tier test gate (Unit / Workflow / E2E) per `three-tier-testing.md`.
- AP #18 sample-invocation (Workflow Tier real-CLI invocation; the Workflow-Tier USE clause).
- Skill-canonical verification (Double-Guardrail; runs invoked-skill's own hooks).
- Mirror-lane Lane A + Lane B 3-command verification.
- Doc-lane diff-trigger when diff touches `*.md` / frontmatter.

## Cross-references

- `../../workflow/WORKFLOW.md` — canonical loop checkboxes.
- `.claude/commands/Leader.md` Stage 4 Gate 1 — the operator-facing trigger.
- `../../standards/STANDARDS.md` "Workflow Validation Gate" — AP #18 binding rule.
- `../../standards/ANTI-PATTERNS.md` AP #14c (subagent verification), AP #18 (sample invocation), AP #20 (checkbox MCP).
- `../../standards/stage-4/three-tier-testing.md` — Unit/Workflow/E2E tier USE rules.
- `../../standards/stage-4/observability-fail-fast.md` — runtime observability invariants the loop verifies.

## When the loop exits

Loop exits ONLY when every checkbox PASSES — no exceptions for "high priority" or "low priority". The only valid skip is a confirmed false positive with documented evidence (AP #11). Skipping a check because it's inconvenient is a direct STANDARDS.md violation (Fix Everything).

On any FAIL: fix, re-run ALL checks (not just the failed one). The cascading-fix property is intentional — one fix can re-break a previously-clean check, so the cheapest way to confirm clean state is full re-run.
