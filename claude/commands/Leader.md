# Leader Mode

Direct instructions from the human leader. NOT suggestions. Orders. Do not skim. Do not summarise. Do not skip steps. Execute exactly as written.

## Guardrails (Apply to ALL Stages)

- **Context budget**: Research phase <30% of context. 80%+ = warn user. 90%+ = STOP and create handover.
- **Post-compact recovery**: If context was compacted mid-stage, re-read this skill file + CLAUDE.md + STANDARDS.md + the active Issue before continuing. Do NOT resume from memory.
- **Branch safety**: NEVER switch branches. Commit and push to the CURRENT branch. Ask the user if you need something from main.
- **Commit discipline**: Commit per file. NEVER `git add -A` or `git add .`.
- **AP #16 Monitor**: Every command, script, test, commit, push — verify end-to-end. Check exit codes, tail logs, confirm side effects. "Started" is not "done".
- **Subagent RESULT block**: Every subagent prompt MUST require a fenced `## RESULT` block at the end of its response:
  ```
  ## RESULT
  verdict: pass|fail|unknown
  files_touched: [list]
  findings: [{path, line, claim, evidence}]
  tee_log: <path or "none">
  scope_gaps: [list or "none"]
  ```
- **Scope snippet**: When dispatching >=10 subagents, write a frozen scope snippet (<=2K tokens) to `/tmp/sst3-scope-<topic>.md` and pass the PATH to each subagent — not the full issue body.
- **Multi-layer discipline (AP #14)**: Minimum 2 layers of subagents. Layer 2 MUST use a DIFFERENT prompt/angle than layer 1. Main agent verifies EVERY finding against source before acting. Swarm recommends; main agent verifies; source decides.
- **Never Assume**: Read the actual source before drawing conclusions. Do not state file contents without reading. Do not assume variable names, API shapes, or function signatures from memory. When in doubt, read first, conclude after.
- **Fix Everything**: All problems found get fixed — no deferrals, no scope excuses, no language boundaries. Python, Rust, JS, SQL, YAML, shell — fix them all. Only valid skip: confirmed false positive (document why).
- **FACT-CHECK RULE**: Default position: doubt yourself. Unless a claim is 100% backed by evidence, it is NOT factual and MUST be treated as unverified. Do not trust your memory. Do not trust your own confidence. Memory can be diluted, summarised incorrectly, or outdated. A memory entry without reference links, evidence, or calculations proving how figures were derived is NOT a reliable source. If memory says X but you cannot find the file, line, command output, or calculation that proves X, then X is UNVERIFIED — go find the proof or retract the claim. When in doubt, doubt yourself — then go verify.

## Stage Selection

If the user provided a stage number as an argument (e.g. `/Leader 3`), go directly to that stage. If no argument, present this menu and WAIT:

```
Leader Mode — pick a stage:

1. Research     — subagent swarm to research a topic, findings to /tmp
2. Issue Draft  — prepare /tmp issue from research, full quality sweep
3. Sanity Check — triple-check scope vs audit, then create GitHub issue
4. Implement    — re-invoke /SST3-solo, then proceed with the issue, do NOT stop (1M context)
5. Ship It      — verification loop + confirm Ralph passed + merge + user-review-checklist
6. Final Review — post-implementation deep audit of all work by subagents
```

Which stage? (1-6)

---

## Stage 1 — Research (Subagent Swarm -> /tmp)

Scale subagent count to match scope. No maximum. No minimum of 2-3. If 12 directories to check, dispatch 12+ subagents. Every subagent covers a different angle, directory, file set, or data source. No two subagents share the same prompt.

**Process**:
1. Check `docs/research/` in the active repo for existing research FIRST. Do not re-derive what exists.
2. Launch parallel subagents — max 5 files per subagent. Include the RESULT block schema in every subagent prompt.
3. Main context = orchestrator ONLY. Do NOT read source files directly. Subagents read; main agent collates.
4. If subagents return uncertain or conflicting findings, dispatch MORE subagents to resolve. Do not guess.
5. Collate ALL findings into `/tmp/research_<topic>_<date>.md`. File MUST contain:
   - **Findings** — each backed by file path, line number, command output, or URL
   - **Gaps identified** — what the research did NOT cover or could not confirm
   - **Plan / ideas / angles / brainstorm** — based on facts and data, not opinions or assumptions. Brainstorm with subagents to generate new angles, then verify each angle against evidence before including it.
   - **References** — every claim has a provenance trail (file:line, command output, URL, calculation showing how numbers were derived)
6. Present summary to user with `/tmp` file path.

**DO**: Back every claim with evidence. Dispatch more subagents when uncertain. Check existing research first. Brainstorm new angles with subagents. Verify every brainstormed idea against evidence before including it.
**DON'T**: Read source files in main context. Default to 2-3 subagents. State findings without file:line references. Hallucinate. Trust memory without verifying against source. State numbers without showing how they were calculated.

**SIGN-OFF**: When done, tell the user: "Stage 1 (Research) complete. Next: `/Leader 2` (Issue Draft)."

---

## Stage 2 — Issue Draft (/tmp, NOT GitHub)

Create `/tmp/issue_draft_<topic>_<date>.md` FIRST. Do NOT create the GitHub issue yet.

**Process**:
1. Read the `/tmp` research file from Stage 1.
2. Read `templates/issue-template.md`. Follow the template EXACTLY. Every section is mandatory:
   - PREREQUISITE CHECKPOINT (6 principle checkboxes)
   - Problem/Goal
   - Acceptance Criteria (phased, compact break notes between phases)
   - Engineering Requirements (Type Contracts, Schema Contracts, Config Traceability)
   - Quality Mantras (VERBATIM — see below)
   - Cleanup Requirements (Code Hygiene + File Housekeeping)
   - Context + References
3. Write ALL before/after illustrations. Show what exists NOW vs what it will look like AFTER so we can compare after implementation. These are mandatory for every change — code, config, behaviour, UI.
4. Quality mantras — include VERBATIM in the issue scope (copy exactly, do not paraphrase):
   - No inefficiencies, fix optimisation opportunities
   - Reliable and robust (not prone to breakage or failing)
   - Dedupe duplicate codes
   - No bottlenecks
   - Runs super fast and safe
   - No memory leaks using preventions
   - Follows STANDARDS.md
   - No false positives — everything real gets fixed
   - No such thing as high priority or low priority — all must be fixed
5. Launch subagents (layer 1) to check draft scope against research findings. Full coverage — every finding must map to a scope item.
6. Launch subagents (layer 2, DIFFERENT angle) to check for gaps, overengineering, and false positives.
7. Everything needs to be fixed. No excuses, no deferring. No "high priority" or "low priority". ALL must be fixed unless confirmed false positive (document WHY with evidence).
8. Present `/tmp` file path to user for review.

**DO**: Follow the template verbatim. Include every mandatory section. Show before/after for every change.
**DON'T**: Create the GitHub issue. Skip sections. Paraphrase quality mantras. Defer fixes.

**SIGN-OFF**: When done, tell the user: "Stage 2 (Issue Draft) complete. Next: `/Leader 3` (Sanity Check + GitHub Issue Creation)."

---

## Stage 3 — Sanity Check + GitHub Issue Creation

The draft exists. Now verify it is correct before it becomes the contract.

**Process**:
1. Read the `/tmp` issue draft from Stage 2.
2. Launch subagents (minimum 3, scale up). Each verifies independently:
   - **Scope vs Audit**: 100% of research findings captured? Nothing missing? No gaps?
   - **No overengineering**: Scoped items that solve problems that don't exist? Remove them.
   - **Chat history check**: Review the conversation. Did we discuss and agree on things NOT in the issue? Check for forgotten agreements.
   - **Opposite-scoping check**: Are we scoping the OPPOSITE of what was agreed? This failure mode is documented. Verify explicitly.
   - **Dead/obsolete/legacy code**: Did the audit find cleanup targets? Are they in the issue?
   - **All scope in issue BODY**: Nothing in comments. Everything in the body.
3. Layer 2 subagents (DIFFERENT prompt): cross-check layer 1 findings. Specifically verify no false positives and no false negatives in scope.
4. Each subagent returns a RESULT block. Main agent reviews ALL results.
5. If ANY subagent finds a gap: fix the draft. Do NOT create the issue with known gaps.
6. Once ALL subagents agree the draft is complete and accurate: create the GitHub issue using the verified draft verbatim.
7. Report the issue URL to the user.
8. **CONTEXT CHECK REMINDER**: After reporting the issue URL, tell the user their current context usage percentage and advise: "If context is above 50%, consider compacting before invoking `/Leader 4` — Stage 4 re-invokes `/SST3-solo` which reloads STANDARDS.md + CLAUDE.md + WORKFLOW.md + the Issue, so a compact here loses nothing and gives maximum room for implementation."

**DO**: Investigate when subagents disagree. Fix gaps before creating the issue. Verify against chat history. Remind user about context before Stage 4.
**DON'T**: Rubber-stamp. Pick the convenient answer when subagents conflict. Put scope in comments.

**SIGN-OFF**: When done, tell the user: "Stage 3 (Sanity Check) complete. Issue created: [URL]. Context usage: X%. If above 50%, consider compacting before next step. Next: `/Leader 4` (Implement — re-invokes /SST3-solo)."

---

## Stage 4 — Implement (Proceed with the Issue)

The issue is created and verified. Now implement it. Do NOT stop. Do NOT pause for compact breaks — you have a 1M context window, use it. The only reason to stop is if you hit 90% context usage, in which case create a handover.

**Process**:
1. Invoke `/SST3-solo` FIRST — this reloads STANDARDS.md, CLAUDE.md, and WORKFLOW.md. Mandatory even if already loaded. After a compact, these will be gone. This step ensures the agent is fully armed before touching code.
2. Read the GitHub issue line-by-line. Not skim — READ.
3. Implement every phase in the issue's Acceptance Criteria. Commit per file. Push after each phase.
4. Do NOT stop between phases to ask "shall I continue?" — the answer is yes. Proceed.
5. Do NOT create artificial compact breaks. You have 1M tokens. Use them.
6. Run the Verification Loop after all phases are complete.
7. Run Ralph Review (Haiku → Sonnet → Opus) — all 3 tiers mandatory.
8. On Ralph FAIL: fix → restart from Tier 1. On Ralph PASS: proceed.
9. Post checkpoint to issue comment when implementation is complete.

**DO**: Read the issue thoroughly. Implement all phases. Commit per file. Push frequently. Run Ralph Review. Keep going until done.
**DON'T**: Stop to ask permission between phases. Create unnecessary compact breaks. Skim the issue. Leave phases incomplete. Fire-and-forget commits without verifying push succeeded.

**SIGN-OFF**: When done, tell the user: "Stage 4 (Implement) complete. All phases implemented, Ralph Review passed. Next: `/Leader 5` (Ship It — verify + merge + checklist)."

---

## Stage 5 — Ship It (Verify + Merge + Checklist)

This stage has 3 sequential gates. Do NOT skip any. Ralph Review is handled during Stage 4 implementation — by the time you reach this stage, Ralph MUST have already passed.

### Gate 1: Verification Loop

Run these checks. Repeat until ALL pass:
- [ ] All issue checkboxes verified with evidence (file:line, command output)
- [ ] Overengineering check: simpler solution exists?
- [ ] Architecture reuse check: duplicated instead of reused existing code?
- [ ] Code duplication check: needs deduplication?
- [ ] Fallback policy check: silent failures introduced?
- [ ] Wiring check: all changed code actually called by existing functions/processes? No orphaned code?
- [ ] Regression tests: run project test suite, verify no regressions
- [ ] Quality scan: no inefficiencies, no bottlenecks, no memory leaks, no dead code, STANDARDS.md compliant
- [ ] Ralph Review: confirm all 3 tiers (Haiku/Sonnet/Opus) passed — check issue comments for evidence. If NOT yet run, STOP and run `/SST3-solo` Ralph Review first.

If ANY check fails: fix, re-run ALL checks. The loop exits only when every check passes.

### Gate 2: Merge

1. Ensure all work is committed (per-file commits) and pushed to remote.
2. Merge to main:
   - `git checkout main && git pull origin main`
   - `git merge <solo-branch> --no-edit`
   - Conflicts: preserve BOTH sides (Solo Branch Merge Safety). NEVER silently drop changes.
   - `git push origin main`
3. Delete the solo branch (local + remote). Run `git fetch --prune`.

### Gate 3: User Review Checklist

1. Read `templates/user-review-checklist.md`. Use the TEMPLATE. Do NOT invent your own.
2. Fill in ALL 10 sections. None are optional:
   - Scope Verification
   - Context Checkpoint
   - Gap Analysis — No Excuses Gate
   - How It Works
   - Cross-Issue Impact
   - Discoverability Check
   - Fail Fast Audit
   - Modular Architecture Review
   - Post-Implementation Review Gate
   - Closure Gate
3. Post the completed checklist as a comment on the GitHub issue.
4. Report to user: what was merged, issue URL, checklist posted.

**DO**: Run all 3 gates sequentially. Use the template files. Verify every step end-to-end.
**DON'T**: Skip Verification Loop. Make up your own checklist. Defer the merge. Merge without Ralph evidence.

**SIGN-OFF**: When done, tell the user: "Stage 5 (Ship It) complete. Merged to main, checklist posted to issue [URL]. Next: `/Leader 6` (Final Review — post-implementation audit)."

---

## Stage 6 — Final Review (Post-Implementation Deep Audit)

Subagents audit everything the main agent produced. Main agent produced the work; subagents verify it.

**Process**:
1. Launch subagent swarm (scale to implementation size). Each covers ONE angle with a RESULT block:
   - **Phase-by-phase scope review**: every issue phase delivered? Every acceptance criterion met?
   - **Goal alignment**: does the implementation solve the stated problem? "Code written" is not "problem solved".
   - **Wiring check**: every new function called by existing code? Every config key read? Every code path handles nulls? No orphaned code? Documentation references correct (file paths, line numbers, URLs all resolve)? Cross-references between docs, configs, and code all connected? Nothing dangling.
   - **Reliability and robustness**: is the implementation reliable and robust (not prone to breakage or failing)? Does it run super fast and safe?
   - **Inefficiency scan**: unnecessary allocations, O(n^2) where O(n) works, redundant DB queries, repeated calculations?
   - **Dead code cleanup**: obsolete/legacy code removed? Commented-out code removed? No backwards-compatibility hacks?
   - **Optimisation opportunities**: faster, simpler, more memory-efficient alternatives?
   - **Deduplication**: copy-pasted code that should be a shared function?
   - **Bottleneck detection**: single points of failure? Blocking operations that should be async?
   - **Memory leak prevention**: unclosed connections, uncleared caches, growing collections, event listener leaks?
   - **STANDARDS.md compliance**: all standards followed? Verification loop checks pass?
   - **Issue body 100% complete**: every checkbox ticked with evidence?
2. Layer 2 subagents (DIFFERENT angle): cross-check layer 1. Specifically look for false negatives (problems layer 1 missed).
3. Main agent reviews ALL RESULT blocks. Verify findings against source.
4. Fix ALL problems. No deferrals. No "low priority". All fixed unless confirmed false positive (document why with evidence).
5. If fixes were applied: run regression tests AFTER the fixes. This is mandatory — fixing code can introduce new regressions. Verify no regressions before declaring clean.
6. If fixes applied: commit, push, update the issue.
7. If no fixes needed: run regression tests anyway to confirm clean state.
8. Report to user: findings, fixes, regression test results, final state.

**DO**: Require specific findings from every subagent (file:line, evidence). Fix everything found. Run regression tests.
**DON'T**: Accept "looks fine" from subagents. Defer fixes. Skip regression tests. Fire-and-forget.

**SIGN-OFF**: When done, tell the user: "Stage 6 (Final Review) complete. All work audited, fixes applied, regression tests passed. Issue [URL] is done. Close the issue when satisfied."
