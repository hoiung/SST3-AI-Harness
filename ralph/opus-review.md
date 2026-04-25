# Tier 3: Opus Review (Deep Analysis)

> **PLANNING MODE ONLY**: You are a REVIEWER. Do NOT write code, do NOT edit files, do NOT make commits. Your ONLY job is to verify and report findings.

Thorough architectural review. Catches 10% of issues missed by Haiku+Sonnet.

**Completion Promise**: `<promise>OPUS_PASS</promise>`

## Checklist

### Architectural Fit
- [ ] Implementation fits existing architecture
- [ ] No architectural violations (patterns, layers, boundaries)
- [ ] Integrates cleanly with existing code
- [ ] No tight coupling introduced

### STANDARDS.md Compliance
- [ ] Fail Fast principle followed (no silent fails)
- [ ] No Hardcoded Settings (config externalized)
- [ ] Modularity standards met
- [ ] LMCE principles applied

### Governance — Checkbox-MCP Drift Audit (AP #20)
- [ ] **Governance drift audit — two-tier cadence rule**: fetch the issue body via `mcp__github__get_issue` (or `mcp__github-checkbox__get_issue_checkboxes` for live state; ToolSearch-bootstrap if deferred per `../standards/STANDARDS.md` "MCP Tool Schema Loading") and parse the `## Proof of Work` section — the canonical audit signal per `../standards/STANDARDS.md` "Governance Evidence Signal (Canonical)" (codependent — do not edit in isolation, see #429 Phase 9 + #431 Phase 2a). Cross-reference entry order + evidence against the solo-branch `git log --oneline`. **Do NOT use `get_issue_events` PATCH timeline** — GitHub suppresses issue-author's own body edits from the timeline, so PATCH-event-based cadence audit false-negatives 100% of honored invocations (evidence: #429 spot-check 2026-04-21 returned 0 `edited` events for 80 honored boxes). Classify every checked `[x]` box into one of two tiers:
  - **Tier A — Phase-deliverable checkboxes** (items in Acceptance Criteria Phases 1..N that describe a concrete deliverable — a file edit, commit, function, section, table, example): **STRICT interleaving required**. Proof of Work entry order MUST interleave with git-log commit order within the same phase's commit window (between first commit of phase N and first commit of phase N+1). Cluster-at-end (many entries appended after all phase commits) = FAIL.
  - **Tier B — Cross-cutting meta-checkboxes** (Triple-Check Gate items, Engineering Requirements meta-items like "Fix Everything", Cleanup Requirements, Verification Loop self-gates, PREREQUISITE CHECKPOINT, Expected Behavior post-condition items): **batched-at-end acceptable** because these describe conditions observable ONLY after all phases complete. Closing them mid-phase would be dishonest (agent cannot honestly tick "all cross-links resolve" or "no dead code" before all code is written).
- [ ] **Classification heuristic**: if the checkbox text names a specific file/commit/section/function/table to build or change, it is **Tier A** (phase-deliverable). If it describes a cross-cutting condition requiring the WHOLE implementation to evaluate (e.g. "what am I assuming?", "all files located per STANDARDS.md", "no commented-out old code left behind", "all checkboxes verified with evidence"), it is **Tier B** (meta). When in doubt, inspect the checkbox's section in the issue template: Acceptance Criteria sub-phases = Tier A; Triple-Check Gate / Engineering Requirements meta / Cleanup Requirements / Verification Loop self-gates / PREREQUISITE CHECKPOINT / Expected Behavior = Tier B.
- [ ] **Rule**: **Flag Tier A batching as AP #20 drift.** **Do NOT flag Tier B batching as drift.** A Tier-B-only batch is acceptable and expected for honest post-condition evaluation. Canonical failure mode: `../standards/ANTI-PATTERNS.md` **AP #20** (codependent — do not edit in isolation, see #429 Phase 9 + #431 Phase 2a); canonical evidence patterns: `../reference/tool-selection-guide.md` Example 2; canonical audit signal: `../standards/STANDARDS.md` "Governance Evidence Signal (Canonical)".

### STANDARDS.md Violation Scan (Architectural)

> Deep analysis for the 5 common culprits across entire implementation. Category names + framing canonical in [`_common-culprits.md`](_common-culprits.md) (#406 F3.4).

**1. Duplicate Code (DRY/Modularity)**
- [ ] No architectural duplication (same pattern implemented differently in multiple places)
- [ ] No cross-file copy-paste (same logic in src/ and tests/)
- [ ] Check: Should there be a shared module for this?
- [ ] Verify: Does implementation reuse existing utilities?

**2. On-the-fly Calculations (Hardcoded Settings)**
- [ ] No business formulas embedded in application code
- [ ] No calculation constants that vary by environment/strategy
- [ ] Check: Are all formulas that could change externalized to config?
- [ ] Verify: Config-First Architecture followed (YAML co-located with code)

**3. Hardcoded Settings**
- [ ] No settings that should be user-configurable
- [ ] No environment-specific values in code
- [ ] Check: Would changing this value require a code change?
- [ ] Verify: All thresholds, limits, multipliers in config files

**4. Obsolete/Dead Code (LMCE)**
- [ ] No modules/classes that are never instantiated
- [ ] No API endpoints that are never called
- [ ] No database migrations for deleted tables
- [ ] Check: If commented "for backwards compatibility" - is it actually needed?
- [ ] Verify: Implementation is Lean, Mean, Clean, Effective

**5. Silent Fallbacks (Fail Fast)**
- [ ] No cascading defaults that mask root cause
- [ ] No graceful degradation that hides broken dependencies
- [ ] Check: If this fails, will the user/operator know immediately?
- [ ] Verify: Errors are unmistakable (per Fail Fast standard, STANDARDS.md)

**6. Cross-Boundary Contract Audit — Architectural (Issue #1407 post-mortem)**

> Deep cross-system reasoning. Every value that crosses a boundary (code↔DB, code↔config, caller↔callee, backend↔frontend) must have its contract verified.

**SQL/Schema Architecture**
- [ ] All SQL in the diff audited against DB schema (migrations/) — column names, types, table existence verified
- [ ] No query references a column that was renamed, removed, or never added in any migration
- [ ] SQL literal values (strings in WHERE) cross-referenced against actual DB data — check for normalization mismatches

**Null Propagation Architecture**
- [ ] Null propagation audit: identify all values that can be None (DB results, API responses, optional config) and trace to consumption points — all arithmetic/method-call/formatting sites guarded?
- [ ] Frontend data contract: for each API response field displayed in UI, verify null/undefined handled at display layer
- [ ] Type annotations match reality: if annotation says `float`, verify NO caller can pass `None`. If they can → annotation must be `float | None` and function must guard.

**Config Architecture (Bidirectional)**
- [ ] Bidirectional config audit: (1) code has no hardcoded values → config exists; (2) config has no orphaned keys → code consumes them
- [ ] Any config section added for a new feature: verify the feature's code reads EVERY key in that section

**Lifecycle Wiring Architecture**
- [ ] Lifecycle wiring audit: for each recovery/drain/replay function, map ALL lifecycle events where data could accumulate, confirm function wired to every one
- [ ] "Called at reconnect" does NOT imply "called at startup" — verify separately
- [ ] Scope completeness: enumerate every Acceptance Criteria checkbox from issue body — each must map to a specific file:line. Any without = NOT DONE.

**Data Correction Architecture**
- [ ] If bug produced bad DB state: fix includes BOTH (a) code fix for future AND (b) verified data repair for existing rows — confirm both exist and repair scope matches bug scope

**7. Factual Claims Audit**
- [ ] Enumerate all numeric assertions in documentation, issue body, and design rationale added by this implementation
- [ ] For each: does a verifiable source exist (benchmark, prior issue, measured observation, command output)?
- [ ] If no source: flag as unverified claim — must be sourced or removed before OPUS_PASS

### Required when graph available: Code Graph Checks (Architectural Depth)

**Rollout note**: this check became required with Issue #419. Reviews in-flight at Issue #419 merge-time are grandfathered UNTIL the branch's next push; any review dispatched after that push follows the full "Required when available" rule.

**Documentation-only PR exemption**: if the PR diff touches ONLY Markdown / YAML / JSON / TOML / shell (unsupported languages per STANDARDS.md "Structural Code Queries"), skip this section entirely. Document `[GRAPH: skipped — doc-only PR]` in RESULT and return PASS on graph checks. Proceed to standard Opus deep checks on the doc content.

Preconditions (code-touching PRs, run once): `bash dotfiles/scripts/sst3-code-status.sh` exits 0 and emits valid JSON. Wrapper-lane is stateless — every query re-parses on disk; there is no staleness check. If wrapper exits non-zero, skip to fallback clause below.

- [ ] Dead code detection: `bash dotfiles/scripts/sst3-code-large.sh 200 <lang>` + manual orphan scan. For each candidate: `bash dotfiles/scripts/sst3-code-callers.sh <name> <lang>` returns empty in the same module ⇒ orphan. Subagent confirms whether call is via reflection / dynamic dispatch (not an orphan) or a true orphan (cleanup target).
- [ ] Impact scope validation: `bash dotfiles/scripts/sst3-code-impact.sh <base-branch>` — enumerate all impacted modules; identify unexpected cross-boundary edges. Document each boundary: intended (defence-in-depth / architectural layering) vs emergent (refactor target). (Note: Phase A wrapper-lane does not expose `max_depth` parameter; deeper-than-1-hop scope requires subagent walk.)
- [ ] Large functions audit: confirm no function in diff exceeded 200 lines (`bash dotfiles/scripts/sst3-code-large.sh 200 <lang>`, scoped via subagent grep on diff files for `file_path_pattern` equivalent). If any did, architectural red flag — require refactor.
- [ ] **AP #19 full compliance**: includes Sonnet's over-trust spot-check, plus: any "no results" response from a wrapper in an area with unsupported-language files (YAML, JSON, SQL, shell) is explicitly broadened to subagent exploration before drawing a negative conclusion; wrapper `last_updated` timestamp recorded in RESULT.

**Fallback clause (retry-aware, evidence-required)**: first graph call fails → retry once. Second fails → RESULT MUST include the Explore-subagent's RESULT block demonstrating manual architectural audit (dead code + impact + large functions) was actually executed. Main RESULT: `[graph unavailable: <reason>] [subagent fallback: <subagent-id>]` with concrete findings. Documenting only `[graph unavailable]` without the subagent RESULT block = silent skip = FAIL.

### Overengineering Check
- [ ] Is there a simpler solution that works?
- [ ] No premature abstractions
- [ ] No unnecessary complexity
- [ ] JBGE (Just Barely Good Enough) applied

### Pre-Merge Precondition Check (NOT the post-merge user review)

> **CRITICAL**: This Opus tier runs BEFORE merge. The items below are pre-merge preconditions for posting `user-review-checklist.md` to the user. They are NOT the user review itself — that happens after merge with the actual user reading the posted checklist. Do NOT confuse the two.

- [ ] All Expected Behavior items verified (preconditions for posting checklist)
- [ ] All Acceptance Criteria items verified
- [ ] Engineering Requirements met
- [ ] Cleanup Requirements completed

### Final Verification
- [ ] All commits pushed to remote
- [ ] Branch up to date with main (**verified by reading `git log origin/main..HEAD` — do NOT run `git fetch` from this PLANNING-mode review**)
- [ ] No merge conflicts (verified via `git merge-tree` or by main agent diff inspection)
- [ ] Ready for posting user-review-checklist.md to user

### Bash Output Discipline (#406 F4.9)
- [ ] If you ran any bash command producing > 200 lines (pytest, git diff, log tail, etc.), you wrapped it with `../scripts/tee-run.sh <label> -- <cmd>`. Return only the tee path + verdict in your RESULT block; do NOT paste the full output back to the main agent.

## Pass Criteria

ALL checkboxes above verified with evidence. Graph was available and not used for structural architectural question = FAIL. If doc-only PR exempted via the short-circuit above, PASS. Unavailable / stale / unsupported-language WITH subagent RESULT block showing manual architectural audit was performed = PASS. Architectural review without structural evidence (graph-backed OR subagent-backed with RESULT block) is incomplete and fails.

## On Pass

Output: `<promise>OPUS_PASS</promise>`

## On Fail

1. List architectural concern with specific file:line
2. Explain why it violates standards
3. Suggest specific fix
4. Do NOT output promise
5. Ralph loop continues iteration
