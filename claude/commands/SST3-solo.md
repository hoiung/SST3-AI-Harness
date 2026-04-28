# SST3-Solo Mode

## Mandatory Reading

Read these files in order BEFORE starting:
1. `../standards/STANDARDS.md` (entire file)
2. Current repository's `CLAUDE.md` (entire file)
3. `../workflow/WORKFLOW.md` (entire file — defines the 5-stage workflow)

## Governance Enforcement — Checkbox MCP (AP #20)

At every Acceptance Criteria checkbox completion → invoke:

```python
mcp__github-checkbox__update_issue_checkbox(
    issue_number=<N>,
    checkbox_text="<exact text without [ ] prefix>",
    evidence="<concise proof: what you did + key results>"
)
```

Comment-only progress tracking is NOT a substitute — it leaves the issue body (the permanent contract) empty of per-criterion evidence. See **AP #20** in `../standards/ANTI-PATTERNS.md`.

**Deferred-tool loading is mandatory, not conditional**: check the deferred-tool list at session start; if `mcp__github-checkbox__*` tools appear there, load their schemas via `ToolSearch(select:mcp__github-checkbox__update_issue_checkbox,mcp__github-checkbox__get_issue_checkboxes,mcp__github-checkbox__health_check,mcp__github-checkbox__get_issue_events,mcp__github-checkbox__list_issue_comments,mcp__github-checkbox__update_issue_comment)` BEFORE any governance work. Full rule (including generic pattern for any deferred MCP tool): STANDARDS.md "MCP Tool Schema Loading".

**Evidence-quality patterns**: canonical table in `../reference/tool-selection-guide.md` Example 2.

## Per-Session Initialization

On each SST3-solo invocation, run this block ONCE (not per subagent dispatch).

**Per-Stage Feedback Capture (canonical: STANDARDS.md §Per-Stage Feedback Capture)**: at session start, if a feedback file exists for the in-flight Issue (per the `solo/issue-N-*` branch), the agent reads any prior `## Stage <N>` blocks to recover stage-level context after compact. Reconstruction-marker convention applies for stages where observations cannot be recovered.

**Graph availability check** — only if `code-review-graph` is registered in `~/.claude.json`.

Registration detection (explicit, not try/except): run
`grep -q '"code-review-graph"' ~/.claude.json && echo registered || echo unregistered`
- If `unregistered`: log `[GRAPH] Server not registered; skipping pre-session check. Downstream graph calls (WORKFLOW Stage 1, Ralph) will skip with documented fallback.` and continue to main SST3-solo work.
- If `registered`: proceed with the graph check below.

Wrapper-lane check (registered case):
0. **Self-test BEFORE status (#447 Phase 5)**: run `bash dotfiles/scripts/sst3-self-test.sh` first. ANY drift line in the NDJSON (`{"kind":"fixture-drift",...}`) means a wrapper has regressed against its frozen known-answer fixture. Log `[WRAPPER-LANE self-test drift: <fixture-list>]` and HALT — open `solo/wrapper-fix-<bug>` (NOT this session's branch), reproduce + fix, push fix branch through its own Stage 4, then resume the original session. Engine-missing (exit 127) on the dev host degrades to subagent-only fallback for THIS session, same as wrapper-lane unavailable below. The self-test gate is the regression contract; status check alone cannot catch wrapper drift because status's NDJSON contract is too narrow (single object).
1. Run `bash dotfiles/scripts/sst3-code-status.sh`. If the call exits non-zero, log `[WRAPPER-LANE] status check failed: <stderr>; retrying once.` and retry once. If second attempt fails, log `[WRAPPER-LANE unavailable: wrapper call failed after retry]` and continue — downstream will fall back to subagent with documented evidence. Common failure: exit 127 (inner engine like ast-grep not installed; see playbook Install section). **Post Issue #456**: exit 127 means the engine is genuinely missing on disk. Pre-#456 the same code ALSO fired when the engine was on disk but PATH was not propagated to non-interactive shells; that case is closed by `sst3-bash-utils.sh` self-bootstrap. Run `scripts/install.sh` to install missing engines — do NOT add custom PATH workarounds in the calling agent.
2. There is no build step — the wrapper-lane is stateless; every query re-parses on disk.
3. There is no staleness check — `last_updated` is the repo HEAD commit time, not a query-cache freshness indicator.
4. **End-to-end smoke** (G-4 fix, #444): after status check succeeds, run a tiny `bash dotfiles/scripts/sst3-code-search.sh '<symbol>' <lang>` against a known-good symbol from the active repo to confirm the round-trip works. Symbol-selection: see canonical shell snippet at `../dotfiles/docs/guides/code-query-playbook.md` "Stage-Mapped Recipes — Stage 1 — symbol-extraction snippet". If the smoke fails with non-zero exit, log `[WRAPPER-LANE smoke test failed: <stderr>]`, fall back to subagent for THIS session.

Cadence: this check runs ONCE per SST3-solo invocation, not per subagent dispatch. The wrapper-lane is request-scoped; there is no daemon to keep fresh. See `../dotfiles/docs/guides/code-query-playbook.md` for operational notes.

**github-checkbox availability check** — only if `github-checkbox` is registered in `~/.claude.json`.

Registration detection (explicit): run
`grep -q '"github-checkbox"' ~/.claude.json && echo registered || echo unregistered`
- If `unregistered`: log `[CHECKBOX] Server not registered; skipping availability check. Governance work MAY proceed without MCP invocation only if the skill being invoked does NOT contain AP #20 directives; otherwise STOP.` and continue.
- If `registered`: proceed with the checkbox check below.

Checkbox availability check (registered case):
1. Load schema: `ToolSearch(query="select:mcp__github-checkbox__health_check,mcp__github-checkbox__get_issue_checkboxes,mcp__github-checkbox__update_issue_checkbox,mcp__github-checkbox__get_issue_events,mcp__github-checkbox__list_issue_comments,mcp__github-checkbox__update_issue_comment")` — mandatory pre-bootstrap per `../standards/STANDARDS.md` "MCP Tool Schema Loading".
2. Call `mcp__github-checkbox__health_check`. On error, log `[CHECKBOX] health_check failed: <error>; retrying once.` and retry once. If second attempt fails, log `[CHECKBOX unavailable: ...]` and **HARD STOP** — do not proceed with governance-sensitive work under any circumstances. This is fail-fast by design (AP #20 + STANDARDS.md "MCP Tool Schema Loading"). Layer 1 (phase-boundary close-out in "During Work") + Layer 2 (Pre-Verification-Loop baseline in "Verification Loop") both REQUIRE this bootstrap to have succeeded — if the bootstrap STOPs, those layers MUST NOT run. There is no "proceed with warning" path.

Cadence: once per SST3-solo invocation, same as graph check.

This is the structural-query layer (graph) + governance-signal layer (github-checkbox); the subagent swarm remains your semantic layer. Rule detail for graph lives in STANDARDS.md "Structural Code Queries"; rule detail for checkbox-MCP bootstrap lives in STANDARDS.md "MCP Tool Schema Loading" + "Governance Evidence Signal (Canonical)".

## Solo Mode Summary

**Purpose**: All SST3 workflow tasks — 5-stage sequential process with subagent swarms for research/review, main agent for implementation.

**Context Window**: 1M tokens (Opus 4.6/Sonnet 4.6), 200K (Haiku 4.5)
**Content Budget**: ~42K tokens (STANDARDS.md + CLAUDE.md + Issue loaded at session start)
**Handover at**: 80% of model window

## 5-Stage Sequential Workflow

**ORDER-DEPENDENT** — race conditions if reordered. No skimming, no pretending, no bypassing.

**Subagents** = research/explore/audit/verify/review (NEVER code)
**Main agent** = collate, write /tmp, create issues, implement, commit, merge

### Stage 1 — Research (Subagent Swarm → /tmp)
- Launch MANY parallel subagents (5 files max each)
- Main context = orchestrator only — NEVER read source files directly
- Research phase <30% of context budget
- Main agent collates findings → writes /tmp file: **findings + gaps + plan**
- Check `docs/research/` for existing research first

### Stage 2 — Issue Creation (Main Agent from /tmp)
- Create issue using `issue-template.md` from /tmp research
- Add ALL before/after illustrations, compact breaks between phases
- Subagents for scope-check vs audit
- Quality mantras VERBATIM: no inefficiencies, fix optimisations, reliable/robust, dedupe, no bottlenecks, fast/safe, no memory leaks, follows STANDARDS.md
- No false positives. No priority levels. All must be fixed.

### Stage 3 — Triple-Check (Subagents Verify Scope)
- Scope vs audit = 100% captured, no gaps, no overengineering
- Check against chat history — don't forget agreed items
- Check for dead/obsolete/legacy code cleanup
- Verify not scoping the opposite of what was agreed
- All scope in issue BODY — never comments

### Stage 4 — Implementation + Merge + User Review
- Implement all phases, commit per file
- Verification Loop (repeat until clean)
- Ralph Review: Haiku → Sonnet → Opus (all 3 mandatory)
- Merge to main BEFORE user review (Solo Branch Merge Safety: pull, diff, preserve both)
- POST user-review-checklist.md from TEMPLATE (ALL sections mandatory)
- Fix gaps — no deferrals, no excuses unless confirmed false positive

### Stage 5 — Post-Implementation Review (Subagent Swarm)
- Phase-by-phase review against issue body scope, goal alignment, design doc
- Wiring check: everything connected to existing functions?
- Inefficiencies, dead code, optimisations, dedupe, bottlenecks, memory leaks
- STANDARDS.md compliance. Issue body 100% complete.
- Fix ALL problems. Run regression tests.

## Task Description

Describe the task you need to complete:

[User will provide task description here]

## Execution Guardrails (Built-in)

### Before Starting Work
- [ ] Read CLAUDE.md in full
- [ ] Read STANDARDS.md in full
- [ ] Read Issue line-by-line (not skim)
- [ ] Create solo branch: `git checkout -b solo/issue-{number}-{description}`
- [ ] **HARD STOP**: NEVER switch branches mid-implementation

### During Work (At Each Phase Checkpoint)
- [ ] Post checkpoint to Issue comment
- [ ] **Close Tier A checkboxes via MCP** (AP #20 Layer 1 — MANDATORY in execute mode only, before moving to next phase): for every completed Tier A Acceptance Criteria in the just-finished phase, invoke `mcp__github-checkbox__update_issue_checkbox(issue_number, checkbox_text, evidence)` with canonical evidence (file:line / commit hash / command+output / subagent RESULT comment-id per `../reference/tool-selection-guide.md` Example 2). ToolSearch-bootstrap if deferred: `ToolSearch(query="select:mcp__github-checkbox__update_issue_checkbox,mcp__github-checkbox__get_issue_checkboxes")`. No phase boundary may be crossed with a Tier A `[ ]` box behind. See `../dotfiles/.claude/commands/Leader.md` Stage 4 step 3a for the full rule.
- [ ] Check context memory: If 80%+ used, warn user. If 90%+, STOP.
- [ ] Commit after EACH file change — NEVER use `git add -A`

### After Compact (Context Recovery)
- [ ] Re-read CLAUDE.md
- [ ] Re-read STANDARDS.md
- [ ] Re-read Issue (or last checkpoint comment)
- [ ] Continue from last checkpoint

## Verification Loop (MANDATORY)

**Layer 2 — Pre-Verification-Loop baseline (MANDATORY)**: if the tool is deferred, `ToolSearch(query="select:mcp__github-checkbox__get_issue_checkboxes,mcp__github-checkbox__update_issue_checkbox")` first. Then run `mcp__github-checkbox__get_issue_checkboxes` and confirm every Tier A phase-complete box is `[x]` with canonical evidence (file:line / commit / command / subagent RESULT per `../reference/tool-selection-guide.md` Example 2). Close any lingering `[ ]` box NOW via `update_issue_checkbox` with canonical evidence — do NOT defer to the loop below. The loop enters from a clean baseline. (Complements Layer 1 at phase-boundary; the expanded bullet below is Layer 3 final-check.)

Repeat until ALL pass:
- [ ] **Layer 3 — All Tier A checkboxes closed via MCP with canonical evidence**: (1) `ToolSearch(query="select:mcp__github-checkbox__get_issue_checkboxes,mcp__github-checkbox__update_issue_checkbox")` if deferred; (2) run `mcp__github-checkbox__get_issue_checkboxes`; (3) for each Tier A `[ ]`-but-done box, invoke `update_issue_checkbox(issue_number, exact_checkbox_text, evidence)` with canonical evidence (file:line / commit / command / subagent RESULT comment-id per `../reference/tool-selection-guide.md` Example 2); (4) re-run `get_issue_checkboxes`, confirm all Tier A `[x]`. Tier B batched-closures applied here are acceptable per AP #20 Phase 9 cadence. (`../workflow/WORKFLOW.md` is canonical — Verification Loop rule lives there; procedure expanded here per skill-execution requirement, not duplicated.)
- [ ] **Per-stage feedback gate** (canonical: STANDARDS.md §Per-Stage Feedback Capture): every `/Leader` stage executed within this session has its `## Stage <N>` block written to the per-issue feedback file with all 10 fields populated (or with documented `[reconstructed-post-compact: ...]` markers + `reconstructed_stages: [N]` frontmatter). Pre-commit hook `sst3-metrics-feedback-present` is the enforcing layer — if the hook fires loud during commit, the file is incomplete; fix and re-stage.
- [ ] Overengineering check: simpler solution exists?
- [ ] Architecture reuse check: duplicated instead of reused?
- [ ] Code duplication check: needs deduplication?
- [ ] Fallback policy check: silent failures?
- [ ] **Wiring check**: All changed code actually called by existing functions/processes? Structural layer: `bash dotfiles/scripts/sst3-code-callers.sh <function> <lang>` + `bash dotfiles/scripts/sst3-code-impact.sh <base-branch>` when graph available (per STANDARDS.md "Structural Code Queries" pre-query gate). Semantic layer: subagent verifies each caller handles the new contract. YAML / shell / unsupported-language keys still grep-based. **Raw-tool counter-query (#447 Phase 5 — wrapper-lane recall delta gate)**: when the wiring check uses any `sst3-code-*.sh` output to declare "no orphans" or "all callers accounted for", a Layer-3 subagent MUST cross-validate ONE call site with the raw equivalent (grep / direct ast-grep) before sign-off. Wrapper says 0 callers + raw says ≥1 = wrapper recall miss = FAIL the wiring check until reconciled.
- [ ] **Regression tests**: Run project test suite, verify no regressions
- [ ] **Quality scan**: No inefficiencies, no bottlenecks, no memory leaks, no dead code, STANDARDS.md compliant
- [ ] **AP #18 Sample Invocation Gate (#447 Phase 5 wrapper-script trigger expansion)**: scope triggers — pipeline / backtest / SL1 / SL2 / orchestration / CLI-wiring / cross-module function-arg propagation / persistent-state write / **any `../scripts/sst3-*.sh` wrapper change**. Real-CLI invocation against ≥3 repo shapes (auto_pb / job-hunter / dotfiles) + raw-tool counter-query for recall comparison, recorded in the issue comment. Skip rule applies only when none of the triggers fire; document the skip-reason explicitly.

## Quality Standards

- Quality First (proper execution over speed)
- JBGE (only problem-preventing content)
- LMCE (lean, mean, clean, effective)
- Fail Fast (error loudly, no silent fallbacks)
- Fix Everything (no deferrals, no scope excuses, no language boundaries)
- Investigate Before Coding (understand → plan → align → then code)
- Not Done Until Working (half-working = not done)
