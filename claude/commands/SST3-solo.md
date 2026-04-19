# SST3-Solo Mode

## Mandatory Reading

Read these files in order BEFORE starting:
1. `standards/STANDARDS.md` (entire file)
2. Current repository's `CLAUDE.md` (entire file)
3. `workflow/WORKFLOW.md` (entire file — defines the 5-stage workflow)

## Per-Session Initialization

On each SST3-solo invocation, run this block ONCE (not per subagent dispatch).

**Graph availability check** — only if `code-review-graph` is registered in `~/.claude.json`.

Registration detection (explicit, not try/except): run
`grep -q '"code-review-graph"' ~/.claude.json && echo registered || echo unregistered`
- If `unregistered`: log `[GRAPH] Server not registered; skipping pre-session check. Downstream graph calls (WORKFLOW Stage 1, Ralph) will skip with documented fallback.` and continue to main SST3-solo work.
- If `registered`: proceed with the graph check below.

Graph check (registered case):
1. Run `mcp__code-review-graph__config action=status`. If the call errors, log `[GRAPH] config status failed: <error>; retrying once.` and retry once. If second attempt fails, log `[GRAPH unavailable: MCP call failed after retry]` and continue — downstream will fall back to subagent with documented evidence.
2. If `total_nodes == 0`, run `graph build` (one-off; subsequent sessions skip the build).
3. If `last_updated > 24h`, run `graph update`.

Cadence: this check runs ONCE per SST3-solo invocation, not per subagent dispatch. Between sessions, a `git fetch` that lands new commits should trigger `graph update` as part of the next session's check. See `../../docs/guides/code-review-graph-playbook.md` for the 24h rationale and per-repo freshness-tuning note.

This is the structural-query layer; the subagent swarm remains your semantic layer. Rule detail lives in STANDARDS.md "Structural Code Queries".

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
- [ ] Check context memory: If 80%+ used, warn user. If 90%+, STOP.
- [ ] Commit after EACH file change — NEVER use `git add -A`

### After Compact (Context Recovery)
- [ ] Re-read CLAUDE.md
- [ ] Re-read STANDARDS.md
- [ ] Re-read Issue (or last checkpoint comment)
- [ ] Continue from last checkpoint

## Verification Loop (MANDATORY)

Repeat until ALL pass:
- [ ] All checkboxes verified with evidence
- [ ] Overengineering check: simpler solution exists?
- [ ] Architecture reuse check: duplicated instead of reused?
- [ ] Code duplication check: needs deduplication?
- [ ] Fallback policy check: silent failures?
- [ ] **Wiring check**: All changed code actually called by existing functions/processes? Structural layer: `mcp__code-review-graph__query callers_of(<function>)` + `query impact(changed_files)` when graph available (per STANDARDS.md "Structural Code Queries" pre-query gate). Semantic layer: subagent verifies each caller handles the new contract. YAML / shell / unsupported-language keys still grep-based.
- [ ] **Regression tests**: Run project test suite, verify no regressions
- [ ] **Quality scan**: No inefficiencies, no bottlenecks, no memory leaks, no dead code, STANDARDS.md compliant

## Quality Standards

- Quality First (proper execution over speed)
- JBGE (only problem-preventing content)
- LMCE (lean, mean, clean, effective)
- Fail Fast (error loudly, no silent fallbacks)
- Fix Everything (no deferrals, no scope excuses, no language boundaries)
- Investigate Before Coding (understand → plan → align → then code)
- Not Done Until Working (half-working = not done)
