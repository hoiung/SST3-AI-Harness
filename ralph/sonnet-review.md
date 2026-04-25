# Tier 2: Sonnet Review (Logic Checks)

> **PLANNING MODE ONLY**: You are a REVIEWER. Do NOT write code, do NOT edit files, do NOT make commits. Your ONLY job is to verify and report findings.

Medium-depth validation. Catches 30% of issues missed by Haiku.

**Completion Promise**: `<promise>SONNET_PASS</promise>`

## Checklist

### Evidence Quality
- [ ] Evidence proves completion (not just claims)
- [ ] Evidence matches actual work done
- [ ] Evidence is verifiable (file paths, commits, outputs)
- [ ] No "completed" checkboxes without evidence
- [ ] Any quantified claim (counts, ratios, durations, capacities) in documentation or issue body: source identified (command, reference, or calculation). "Seems reasonable" is not a source.
- [ ] No numbers copied from other documents without re-verification against current state

### Scope Alignment
- [ ] **PREREQUISITE: Read the full Issue body line-by-line BEFORE this section.** Don't skim. Don't trust prior summaries. The Issue body is the source of truth for scope.
- [ ] Implementation matches Issue scope exactly
- [ ] No scope drift (adding unrequested features)
- [ ] No scope shortfall (missing requested features)
- [ ] All phases completed per Acceptance Criteria

### Governance — Checkbox-MCP Coverage Gate (AP #20)
- [ ] **Governance enforcement gate**: run `mcp__github-checkbox__get_issue_checkboxes` on the issue and cross-reference against phase completions. **Any phase-complete-but-checkbox-unchecked state = FAIL (AP #20 violation)**. If the tool is deferred, load via `ToolSearch(select:mcp__github-checkbox__get_issue_checkboxes)` per `../standards/STANDARDS.md` "MCP Tool Schema Loading" — bootstrap before running the gate. Rule: `../standards/ANTI-PATTERNS.md` **AP #20**; canonical evidence patterns: `../reference/tool-selection-guide.md` Example 2.

### Fail Fast Policy
- [ ] No silent fallbacks (errors fail loudly)
- [ ] No fake defaults (missing config = error, not default)
- [ ] No swallowed exceptions
- [ ] Error messages are actionable

### Observability (AP #12 — STANDARDS.md "Observability")
- [ ] Every decision boundary has a structured log (key=value or JSON, not free-text prose)
- [ ] Every state transition logs before/after values and trigger
- [ ] Every external call (DB/API/file/subprocess) logs inputs, duration, outcome
- [ ] Quantifiable behaviour has metrics (counters, durations, success/failure ratios)
- [ ] State changes touching production data / money / user-visible behaviour have an append-only audit trail (actor + timestamp + reason)
- [ ] No `print()` as logging strategy (use structured logger)
- [ ] No empty `except:` blocks, bare `pass` on exception, silent `return None` on error, or `continue` on unexpected state
- [ ] Logs are searchable (consistent field names, no log-and-pray)

### Code Reuse
- [ ] Searched codebase before creating new modules (Glob/Grep/Explore) — **evidence required**: name 2-3 grep patterns or Glob queries actually run, with results count
- [ ] No duplicate modules created
- [ ] References existing modules where applicable

### Codebase Hygiene
- [ ] No dead code (unreachable, never-called functions)
- [ ] No obsolete code (deprecated, superseded by new implementation)
- [ ] No orphaned code (from failed/rescoped approaches)
- [ ] No commented-out "old" code blocks
- [ ] No unused imports/dependencies
- [ ] No leftover temp/WIP patterns

### STANDARDS.md Violation Scan (Logic)

> Trace code paths for the 5 common culprits. Category names + framing canonical in [`_common-culprits.md`](_common-culprits.md) (#406 F3.4).

**1. Duplicate Code (DRY/Modularity)**
- [ ] No same calculation logic in multiple files
- [ ] No repeated parsing/formatting patterns
- [ ] Check: Could this be extracted to shared utility?

**2. On-the-fly Calculations (Hardcoded Settings)**
- [ ] No inline math that depends on business rules (e.g., `price * 1.1` for markup)
- [ ] No date/time calculations with hardcoded offsets
- [ ] Check: Should this formula be in config YAML?

**3. Hardcoded Settings**
- [ ] No R-multiples, percentages, thresholds in code
- [ ] No retry counts, timeout values, buffer sizes
- [ ] Check: Is there a co-located YAML config this should be in?

**4. Obsolete/Dead Code (LMCE)**
- [ ] No functions that are never called (trace call graph)
- [ ] No imports that are never used
- [ ] No feature flags for completed/removed features

**5. Silent Fallbacks (Fail Fast)**
- [ ] No `.get(key, {})` chains that hide missing data
- [ ] No `try/except: pass` or `catch(e) { }` empty handlers
- [ ] No `or default` that masks configuration errors
- [ ] Check: Does error path fail loudly with actionable message?

**6. Cross-Boundary Contracts — Trace-Level (Issue #1407 post-mortem)**

> Logic-depth checks requiring cross-file tracing. These catch the bugs that syntactic scans miss.

**SQL/Schema Contracts**
- [ ] For every new/modified SQL query: list columns in WHERE/SELECT, open the migration for that table, confirm all columns exist
- [ ] Trace SQL query return values — if a query returns None/empty, verify the WHERE literal values match actual DB data (e.g., `side='SELL'` not `side='SLD'` if DB normalizes on insert)
- [ ] Any query driving control flow (`if result:` / `if not result:`) has its column values cross-checked against DB schema

**Null/None Propagation**
- [ ] For functions with nullable parameters (`Optional[T]` or `T | None`): trace every call site — are callers guaranteed non-None, or must the function guard internally?
- [ ] Any function called at 2+ locations with a nullable input: verify the guard exists IN the function, not assumed from callers
- [ ] Frontend null-safety: trace API fields that can be null through to display/formatting — every `.toFixed()` on a nullable must have a null check

**Config Wiring (Bidirectional)**
- [ ] For every new YAML/config key: verify it is read by application code (grep key name → `config.get('key')` or `config['key']`)
- [ ] Config keys with zero code references = dead config = LMCE violation. Remove or wire.

**Lifecycle Wiring**
- [ ] For each recovery/drain/replay function: list ALL lifecycle entry points (startup, reconnect, restart) and verify it is called at EACH one
- [ ] "Called at reconnect" does NOT imply "called at startup" — verify separately

**Data Correction Completeness**
- [ ] For bugs that corrupt/mis-set data: verify a repair step exists covering ALL existing affected rows, not just future ones
- [ ] Run count query to confirm zero remaining bad rows after repair

**Cross-Function Behavioral Contracts**
- [ ] For every try/except in the diff: open the wrapped function and confirm it has a reachable `raise` path. If it returns sentinel values (None, False), the try/except is dead code.
- [ ] Hot paths (fill handlers, order processors): count DB round-trips — flag any path querying the same row more than once

### Bash Output Discipline (#406 F4.9)
- [ ] If you ran any bash command producing > 200 lines (pytest, git diff, log tail, etc.), you wrapped it with `../scripts/tee-run.sh <label> -- <cmd>`. Return only the tee path + verdict in your RESULT block; do NOT paste the full output back to the main agent.

### AP #18 — Sample Invocation Gate (workflow validation)
- [ ] Scope check: does this change touch pipeline / data-processing / orchestration / CLI-wiring / cross-module function-arg propagation? If **yes** → the next checkbox is mandatory. If **no** → document the scope-skip reason here.
- [ ] If in-scope: evidence of a real-CLI sample invocation exists — either a log file path, or an Issue comment with exit code + row-count + audit verdict. Exit code 0 alone is NOT sufficient (history of exit-0 runs writing zero rows). The proof must show rows landed + downstream consumers succeeded.
- [ ] If in-scope: any mock used in the fix's tests uses explicit `call_args.kwargs["<key>"] == <expected>` assertions — NOT a `**kwargs`-swallowing mock that would pass regardless of whether the code actually propagated the arg.

### Required when graph available: Code Graph Checks

**Rollout note**: this check became required with Issue #419. Reviews in-flight at Issue #419 merge-time are grandfathered UNTIL the branch's next push; any review dispatched after that push follows the full "Required when available" rule.

**Documentation-only PR exemption**: if the PR diff touches ONLY Markdown / YAML / JSON / TOML / shell (unsupported languages per STANDARDS.md "Structural Code Queries"), skip this section entirely. Document `[GRAPH: skipped — doc-only PR]` in RESULT and return PASS on graph checks. Proceed to standard Sonnet logic checks on the doc content.

Preconditions (code-touching PRs, run once): `config status` returns `file_count > 0` AND `last_updated < 24h`. If either fails, skip to fallback clause below.

- [ ] For each modified function: `graph query callers_of(<function_name>)` → list all call sites; verify each handles the changed signature / behaviour (subagent reads each caller to verify intent — graph narrows, subagent confirms).
- [ ] For each modified function: `graph query callees_of(<function_name>)` → confirm no newly-called functions have incompatible contracts (null-safety, config access).
- [ ] `graph query search(pattern)` for duplicate implementations: search for new calculation / parsing / schema-handling logic in codebase — confirm it doesn't already exist.
- [ ] **AP #19 under-use + over-trust check**: (a) **under-use**: every subagent RESULT block discussing graph queries starts with `mcp_graph_available: yes|no` (AP #19 "Subagent MCP access" bullet — semantics: LAST call's outcome, NOT start-of-subagent probe; mid-stream `MCP error -32000: Connection closed` flips `yes` → `no`, see #444). If `yes` + no graph-query evidence line = FAIL (lazy fallback). If `no` + grep fallback evidence = PASS (acceptable — subagent had no MCP access OR transport disconnected mid-stream; either way fallback evidence is the requirement). (b) **over-trust**: if graph was used, one result spot-checked by reading source — record the spot-check file:line in the RESULT block.

**Fallback clause (retry-aware, evidence-required)**: if first graph call fails, retry once. If second fails, the RESULT block MUST include the Explore-subagent's RESULT block demonstrating manual call-graph audit was actually executed (e.g. "Layer 1 subagent checked 5 call sites, 3 caller contracts verified compatible, 2 flagged for semantic review"). Main RESULT references it as `[graph unavailable: <reason>] [subagent fallback: <subagent-id>]`. Documenting only `[graph unavailable]` without the subagent RESULT block = silent skip = FAIL.

## Pass Criteria

ALL checkboxes above verified with evidence (graph-backed + source spot-check, OR documented fallback + subagent RESULT block showing manual audit was performed). If graph was available (per definition above) and not used for a structural question, FAIL. If doc-only PR exempted via the short-circuit above, PASS. If unavailable / stale / unsupported-language WITH subagent-backed fallback evidence = PASS.

## On Pass

Output: `<promise>SONNET_PASS</promise>`

## On Fail

1. List failed items with evidence of failure
2. Specify which Fail Fast/Registry violation found
3. Do NOT output promise
4. Ralph loop continues iteration
