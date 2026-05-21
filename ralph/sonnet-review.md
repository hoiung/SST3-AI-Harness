# Tier 2: Sonnet Review (Logic Checks)

> **PLANNING MODE ONLY**: You are a REVIEWER. Do NOT write code, do NOT edit files, do NOT make commits. Your ONLY job is to verify and report findings.

Medium-depth validation. Catches 30% of issues missed by Haiku.

**Completion Promise**: `<promise>SONNET_PASS</promise>`

## Checklist

### Evidence Quality / Scope Alignment
- [ ] Evidence proves completion (file paths, commits, outputs), matches actual work done, verifiable; no narrative-only "completed" checkboxes
- [ ] Quantified claims (counts, ratios, durations, capacities) backed by source (command, reference, calculation); "seems reasonable" is not a source
- [ ] **PREREQUISITE**: Read the full Issue body line-by-line BEFORE this section. The Issue body is the source of truth for scope.
- [ ] Implementation matches Issue scope exactly; no scope drift; no scope shortfall; all phases per Acceptance Criteria

### Governance — Checkbox-MCP Coverage Gate (AP #20)
- [ ] **Governance enforcement gate**: run `mcp__github-checkbox__get_issue_checkboxes` on the issue and cross-reference against phase completions. **Any phase-complete-but-checkbox-unchecked state = FAIL (AP #20 violation)**. If the tool is deferred, load via `ToolSearch(select:mcp__github-checkbox__get_issue_checkboxes)` per STANDARDS.md "MCP Tool Schema Loading". Canonical: AP #20, tool-selection-guide.md Example 2.

### Fail Fast Policy / Observability (AP #12)
- [ ] No silent fallbacks, no fake defaults, no swallowed exceptions; error messages actionable
- [ ] Every decision boundary + state transition + external call logs structured (key=value or JSON, not free-text prose); quantifiable behaviour has metrics; production/money/user-visible state changes have append-only audit trail
- [ ] No `print()` as logging; no empty `except:`, bare `pass` on exception, silent `return None` on error, or `continue` on unexpected state; logs searchable (consistent field names)

### State-Machine Mutation Correctness (Conditional, #477 AC 3.1 — Theme 3)
- [ ] **Scope**: introduces or modifies counters / flags / state enums / queues / semaphores / variables gating downstream decisions? If YES, next checkbox mandatory. If NO, mark "N/A — no state machines in scope."
- [ ] **Mutation-site audit** (if scope=YES): for every state variable, list mutation sites (`grep -n '<var>\\s*[+\\-*/]?=\\|<var>\\s*=\\s*[^=]' <file>`) and confirm exactly one mutation per logical event. Try/except: if `state += 1` occurs in try-block AND except-handler reaches same variable, confirm mutual exclusivity OR document intentional double-mutation inline. Authority duplication = FAIL.

### Test-Prod Call Coverage (Theme 9, #477 AC 3.4) — Unit Tier seam check (#484 T4.2)

> Unit Tier enforcement primitive. Canonical: STANDARDS.md "Three-Tier Testing Framework" → Unit Tier + "Test-Prod Call Coverage Discipline".

- [ ] Every new public function/method: name test file importing + invoking it (`grep -rnE 'from <new-module> import|<new-module>\\.<callable>' tests/`). Empty grep on new public callable = FAIL.
- [ ] Every new response-payload field (API/JSON/dict key): name test asserting field presence + value (`grep -rnE '<field-name>' tests/`). Field with no test = FAIL.
- [ ] Every new config key (YAML/env/dict): name test exercising read path (`grep -rnE '<config-key>' tests/`). Config read with no test = FAIL.

### Code Reuse / Codebase Hygiene
- [ ] Searched codebase before creating new modules (Glob/Grep/Explore) — **evidence required**: 2-3 grep patterns or Glob queries actually run + result counts
- [ ] No duplicate modules created; references existing modules where applicable
- [ ] No dead/obsolete/orphaned code (failed/rescoped approaches); no commented-out "old" code; no unused imports; no leftover temp/WIP patterns

### STANDARDS.md Violation Scan — Logic (per-tier escalation lens)

> Categories canonical in [`_common-culprits.md`](_common-culprits.md). Sonnet's logic lens: trace code paths for each category at trace-level depth.

- [ ] **5-culprits trace-level audit**: same calculation logic in multiple files / inline math depending on business rules / R-multiples + thresholds + retry counts + timeout values + buffer sizes in code / functions never called + imports never used + feature flags for completed features / `.get(key, {})` chains hiding missing data + empty handlers + `or default` masking config errors. For each: extract candidate? Co-located YAML config? Call graph traced? Loud failure on error path?

### Cross-Boundary Contracts (Issue #1407 post-mortem) — Trace-Level

> Logic-depth checks requiring cross-file tracing.

- [ ] **SQL/Schema**: for every new/modified SQL query: list columns in WHERE/SELECT, open migration for that table, confirm all columns exist. Trace SQL return values — if None/empty, verify WHERE literals match actual DB data. Query driving control flow has values cross-checked against DB schema.
- [ ] **Null/None propagation**: nullable parameters (`Optional[T]`) — trace every call site; guard exists IN function, not assumed from callers. Frontend null-safety: every `.toFixed()` on nullable has null check.
- [ ] **Config wiring (bidirectional)**: every new YAML/config key is read by application code (`config.get('key')`); zero-reference keys = dead config = LMCE violation.
- [ ] **Lifecycle wiring**: each recovery/drain/replay function called at EACH lifecycle entry point (startup, reconnect, restart) — verified separately, not assumed.
- [ ] **Data correction completeness**: bugs corrupting data → repair step covers ALL existing affected rows; count query confirms zero remaining bad rows.
- [ ] **Cross-function contracts**: every try/except in diff → confirm wrapped function has reachable `raise` path (sentinel returns = dead code). Hot paths: count DB round-trips, flag duplicate-table-same-row queries.

### Bash Output Discipline
> Canonical: [`_bash-output-discipline.md`](_bash-output-discipline.md). Apply checkbox here.

### AP #18 — Sample Invocation Gate (Workflow Tier validation gate, #484 T4.2)

> Workflow Tier — assembled engine runs, wiring/cross-module propagation works. Canonical: STANDARDS.md "Three-Tier Testing Framework" → Workflow Tier; AP #18.

- [ ] Scope check: touches pipeline / backtest / SL1 / SL2 / orchestration / CLI-wiring / cross-module function-arg propagation? If yes → next mandatory. If no → document scope-skip reason.
- [ ] If in-scope: real-CLI sample invocation evidence — log file path (e.g. `logs/sample_<issue>_validation.log`) OR Issue comment with exit code + DB row-count + contamination-audit verdict. Exit code 0 alone NOT sufficient (exit-0 with zero rows is a known regression). Proof: rows landed + downstream consumers succeeded.
- [ ] If in-scope: mocks use explicit `call_args.kwargs["<key>"] == <expected>` assertions — NOT `**kwargs`-swallowing mocks that pass regardless of propagation.

### E2E — System Verification Gate (E2E Tier system gate, #484 T4.2)

> E2E Tier — whole system passes a driving test end-to-end. Canonical: STANDARDS.md "Three-Tier Testing Framework" → E2E Tier; AP #26.

- [ ] Scope check: affects end-to-end system path (multiple components / cross-repo contract / orchestration / persistent-state spanning pipeline / real downstream consumer)? If yes → next mandatory. If no → "N/A — Unit/Workflow-Tier-only change".
- [ ] If in-scope: E2E/system verification evidence — exercised against real system (real DB + real downstream consumer + live invocation), not component-isolated sample. Proof: downstream consumer accepted real contract; system produced intended result end-to-end.

### Voice-Frame Preservation (semantic) — Conditional, #484 V2.2

> Distinct from lexical voice guard (`check-ai-writing-tells.py`) and from AP #18. Catches **semantic frame shift** in AI-integrated operator-supplied content (twist failure mode — AP #25 / STANDARDS.md "Polish vs Twist").

- [ ] **Scope**: diff integrates operator-supplied source content into voice-bearing prose AND `invoked_skill ∈ {blog, voice-doc-repo}`? If no → "N/A — no operator-supplied prose in-diff". If yes → next mandatory.
- [ ] **Twist check (if scope=YES)**: for each in-diff prose hunk, identify operator-supplied source phrasing; test polished output against STANDARDS.md "Polish vs Twist" TWIST-forbidden checklist (qualifier added changes interpretation / comparison reframed as verdict / hedge dropped or added / analytical lens imposed). Return PASS/FAIL **per hunk**. Any FAIL = section FAIL.

### Wrapper-Lane Checks (Required when available)

> Doc-only exemption: [`_doc-only-exemption.md`](_doc-only-exemption.md). Preconditions: [`_wrapper-lane-preconditions.md`](_wrapper-lane-preconditions.md). Fallback: [`_fallback-clause.md`](_fallback-clause.md).

- [ ] For each modified function: `bash dotfiles/scripts/sst3-code-callers.sh <function_name> <lang>` → list all call sites; verify each handles changed signature/behaviour (subagent reads each caller for intent).
- [ ] For each modified function: outgoing-call audit (callees) — `bash dotfiles/scripts/sst3-code-callees.sh <function_name> <lang>` → list every callee; verify contract handled (null-safety, config access, signature compatibility). Unsupported language → dispatch semantic subagent.
- [ ] `bash dotfiles/scripts/sst3-code-search.sh '<pattern>' <lang>` for duplicate implementations: search for new calculation/parsing/schema-handling logic — confirm not already existing.
- [ ] **Sync-lane (diff-triggered)** per [`_doc-only-exemption.md`](_doc-only-exemption.md) — run `sst3-sync-related-code.sh` / `sst3-doc-frontmatter.sh` if `docs/research/*` changed.
- [ ] **AP #19 under-use + over-trust check**: every subagent RESULT block starts with `mcp_graph_available: yes|no` per [`_wrapper-lane-preconditions.md`](_wrapper-lane-preconditions.md). If wrapper-lane used, one result spot-checked by reading source — record spot-check file:line in RESULT.

## Pass Criteria

ALL checkboxes above verified with evidence (wrapper-lane + source spot-check, OR documented fallback + subagent RESULT block per `_fallback-clause.md`). Wrapper-lane available + not used for a structural question = FAIL. Doc-only PR exempted per `_doc-only-exemption.md` = PASS. Unavailable / stale / unsupported-language WITH subagent-backed fallback evidence = PASS.

## On Pass

Output: `<promise>SONNET_PASS</promise>`

## On Fail

1. List failed items with evidence of failure
2. Specify which Fail Fast/Registry violation found
3. Do NOT output promise
4. Ralph loop continues iteration
