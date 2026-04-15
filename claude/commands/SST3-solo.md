# SST3-Solo Mode

## Mandatory Reading

Read these files in order BEFORE starting:
1. `standards/STANDARDS.md` (entire file)
2. Current repository's `CLAUDE.md` (entire file)
3. `workflow/WORKFLOW.md` (entire file — defines the 5-stage workflow)

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
- [ ] **Wiring check**: All changed code actually called by existing functions/processes?
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
