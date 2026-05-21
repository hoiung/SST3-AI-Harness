# Tier 3: Opus Review (Deep Analysis)

> **PLANNING MODE ONLY**: You are a REVIEWER. Do NOT write code, do NOT edit files, do NOT make commits. Your ONLY job is to verify and report findings.

Thorough architectural review. Catches 10% of issues missed by Haiku+Sonnet.

**Completion Promise**: `<promise>OPUS_PASS</promise>`

## Checklist

### Architectural Fit / STANDARDS.md Compliance
- [ ] Implementation fits existing architecture; no pattern/layer/boundary violations; integrates cleanly; no tight coupling introduced
- [ ] Fail Fast principle followed (no silent fails); no hardcoded settings (config externalized); modularity standards met; LMCE principles applied

### Governance — Checkbox-MCP Drift Audit (AP #20)
- [ ] **Governance drift audit — two-tier cadence rule**: fetch issue body via `mcp__github__get_issue` (or `mcp__github-checkbox__get_issue_checkboxes` for live state; ToolSearch-bootstrap if deferred per STANDARDS.md "MCP Tool Schema Loading") and parse `## Proof of Work` section. Cross-reference entry order + evidence against solo-branch `git log --oneline`. **Do NOT use `get_issue_events` PATCH timeline** — GitHub suppresses issue-author body edits from the timeline (false-negatives 100% of honored invocations). Classify every checked `[x]` box:
  - **Tier A — Phase-deliverable** (Acceptance Criteria Phases describing concrete deliverable: file edit, commit, function, section, table, example): **STRICT interleaving required**. PoW entry order MUST interleave with git-log commit order within same phase's commit window. Cluster-at-end = FAIL.
  - **Tier B — Cross-cutting meta** (Triple-Check Gate, Engineering Requirements meta, Cleanup Requirements, Verification Loop self-gates, PREREQUISITE CHECKPOINT, Expected Behavior post-conditions): **batched-at-end acceptable** because these describe conditions observable ONLY after all phases complete.
- [ ] **Classification heuristic**: if checkbox names specific file/commit/section/function/table to build/change → Tier A. If describes cross-cutting condition requiring WHOLE implementation to evaluate → Tier B. When in doubt: Acceptance Criteria sub-phases = Tier A; Triple-Check / Engineering Requirements meta / Cleanup / Verification Loop self-gates / PREREQUISITE / Expected Behavior = Tier B.
- [ ] **Rule**: Flag Tier A batching as AP #20 drift. Do NOT flag Tier B batching as drift. Canonical: AP #20, tool-selection-guide.md Example 2, STANDARDS.md "Governance Evidence Signal (Canonical)".

### STANDARDS.md Violation Scan — Architectural (per-tier escalation lens)

> Categories canonical in [`_common-culprits.md`](_common-culprits.md). Opus's architectural lens: deep analysis across entire implementation for each category.

- [ ] **5-culprits architectural audit**: same pattern implemented differently in multiple places / business formulas embedded in application code / settings that should be user-configurable / modules/classes never instantiated + API endpoints never called / cascading defaults masking root cause + graceful degradation hiding broken dependencies. For each: should there be a shared module? Config-First Architecture? Would changing this value require code change? If commented "for backwards compatibility" — actually needed? Errors unmistakable per Fail Fast standard?

### State-Machine Mutation Architecture (Conditional, #477 AC 3.2 — Theme 3)

> Architectural-depth state-machine review. Sonnet covers trace-level mutation-site audit; Opus adds cross-boundary architecture concerns.

- [ ] **Scope**: introduces or modifies counters / flags / state enums / queues / semaphores / locks / variables gating downstream control flow? If YES, next checkboxes mandatory. If NO, "N/A — no state machines in architectural scope."
- [ ] **Mutation-path architecture audit** (if scope=YES): enumerate ALL writers across diff + adjacent modules (`grep -rnE '<var>\\s*[+\\-*/]?=' src/`). Verify exactly ONE module owns transition authority. Multi-writer states = architectural red flag unless documented as intentional fan-in (with concurrency model named: lock / atomic / single-thread / actor / message-bus).
- [ ] **Authority-duplication detection** (if scope=YES): for any try/except pair, confirm success-path and error-path are mutually exclusive on state writes. Double-mutation in try-block AND except-handler = bug class (Issue #1448 evidence). Confirm exactly-once semantics OR document intentional double-write inline.
- [ ] **Concurrent-safety check** (if scope=YES + state crosses thread/process/coroutine boundary): named concurrency primitive present (asyncio.Lock / threading.Lock / DB row-lock / atomic op). If absent, racy by construction = FAIL.

### Cross-Boundary Contract Audit — Architectural (Issue #1407 post-mortem)

> Deep cross-system reasoning. Every value crossing a boundary (code↔DB, code↔config, caller↔callee, backend↔frontend) must have its contract verified.

- [ ] **SQL/Schema architecture**: all SQL in diff audited against DB schema (migrations/) — column names, types, table existence verified. No query references renamed/removed/never-added columns. SQL literal values cross-referenced against actual DB data (normalization-mismatch check).
- [ ] **Null propagation architecture**: identify all values that can be None (DB results, API responses, optional config); trace to consumption points; arithmetic/method-call/formatting sites guarded. Frontend data contract: API response fields displayed in UI handle null/undefined at display layer. Type annotations match reality (`float` annotation → no caller can pass `None`).
- [ ] **Config architecture (bidirectional)**: (1) code has no hardcoded values → config exists; (2) config has no orphaned keys → code consumes them. New config section: feature's code reads EVERY key in that section.
- [ ] **Lifecycle wiring architecture**: each recovery/drain/replay function mapped to ALL lifecycle events where data could accumulate; wired to every one. "Called at reconnect" ≠ "called at startup".
- [ ] **Scope completeness**: enumerate every Acceptance Criteria checkbox from issue body — each maps to specific file:line. Any without = NOT DONE.
- [ ] **Data correction architecture**: bug producing bad DB state → fix includes BOTH (a) code fix for future AND (b) verified data repair for existing rows.

### Factual Claims Audit
- [ ] Enumerate all numeric assertions in documentation, issue body, design rationale; verify each has source (benchmark, prior issue, measured observation, command output). No source = flag as unverified — must be sourced or removed before OPUS_PASS.

### Wrapper-Lane Architectural Depth Checks

> Doc-only exemption: [`_doc-only-exemption.md`](_doc-only-exemption.md). Preconditions: [`_wrapper-lane-preconditions.md`](_wrapper-lane-preconditions.md). Fallback: [`_fallback-clause.md`](_fallback-clause.md).

- [ ] **Dead code detection**: `bash dotfiles/scripts/sst3-code-large.sh 200 <lang>` + manual orphan scan. For each candidate: `bash dotfiles/scripts/sst3-code-callers.sh <name> <lang>` returns empty in same module ⇒ orphan. Subagent confirms whether reflection/dynamic dispatch (not orphan) vs true orphan (cleanup target).
- [ ] **Impact scope validation**: `bash dotfiles/scripts/sst3-code-impact.sh <base-branch>` — enumerate all impacted modules; identify unexpected cross-boundary edges. Document each boundary: intended (defence-in-depth / architectural layering) vs emergent (refactor target). Phase A wrapper-lane does not expose `max_depth`; deeper-than-1-hop requires subagent walk.
- [ ] **Large functions audit**: confirm no function in diff exceeded 200 lines (`sst3-code-large.sh 200 <lang>` scoped via subagent grep on diff files). If any did → architectural red flag, require refactor.
- [ ] **AP #19 full compliance**: includes Sonnet's over-trust spot-check, plus: any "no results" response in area with unsupported-language files (YAML, JSON, SQL, shell) explicitly broadened to subagent exploration before drawing negative conclusion; wrapper `last_updated` recorded in RESULT.

### Overengineering Check
- [ ] Simpler solution that works? No premature abstractions; no unnecessary complexity; JBGE (Just Barely Good Enough) applied.

### Pre-Merge Precondition Check (NOT the post-merge user review)

> **CRITICAL**: This Opus tier runs BEFORE merge. The items below are pre-merge preconditions for posting `user-review-checklist.md` to the user. They are NOT the user review itself.

- [ ] All Expected Behavior items verified (preconditions for posting checklist)
- [ ] All Acceptance Criteria items verified — **Stage 5 re-litigates any deferred items via the §3-Deferral Re-Litigation Angle per Leader.md Stage 5 step 1 (#477 AC 2.7)**. Items left in user-review-checklist §3 "Items Not Fixed" without one of three flags `[deferred-FP|N/A|tracking-issue]` will be re-classified by the Stage 5 angle; bidirectional cross-reference with user-review-checklist.md §3 3-flag taxonomy.
- [ ] Engineering Requirements met; Cleanup Requirements completed

### Final Verification
- [ ] All commits pushed to remote; branch up to date with main (verified by reading `git log origin/main..HEAD` — do NOT run `git fetch` from this PLANNING-mode review); no merge conflicts (verified via `git merge-tree` or main-agent diff inspection); ready for posting user-review-checklist.md.

### Bash Output Discipline
> Canonical: [`_bash-output-discipline.md`](_bash-output-discipline.md). Apply checkbox here.

## Pass Criteria

ALL checkboxes above verified with evidence. Wrapper-lane was available and not used for structural architectural question = FAIL. Doc-only PR exempted per [`_doc-only-exemption.md`](_doc-only-exemption.md) = PASS. Unavailable / stale / unsupported-language WITH subagent RESULT block showing manual architectural audit was performed per [`_fallback-clause.md`](_fallback-clause.md) = PASS. Architectural review without structural evidence (wrapper-backed OR subagent-backed with RESULT block) is incomplete and fails.

## On Pass

Output: `<promise>OPUS_PASS</promise>`

## On Fail

1. List architectural concern with specific file:line
2. Explain why it violates standards
3. Suggest specific fix
4. Do NOT output promise
5. Ralph loop continues iteration
