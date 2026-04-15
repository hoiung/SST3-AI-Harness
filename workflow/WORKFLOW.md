# SST3 Solo Workflow

**Subagents**: research, read, audit, plan, verify. NEVER write code, create issues, or implement. **Main agent**: collates findings, writes /tmp, creates issues, implements, commits, merges.

## The 5-Stage Sequential Workflow

**CRITICAL**: ORDER-DEPENDENT. No skipping, no reordering.

### Stage 1 — Research (Subagent Swarm → /tmp)

- [ ] Check `docs/research/` for existing research on this domain first
- [ ] Launch MANY parallel subagents, each with focused area (5 files max per subagent)
- [ ] Main context = orchestrator only — NEVER read source files directly in main context
- [ ] Research phase must use <30% of context budget
- [ ] Main agent collates all subagent findings into /tmp file containing: **findings + gaps + plan**
- [ ] Output /tmp file for user review before proceeding to Stage 2

### Stage 2 — Issue Creation (Main Agent from /tmp Research)

- [ ] Use `../templates/issue-template.md` — NEVER create issues from scratch
- [ ] Add ALL before/after illustrations for comparison after implementation
- [ ] Add compact breaks between phases in Acceptance Criteria
- [ ] Check context memory — stop and allow compact before continuing if needed
- [ ] Multiple subagents for full coverage scope-check vs audit
- [ ] Quality mantras listed VERBATIM in issue scope — not summarized:
  - No inefficiencies, fix optimisation opportunities
  - Reliable and robust (not prone to breakage or failing)
  - Dedupe duplicate codes
  - No bottlenecks
  - Runs super fast and safe
  - No memory leaks using preventions
  - Follows STANDARDS.md
- [ ] No false positives — everything real gets fixed
- [ ] No such thing as high priority or low priority — all must be fixed

### Stage 3 — Triple-Check (Subagents Verify Scope)

- [ ] Scope vs audit doc = 100% captured, nothing missing, no gaps
- [ ] No overengineering — only what was agreed
- [ ] Check against chat history — don't forget things discussed and agreed on
- [ ] Verify no tendency to scope the opposite of what was agreed
- [ ] Check for dead/obsolete/legacy code cleanup opportunities
- [ ] Same quality mantras repeated:
  - No inefficiencies, fix optimisation opportunities
  - Reliable and robust (not prone to breakage or failing)
  - Dedupe duplicate codes, no bottlenecks, fast and safe, no memory leaks
  - Clean up dead obsolete legacy codes
  - Follows STANDARDS.md
- [ ] All scope goes in issue BODY — never in comments (comments are temporal, body is permanent)

### Stage 4 — Implementation + Merge + User Review

- [ ] Implement all phases from issue Acceptance Criteria
- [ ] Commit after EACH file change: `git add {file} && git commit -m "type: description (#issue)" && git push`
- [ ] Run Verification Loop (repeat until clean — see below)
- [ ] Run Ralph Review: Haiku → Sonnet → Opus (all 3 mandatory)
- [ ] Merge to main BEFORE user review (protects work):
  - `git checkout main && git pull origin main` (check for conflicts — preserve BOTH)
  - `git merge solo/issue-{number}-{description} && git push`
- [ ] POST `user-review-checklist.md` from TEMPLATE — not made up, ALL sections mandatory, NONE optional
- [ ] Work through checklist WITH user
- [ ] Fix any gaps found — no deferrals, no excuses unless confirmed false positive
- [ ] User approves

### Stage 5 — Post-Implementation Review (Subagent Swarm)

- [ ] Review against issue body scope, goal alignment, and design doc
- [ ] **Wiring check**: Everything wired up properly — common failure: fix/enhance/refactor but forget to wire up to existing functions
- [ ] Check for: inefficiencies, dead code from refactors, optimisation opportunities
- [ ] Reliable and robust (not prone to breakage or failing)
- [ ] Duplications that need dedupe, bottlenecks
- [ ] No memory leaks using preventions
- [ ] Follows STANDARDS.md
- [ ] Check issue body scope 100% completed — no gaps
- [ ] Fix ALL problems — no deferrals, no excuses
- [ ] Run regression tests — if not run yet, run them now

## Verification Loop

- [ ] **Scope completeness gate**: Enumerate every Acceptance Criteria checkbox from issue body. For EACH one: state file:line that implements it. Any checkbox without file:line = NOT DONE. Do NOT proceed until all checkboxes have evidence.
- [ ] All checkboxes verified with evidence
- [ ] Overengineering check: simpler solution exists?
- [ ] Architecture reuse check: duplicated instead of reused?
- [ ] Code duplication check: needs deduplication?
- [ ] Fallback policy check: silent failures?
- [ ] **Wiring check — 4 parts**:
  1. Every new function/method is called from at least one caller (grep for function name in codebase)
  2. Every config key added to YAML is read by code (grep for key name in source — zero results = dead config)
  3. Every SQL query's column names exist in the target table (verify with `\d tablename` or migration file)
  4. Every None-producing code path: confirm callee's type annotation accepts `Optional` / has null guard
- [ ] **Regression tests**: Run project test suite, verify no regressions
- [ ] **Quality scan**: No inefficiencies, no bottlenecks, no memory leaks, no dead code, STANDARDS.md compliant
- [ ] **AP #18 Sample Invocation Gate**: if the change touches pipeline / data-processing / orchestration / CLI-wiring / cross-module function-arg propagation → a REAL-CLI sample invocation (8-item liquid basket, real DB) must be run BEFORE close. Exit code 0 alone insufficient — verify row-count landed, downstream consumers succeeded, audit queries OK. Document the sample log path + verification queries in an Issue comment. If NOT in-scope, document the scope-skip reason. Canonical: ANTI-PATTERNS.md #18 + STANDARDS.md "Testing Priority — Workflow Validation Gate".

## Branch & Commit Discipline

```bash
# Create branch
git checkout -b solo/issue-{number}-{description}

# HARD STOP: NEVER switch branches mid-implementation
# NEVER use git add -A or git add . — stage files individually

# After EACH file change
git add {file}
git commit -m "type: description (#issue)"
git push

# Merge and cleanup (after Ralph Review passes, BEFORE user review)
git checkout main
git pull origin main
# Check for conflicts — diff for concurrent edits, preserve BOTH
git merge solo/issue-{number}-{description}
git push
git branch -d solo/issue-{number}-{description}
git push origin --delete solo/issue-{number}-{description}
```

## Context Management

**Context**: 1M window (Opus/Sonnet), 200K (Haiku). Handover at 80% (800K of 1M, 160K of 200K) — stop threshold, not routine. Warn at 70%, work until 80%. Content budget ~42K. Research budget <30% Stage 1.

## Quality Standards

See STANDARDS.md (mandatory read). Key rule labels: Quality First, JBGE, LMCE, Fail Fast, Fix Everything, Investigate Before Coding, Wiring Verification, Never Replace — ADD Alongside.

## Templates

- **Issue Creation**: `../templates/issue-template.md`
- **Execution Template**: `../templates/subagent-solo-template.md`
- **User Review**: `../templates/user-review-checklist.md`
- **Chat Handover**: `../templates/chat-handover.md`

## Checkpoint Format

Post to Issue after each phase:

```markdown
## Phase X Checkpoint

**Completed**:
- [description of phase work]

**Files Modified**:
- `path/to/file.ext` (lines X-Y)

**Next**:
- [upcoming work]

**Context**: ~X% used
```
