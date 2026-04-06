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
- [ ] If you ran any bash command producing > 200 lines (pytest, git diff, log tail, etc.), you wrapped it with `../dotfiles/SST3/scripts/tee-run.sh <label> -- <cmd>`. Return only the tee path + verdict in your RESULT block; do NOT paste the full output back to the main agent.

## Pass Criteria

ALL checkboxes above verified with evidence.

## On Pass

Output: `<promise>HAIKU_PASS</promise>`

## On Fail

1. List failed items with file:line references
2. Do NOT output promise
3. Ralph loop continues iteration
