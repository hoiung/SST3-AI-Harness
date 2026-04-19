# Tier 1: Haiku Review (Surface Checks)

> **PLANNING MODE ONLY**: You are a REVIEWER. Do NOT write code, do NOT edit files, do NOT make commits. Your ONLY job is to verify and report findings.

Fast, cheap surface validation. Catches 60% of issues.

**Completion Promise**: `<promise>HAIKU_PASS</promise>`

## Checklist

### File Structure
- [ ] All new files in correct locations per STANDARDS.md
- [ ] No temp files committed (**"temp file" = anything under `temp/`, `C:/temp/`, `$SST3_TEMP/`, or matching `*.tmp`/`*.bak`**)
- [ ] Files named per conventions

### Checkboxes
- [ ] All "Expected Behavior" checkboxes have evidence
- [ ] All "Acceptance Criteria" checkboxes have evidence
- [ ] No unchecked mandatory checkboxes

### Commits (current branch only — don't audit pre-branch history)
- [ ] All commits on the current solo branch reference issue number (#X)
- [ ] Commit format: `type: description (#issue)`
- [ ] No "WIP" or "temp" commits

### Debug Code
- [ ] No console.log statements
- [ ] No print() debug statements
- [ ] No debug flags left enabled
- [ ] No commented-out old code

### STANDARDS.md Violation Scan (Surface)

> Scan for obvious violations of the 5 common culprits. Category names + framing canonical in [`_common-culprits.md`](_common-culprits.md) (#406 F3.4).

**1. Duplicate Code (DRY/Modularity)**
- [ ] No copy-pasted code blocks visible
- [ ] No repeated function signatures with same logic

**2. On-the-fly Calculations (Hardcoded Settings)**
- [ ] No magic numbers in calculations (e.g., `* 0.5`, `+ 100`)
- [ ] No inline formulas that should be in config

**3. Hardcoded Settings**
- [ ] No embedded URLs, paths, credentials
- [ ] No hardcoded thresholds, limits, timeouts

**4. Obsolete/Dead Code (LMCE)**
- [ ] No commented-out code blocks
- [ ] No TODO/FIXME referencing old approaches

**5. Silent Fallbacks (Fail Fast)**
- [ ] No `catch` blocks that swallow errors silently
- [ ] No `|| default` patterns hiding missing config (**legitimate optional defaults — argparse `default=`, function default args for non-required tunables — are NOT violations; only flag patterns hiding required config**)

**6. Cross-Boundary Contracts (Issue #1407 post-mortem)**

> Surface checks for code that touches DB, config, or other functions

- [ ] SQL WHERE clauses use values matching actual DB enum/column values (e.g., `'SELL'` not `'SLD'` if DB normalizes)
- [ ] New SQL queries only reference columns that exist in the target table (cross-check migration file)
- [ ] New config YAML keys are consumed by code (grep key name — must appear in at least one `.get()` or `[]` access)
- [ ] Function parameters that can be None/null are guarded before arithmetic, `.toFixed()`, `float()`, or `Decimal()`
- [ ] JS/React: no `.toFixed()` or `Number()` called on values that can be null without a null guard
- [ ] Recovery/replay/drain functions are wired to ALL lifecycle events (startup AND reconnect) — not just one
- [ ] try/except blocks: the wrapped function can actually raise (check its implementation — if it returns sentinel values, try/except is dead code)
- [ ] No duplicate DB queries within the same function (same table + same WHERE hit twice without mutation between)
- [ ] If fix addresses a data bug: existing bad data rows also repaired (not just future data fixed)

### Bash Output Discipline (#406 F4.9)
- [ ] If you ran any bash command producing > 200 lines (pytest, git diff, log tail, etc.), you wrapped it with `../scripts/tee-run.sh <label> -- <cmd>`. Return only the tee path + verdict in your RESULT block; do NOT paste the full output back to the main agent.

### Preferred: Code Graph Checks (run when graph available and fresh)

**Rollout note**: "Preferred" became the wording with Issue #419. Reviews in-flight at Issue #419 merge-time are grandfathered UNTIL the branch's next push; any review dispatched after that push follows the full wording below.

**Documentation-only PR exemption** (run FIRST — short-circuits the rest of this section): if the PR diff touches ONLY documentation / non-code files (Markdown, YAML, JSON, TOML, shell scripts, other unsupported languages per STANDARDS.md "Structural Code Queries"), skip this entire section. Document the skip reason in RESULT: `[GRAPH: skipped — doc-only PR]`. Proceed to standard Haiku surface checks. This is a PASS path, not a fallback.

Preconditions (code-touching PRs, run once per review): `config status` returns `total_nodes > 0` and `last_updated` within 24 h. If either fails, skip to the fallback clause below.

- [ ] `graph query large_functions(min_lines=100)` — any new/modified function approaching 200 lines?
- [ ] `graph query impact(changed_files)` — any unexpected downstream impacts in callers?
- [ ] Orphaned-function scan: for each modified function, `graph query callers_of(<name>)` — zero callers in the same module = orphan candidate (subagent confirms intent).

**Fallback clause (retry-aware, evidence-required)**: if first graph call fails, retry once. If second fails, or graph is stale / unsupported-language, the RESULT block MUST include ONE of:
- (A) Graph evidence: `last_updated`, number of results per query, spot-check source file:line; OR
- (B) Subagent-fallback evidence: an Explore subagent's RESULT block showing the manual call-graph / orphan audit was actually performed, referenced in main RESULT as `[subagent fallback: Explore / <subagent-id>]` with concrete findings (e.g. "checked 5 call sites, all compatible").
Documenting "[graph unavailable]" without EITHER (A) or (B) is a silent skip = FAIL. A documented fallback WITH subagent evidence = PASS.

## Pass Criteria

ALL checkboxes above verified with evidence (structural via graph where supported, semantic/fallback via subagent). RESULT block documents graph-call outputs + any fallback reasons. Silent skip of graph checks when graph was available = FAIL. Doc-only PR exemption via the short-circuit above = PASS.

## On Pass

Output: `<promise>HAIKU_PASS</promise>`

## On Fail

1. List failed items with file:line references
2. Do NOT output promise
3. Ralph loop continues iteration
