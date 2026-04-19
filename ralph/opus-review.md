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

### Optional: Code Graph Checks (if code-review-graph available)
- [ ] Dead code detection via graph — any orphaned functions introduced by this change?
- [ ] Community detection — does the change cross architectural boundaries unexpectedly?
- [ ] Large functions audit — did the change push any function over 200 lines?

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

ALL checkboxes above verified with evidence. Code graph checks are optional — do not fail if MCP server unavailable.

## On Pass

Output: `<promise>OPUS_PASS</promise>`

## On Fail

1. List architectural concern with specific file:line
2. Explain why it violates standards
3. Suggest specific fix
4. Do NOT output promise
5. Ralph loop continues iteration
