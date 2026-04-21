# GitHub Issue Template

### Title Format
```
[Type]: Brief description
```

**Types**: Feature, Fix, Refactor, Docs, Test, Chore

### Pre-Issue Research Gate (Stage 1 — MANDATORY)

- [ ] Check `docs/research/` for existing research on this domain
- [ ] Launch parallel subagents (5 files max each) to explore codebase — main context MUST NOT read source files directly
- [ ] Map root cause (not symptom) — why does this need to exist?
- [ ] Identify hidden dependencies: what other systems does this touch?
- [ ] Validate config: are all required config values present and valid? (Fail Fast — missing config = error, not default)
- [ ] Main agent collates all subagent findings into /tmp file: **findings + gaps + plan**
- [ ] Research phase used <30% of context budget
- [ ] Confirm: Issue body scope below reflects research findings, not assumptions

> **Subagent dispatch discipline (#406 F5.1 + F5.3)** — when dispatching ≥10 subagents, follow STANDARDS.md "Subagent Orchestration Discipline":
> - **Scope Snippet Rule** (F5.1): main agent writes a frozen scope snippet (≤2K tokens, scope+acceptance only) to `${SST3_TMP:-/tmp}/sst3-issue-<N>-scope.md` and passes the path to subagents instead of the full issue body. ONE scout subagent reads the full issue.
> - **RESULT Block Schema** (F5.2): every swarm subagent ends with the fenced `## RESULT` block (verdict / files_touched / findings / tee_log / scope_gaps). Main agent parses RESULT, ignores prose body.
> - See `../standards/STANDARDS.md` "Subagent Orchestration Discipline" for the full schema and rules.

### Issue Body

**PREREQUISITE CHECKPOINT** — first lines of every Issue body:

> **PREREQUISITE CHECKPOINT**
- [ ] Confirm: Read ALL sections below line-by-line (Problem/Goal, Expected Behavior, Acceptance Criteria). Evidence required: List 3-5 key scope items when checking this box.

> - [ ] **Fail Fast**: Loud errors, no fallbacks/defaults/silent failures
> - [ ] **No Hardcoded Settings**: Parameters in config files, not embedded in code
> - [ ] **Reuse Existing**: Use existing architecture/patterns, don't duplicate
> - [ ] **LMCE**: Lean, Mean, Clean, Effective
> - [ ] **JBGE**: Just Barely Good Enough (only what prevents problems)
> - [ ] **Single Objective**: This Issue has ONE objective. If mixed (fix + refactor), split now.
> - [ ] **Sample Invocation Gate (AP #18)**: if this Issue touches pipeline / data-processing / orchestration / CLI-wiring / cross-module function-arg propagation, Stage 4 MUST include a real-CLI sample invocation (real DB, 8-item liquid basket) that exercises the full pipeline end-to-end before close. Unit + smoke tests alone are INSUFFICIENT. Mocks MUST assert explicit `call_args.kwargs[...]` — never rely on `**kwargs`-swallowing. Skip only if change does NOT trigger AP #18 scope; document the skip reason when checking the box.

## Problem/Goal

[Clearly state what needs to be done and why. Include business value or technical rationale.]

## Expected Behavior

- [ ] [First expected behavior as checkbox]
- [ ] [Second expected behavior as checkbox]

## Acceptance Criteria

### [Phase 1: Description]
> **PHASE CHECKPOINT**: After this phase, post a checkpoint comment to the issue and CONTINUE to the next phase. Do NOT pause for user. Stop only if context is 80%+ used, a destructive action needs consent, you are genuinely stuck, or the task is complete.

- [ ] [Specific acceptance criterion]
- [ ] [Specific acceptance criterion]

### [Phase 2: Description]
> **PHASE CHECKPOINT**: After this phase, post a checkpoint comment to the issue and CONTINUE to the next phase. Do NOT pause for user. Stop only if context is 80%+ used, a destructive action needs consent, you are genuinely stuck, or the task is complete.

- [ ] [Specific acceptance criterion]
- [ ] [Specific acceptance criterion]

### Engineering Requirements (if code changes)
- [ ] **Fix Everything**: All problems found get fixed — no deferrals, no scope excuses, no language boundaries
- [ ] **Type Contracts**: Every function parameter type annotation verified against actual callers. `None` callers → annotation must be `T | None` with null guard.
- [ ] **Schema Contracts**: Every SQL query's column names verified against actual DB schema (`\d tablename` or migration file). SQL literal values match DB data.
- [ ] **Config Traceability**: Every YAML key added is read by code. Dead config (key in YAML, never read) = FAIL. List key → code location.

### Quality Mantras (VERBATIM — repeat at each phase)

- No inefficiencies, fix optimisation opportunities
- Reliable and robust (not prone to breakage or failing)
- Dedupe duplicate codes
- No bottlenecks
- Runs super fast and safe
- No memory leaks using preventions
- Follows STANDARDS.md
- No false positives — everything real gets fixed
- No such thing as high priority or low priority — all must be fixed

## Cleanup Requirements

### Code Hygiene (REMOVAL)
- [ ] Remove debug code (console.log, print statements, debug flags)
- [ ] Remove abandoned code from failed/rescoped approaches
- [ ] Remove orphaned code from scope/direction changes
- [ ] Verify no commented-out "old" code left behind

### File Housekeeping
- [ ] Document all files created during implementation
- [ ] Specify temp vs permanent files
- [ ] All files properly located per STANDARDS.md

## Context

[Any additional background, constraints, or considerations]

## References

- Related Issues: #X, #Y
- Documentation: [link]
- Graph queries used (when structural-code topic, per AP #19 RESULT discipline): list every `callers_of` / `impact` / `search` call — target, result count, `last_updated`, `embeddings_count`, and one spot-check source file:line per query. Makes Stage 3 + Stage 5 re-verification trivial.

---

## Triple-Check Gate (Stage 3 — MANDATORY before Solo Assignment)

### Scope Coverage Audit
- [ ] List all checkboxes in Expected Behavior + Acceptance Criteria: ___ total
- [ ] For each checkbox: confirm research supports a specific implementation approach
- [ ] Any checkbox without a clear approach = STOP and resolve before proceeding

### Anti-Bias Self-Check
- [ ] Am I solution-building before understanding the existing implementation? (If YES → read codebase first)
- [ ] Have I examined the existing code that this touches? (File paths: ___)
- [ ] What am I assuming that could be wrong? (Document here: ___)
- [ ] What will break when I make this change? (Integration risks: ___)
- [ ] Does this solve the root cause or a symptom?

### Scope Verification
- [ ] Independent subagent verification: scope vs audit doc = 100% captured
- [ ] Check against chat history: nothing discussed and agreed was forgotten
- [ ] Verify not scoping the opposite of what was agreed
- [ ] Check for dead/obsolete/legacy code cleanup opportunities
- [ ] All scope in issue BODY — never in comments

### Scope Amendment (If gaps found)
- [ ] All gaps added to Acceptance Criteria above (NOT in comments — BODY is permanent scope)
- [ ] Re-run Scope Coverage Audit with amended checkboxes

---

## Solo Assignment (SST3 Automated)

### Execution Guardrails (MANDATORY)

#### Before Starting Work
- [ ] Read CLAUDE.md in full
- [ ] Read STANDARDS.md in full
- [ ] Read this Issue line-by-line (not skim)
- [ ] List 3-5 key scope items as evidence of reading

#### Codebase Review (Prevent Duplication)
- [ ] **Review scope**: What problem does this solve? What's the expected outcome?
- [ ] **Search for existing code**: Use Glob/Grep/Agent(Explore) to find similar modules
- [ ] **Explore related code**: Find files/modules related to this feature
- [ ] **Identify reuse opportunities**: Can existing code be extended instead of new code?
- [ ] **Document findings**: Note which existing modules/patterns to leverage

#### Branch Creation
- [ ] Create solo branch: `git checkout -b solo/issue-{number}-{description}`
- [ ] **HARD STOP**: NEVER switch branches mid-implementation. NEVER run `git checkout main` or `git switch`.

#### During Work (At Each Phase Checkpoint)
- [ ] **Post checkpoint to Issue comment** with:
  - Phase completed
  - Files modified
  - Key changes made
  - Any blockers or scope changes
- [ ] **Check context memory**: If 70%+ used, warn user. If 80%+, STOP and notify.
- [ ] **Commit after EACH file change**: `git add {file} && git commit -m "type: description (#issue)" && git push`
- [ ] **NEVER use `git add -A` or `git add .`** — stage files individually by name only

#### Context Management (For Long Issues)
- [ ] **After each phase**: Check context usage — if 70%+, warn; if 80%+, stop
- [ ] **At 70% context**: Warn user - "Context at ~70%, approaching stop threshold"
- [ ] **At 80% context**: STOP immediately, post checkpoint, notify user
- [ ] **Before any risky operation**: Ensure checkpoint posted (compaction could happen anytime)

**Checkpoint Content**:
```
## Checkpoint: Phase X Complete
- Current phase: [phase name]
- Files modified: [list]
- Next steps: [what remains]
- Blockers: [if any]
- Resume command: /SST3-solo then "continue Issue #X from Phase Y"
```

#### After Compact (Context Recovery)
- [ ] Re-read CLAUDE.md
- [ ] Re-read STANDARDS.md
- [ ] Re-read this Issue (or last checkpoint comment)
- [ ] Continue from last checkpoint

### Verification Loop (MANDATORY - Repeat Until Clean)

> Canonical: [`SST3/workflow/WORKFLOW.md` "## Verification Loop"](../workflow/WORKFLOW.md#verification-loop). Run that loop here. Don't restate it. (#406 F3.6 dedup — single source of truth.)

- [ ] Verification Loop run, all checks pass per WORKFLOW.md canonical list

### Ralph Review Loop (MANDATORY - Automated 3-Tier Review)

> **REQUIRED**: Implement → Haiku → Sonnet → Opus. **Subagents are PLANNING ONLY** (review, do NOT write code). FAIL any tier: fix + restart Tier 1.

#### Tier 1: Haiku Subagent (Surface Checks)
**Model**: `haiku` (MANDATORY)
**Mode**: PLANNING ONLY - review, do NOT write code
- [ ] Subagent spawned in PLANNING MODE (no code written)
- [ ] HAIKU_PASS received
- [ ] All checkboxes have evidence
- [ ] Files in correct locations
- [ ] No debug code
- [ ] Commits reference issue number

#### Tier 2: Sonnet Subagent (Logic Checks)
**Model**: `sonnet` (MANDATORY)
**Mode**: PLANNING ONLY - review, do NOT write code
- [ ] Subagent spawned in PLANNING MODE (no code written)
- [ ] SONNET_PASS received
- [ ] Evidence proves completion
- [ ] Scope alignment verified
- [ ] No silent fails, no fake defaults
- [ ] No duplicate modules
- [ ] No dead/obsolete/orphaned code

#### Tier 3: Opus Subagent (Deep Analysis)
**Model**: `opus` (MANDATORY)
**Mode**: PLANNING ONLY - review, do NOT write code
- [ ] Subagent spawned in PLANNING MODE (no code written)
- [ ] OPUS_PASS received
- [ ] Architectural fit
- [ ] No overengineering
- [ ] STANDARDS.md compliant
- [ ] User review checklist complete

**Checklists**: `ralph/`

### Branch & Commit Discipline
> Commit after EACH file change. NO batching. NEVER `git add -A`.

- [ ] **After EACH file change**: commit + push immediately
- [ ] Commit format: `type: description (#issue)` (e.g., `refactor: update template (#390)`)

### Merge to Main (BEFORE User Review - Protects Work)
- [ ] Run Ralph Review (Haiku → Sonnet → Opus)
- [ ] Pull main, check for conflicts (Solo Branch Merge Safety: diff for concurrent edits, preserve BOTH)
- [ ] Merge solo branch: `git merge solo/issue-{number}-{description}`
- [ ] Push main: `git push`

### User Review (MANDATORY - Cannot Skip)
- [ ] POST user-review-checklist.md to user in chat (from TEMPLATE — ALL sections mandatory)
- [ ] Work through checklist WITH user
- [ ] Run validation: `python SST3/scripts/check-issue-body-vs-comments.py --issue [NUMBER]`
- [ ] **WAIT** for user approval
- [ ] User approves

### Cleanup (After User Approval)
- [ ] Delete local branch: `git branch -d solo/issue-{number}-{description}`
- [ ] Delete remote branch: `git push origin --delete solo/issue-{number}-{description}`
- [ ] Close Issue
