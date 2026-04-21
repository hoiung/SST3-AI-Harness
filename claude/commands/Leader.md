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
  mcp_graph_available: yes|no   (FIRST line when subagent discusses graph queries — AP #19 L435)
  verdict: pass|fail|unknown
  files_touched: [list]
  findings: [{path, line, claim, evidence}]
  tee_log: <path or "none">
  scope_gaps: [list or "none"]
  ```
- **Scope snippet**: When dispatching >=10 subagents, write a frozen scope snippet (<=2K tokens) to `/tmp/sst3-scope-<topic>.md` and pass the PATH to each subagent — not the full issue body.
- **Double-Guardrail Principle (N32)**: every `/Leader` invocation checks BOTH the cross-cutting SST3 canonical (STANDARDS.md + ANTI-PATTERNS.md + WORKFLOW.md + project CLAUDE.md) AND the invoked-skill's domain canonical (voice_rules, eBay rules, blog voice-guard, job-hunter dual-lens, claude-api prompt caching, project CLAUDE.md rules). Stage 1 identifies the invoked skill and records `invoked_skill` + `skill_canonical_files` in the research file. Stage 3 adds a skill-canonical compliance subagent angle. Stage 4 Gate 1 + Stage 5 run the skill's own verification hooks. See STANDARDS.md "Double-Guardrail Principle".
- **Multi-layer discipline (AP #14)**: Minimum 2 layers of subagents. Layer 2 MUST use a DIFFERENT prompt/angle than layer 1. Main agent verifies EVERY finding against source before acting. Swarm recommends; main agent verifies; source decides.
- **Never Assume**: Read the actual source before drawing conclusions. Do not state file contents without reading. Do not assume variable names, API shapes, or function signatures from memory. When in doubt, read first, conclude after.
- **Fix Everything**: All problems found get fixed — no deferrals, no scope excuses, no language boundaries. Python, Rust, JS, SQL, YAML, shell — fix them all. Only valid skip: confirmed false positive (document why).
- **FACT-CHECK RULE**: Default position: doubt yourself. Unless a claim is 100% backed by evidence, it is NOT factual and MUST be treated as unverified. Do not trust your memory. Do not trust your own confidence. Memory can be diluted, summarised incorrectly, or outdated. A memory entry without reference links, evidence, or calculations proving how figures were derived is NOT a reliable source. If memory says X but you cannot find the file, line, command output, or calculation that proves X, then X is UNVERIFIED — go find the proof or retract the claim. When in doubt, doubt yourself — then go verify.
- **Governance Enforcement — Checkbox MCP (AP #20)**: at every Acceptance Criteria checkbox completion → invoke `mcp__github-checkbox__update_issue_checkbox(issue_number, checkbox_text, evidence)` with per-deliverable evidence. Comment-only progress is NOT a substitute. **Before invocation**: check for deferred-tool status and load the schema via `ToolSearch` per STANDARDS.md "MCP Tool Schema Loading" — mandatory, not optional. Canonical evidence-quality patterns: `reference/tool-selection-guide.md` Example 2.

## Stage Selection

If the user provided a stage number as an argument (e.g. `/Leader 3`), go directly to that stage. Treat `/Leader 6` as a deprecated alias for `/Leader 5` — silently proceed to Stage 5. If no argument, present this menu and WAIT:

```
Leader Mode — pick a stage:

1. Research     — subagent swarm to research a topic, findings to /tmp
2. Issue Draft  — prepare /tmp issue from research, full quality sweep
3. Sanity Check — triple-check scope vs audit, then create GitHub issue
4. Implement    — /SST3-solo, implement all phases, Verification Loop, Ralph Review, merge, user-review-checklist
5. Post-Implementation Review — subagent swarm post-implementation deep audit (100% mandatory)
```

Which stage? (1-5)

---

## Stage 1 — Research (Subagent Swarm -> /tmp)

Scale subagent count to match scope. No maximum. No minimum of 2-3. If 12 directories to check, dispatch 12+ subagents. Every subagent covers a different angle, directory, file set, or data source. No two subagents share the same prompt.

**Process**:
0. **Restate the task in the user's exact words** at the TOP of the research file, before any other content. Quote the user's original phrasing verbatim. If your interpretation requires translating jargon, preserve the original alongside your interpretation. Rationale (round-5 N49 agent5): ~4h + thousands of tokens wasted on intent misinterpretation — no graph query or subagent angle can catch an intent error; only pre-swarm restatement can. Stage 3 sanity-check verifies the restatement matches the user's literal task before approving scope.
0a. **Identify invoked skill + record skill-canonical metadata** (N32 Double-Guardrail first link). Record in the research file: `invoked_skill: <skill-name-or-"none">` and `skill_canonical_files: [list of files]`. Examples — `blog` / `job-hunter` → `voice_rules.py`, `VOICE_PROFILE.md`; `ebay-seller-tool` → Seagate HARD CONTRACT + 21-field listing contract docs; `claude-api` → prompt-caching SDK references + current model IDs; `SST3-solo` / `Leader` → N/A (cross-cutting SST3 only, no domain skill). If task is pure infrastructure (no domain skill invoked), record `invoked_skill: none`. This metadata is READ by Stage 3 (skill-canonical compliance subagent angle), Stage 4 Gate 1 (skill-canonical verification checkbox), and Stage 5 (skill-canonical audit). See STANDARDS.md "Double-Guardrail Principle".
1. Check `docs/research/` in the active repo for existing research FIRST. Do not re-derive what exists.
1a. **MANDATORY freshness CHECK at Stage 1 top**: run `mcp__code-review-graph__config action=status` unconditionally and record `last_updated` + `total_nodes` + `embeddings_count` in the research file — audit trail for Stage 5 reviewers, even on 12-moments topics. If structural-code topic AND graph stale (`last_updated` older than HEAD or null), ALSO run `mcp__code-review-graph__graph action=update` before any Stage-1 graph query. **Null/0 decision rule (TC-5 N26)**: if `config status` returns `last_updated=null` AND `total_nodes>0` (graph populated but timestamp not recorded), treat as STALE for structural-code topics → run `graph update` to backfill the timestamp. For 12-moments topics, log the anomaly and proceed. (Parity fix for #422 Stage 4 asymmetry — round-4 N5 + round-5 self-validation. Refined: CHECK is unconditional; UPDATE is conditional on whether graph will be queried.)
1b. **Pre-swarm graph SEED**: if the research topic is structural code in a supported language (see STANDARDS.md "Structural Code Queries"), use graph to DEFINE scope BEFORE dispatching the swarm — not to verify pre-formed scope AFTER. Run `mcp__code-review-graph__query callers_of <symbol>` and `search <symbol>` on every symbol the USER MENTIONED in the task description, plus `impact` on files the user named. Feed the resulting call-site / symbol / blast-radius data into the subagent prompts so layer-1 angles are scoped to real evidence, not hypothesis. Graph findings SEED the swarm; they do NOT replace its different-angle coverage. **Hybrid topics** (code + docs, e.g. "refactor X + update README"): run graph queries on the code portion ONLY; use subagents for the semantic portion. Record `graph_applicable_files` vs `graph_exempt_files` in the research file. Skip-condition: if topic is semantic / voice / intent / cross-document / non-code (12 subagent-only moments per STANDARDS.md), skip graph queries and go to step 2 — the 1a freshness CHECK still ran unconditionally for audit trail. Record graph calls + `last_updated` + `embeddings_count` + one spot-check file:line per query in the /tmp research file.
2. Launch parallel subagents — max 5 files per subagent. Include the RESULT block schema in every subagent prompt.
3. Main context = orchestrator ONLY. Do NOT read source files directly. Subagents read; main agent collates.
4. If subagents return uncertain or conflicting findings, dispatch MORE subagents to resolve. Do not guess.
5. Collate ALL findings into `/tmp/research_<topic>_<date>.md`. File MUST contain:
   - **Findings** — each backed by file path, line number, command output, or URL
   - **Gaps identified** — what the research did NOT cover or could not confirm
   - **Plan / ideas / angles / brainstorm** — based on facts and data, not opinions or assumptions. Brainstorm with subagents to generate new angles, then verify each angle against evidence before including it.
   - **References** — every claim has a provenance trail (file:line, command output, URL, calculation showing how numbers were derived)
6. Present summary to user with `/tmp` file path.

**DO**: Back every claim with evidence. Dispatch more subagents when uncertain. Check existing research first. Brainstorm new angles with subagents. Verify every brainstormed idea against evidence before including it. Record `graph_applicable: true|false (reason: <class>)` in the /tmp research file — downstream stages 2/3/4/5 MUST read this field and do NOT re-derive the classification independently (single-declaration-carries-forward, TB-2 N29+N34).
**DON'T**: Read source files in main context. Default to 2-3 subagents. State findings without file:line references. Hallucinate. Trust memory without verifying against source. State numbers without showing how they were calculated.

**SIGN-OFF**: When done, tell the user: "Stage 1 (Research) complete. Next: `/Leader 2` (Issue Draft)."

---

## Stage 2 — Issue Draft (/tmp, NOT GitHub)

Create `/tmp/issue_draft_<topic>_<date>.md` FIRST. Do NOT create the GitHub issue yet.

**Process**:
1. Read the `/tmp` research file from Stage 1.
1b. **Graph scope-completeness recipe** (structural-code topics in supported languages — see playbook "Stage-Mapped Recipes" Stage 2 section): for every function/hook/class named in the scope, run `mcp__code-review-graph__query callers_of <file::symbol>` and compare the count to what Stage 1 research claimed. More call sites than research flagged = expand scope. For every "X doesn't exist" claim, run `search X` (literal identifier when `embeddings_count=0`). Record every query + target + count + one spot-check file:line in the draft's References section. Skip if topic is semantic / non-code / one of the 12 subagent-only moments.
2. Read `../templates/issue-template.md`. Follow the template EXACTLY. Every section is mandatory:
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

**Skill-canonical at draft-write time (N32 Double-Guardrail)**: while authoring the draft, verify it does NOT violate the invoked skill's canonical (per Stage 1 research-file `invoked_skill`). No voice-banned words in an acceptance criterion for a blog / job-hunter / CV task; no Seagate series mislabel in eBay scope; no retired model IDs in a claude-api task. This is the author-time counterpart to Stage 3's subagent verification.

**DO**: Follow the template verbatim. Include every mandatory section. Show before/after for every change.
**DON'T**: Create the GitHub issue. Skip sections. Paraphrase quality mantras. Defer fixes.

**SIGN-OFF**: When done, tell the user: "Stage 2 (Issue Draft) complete. Next: `/Leader 3` (Sanity Check + GitHub Issue Creation)."

---

## Stage 3 — Sanity Check + GitHub Issue Creation

The draft exists. Now verify it is correct before it becomes the contract.

**Process**:
1. Read the `/tmp` issue draft from Stage 2. Read `graph_applicable` from the Stage 1 research file — do NOT re-classify independently (TB-2 single-declaration-carries-forward).
2. Launch subagents (minimum 3, scale up). Each verifies independently:
   - **Scope vs Audit**: 100% of research findings captured? Nothing missing? No gaps?
   - **No overengineering**: Scoped items that solve problems that don't exist? Remove them.
   - **Chat history check**: Review the conversation. Did we discuss and agree on things NOT in the issue? Check for forgotten agreements.
   - **Opposite-scoping check**: Are we scoping the OPPOSITE of what was agreed? This failure mode is documented. Verify explicitly.
   - **Dead/obsolete/legacy code**: Did the audit find cleanup targets? Are they in the issue? Structural layer: `mcp__code-review-graph__query large_functions(min_lines=200)` + `query impact(changed_files)` on the area the Issue edits, when graph available and fresh (pre-query gate per STANDARDS.md "Structural Code Queries"). Surfaces dead-code / wide-blast-radius candidates that should be in scope. Subagent still verifies intent (intentional duplication vs accidental).
   - **All scope in issue BODY**: Nothing in comments. Everything in the body.
   - **Skill-canonical compliance** (Double-Guardrail Principle — N32): subagent reads the invoked skill's canonical (per Stage 1 research-file metadata `invoked_skill` + `skill_canonical_files`) and verifies the issue draft does not violate any rule. Examples: voice_rules banned-words clean (blog / job-hunter / CV); Seagate HARD CONTRACT + 21-field + SMART gate (eBay); prompt-caching + model-ID currency (claude-api); paper/live parity + never-touch-production (auto_pb).
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

## Stage 4 — Implement (includes Verification Loop + Merge + User-Review-Checklist)

The issue is created and verified. Now implement it. Do NOT stop. Do NOT pause for compact breaks — you have a 1M context window, use it. The only reason to stop is if you hit 90% context usage, in which case create a handover.

Stage 4 has three sequential gates after the implementation phases complete: Gate 1 Verification Loop, Gate 2 Merge, Gate 3 User-Review-Checklist. Ralph Review runs inside the implementation loop (step 7) BEFORE Gate 1.

**Process**:
1. Invoke `/SST3-solo` FIRST — this reloads STANDARDS.md, CLAUDE.md, and WORKFLOW.md. Mandatory even if already loaded. After a compact, these will be gone. This step ensures the agent is fully armed before touching code.
2. Read the GitHub issue line-by-line. Not skim — READ.
3. Implement every phase in the issue's Acceptance Criteria. Commit per file. Push after each phase.
4. Do NOT stop between phases to ask "shall I continue?" — the answer is yes. Proceed.
5. Do NOT create artificial compact breaks. You have 1M tokens. Use them.
6. Run the Verification Loop (Gate 1 below) after all phases are complete. **Audit-phase freshness (MANDATORY first step)**: before ANY audit / wiring / `callers_of` / `impact` query in the Verification Loop, run `mcp__code-review-graph__graph action=update` unconditionally — your solo-branch edits rendered any session-start snapshot stale. Same rule applies at the Stage 5 Post-Implementation Review audit phase (see playbook "Audit-phase freshness" bullet under "Stage 4 — Implementation (Verification Loop)"). Skip only if doc-only diff (exempts all graph checks).
7. Run Ralph Review (Haiku → Sonnet → Opus) — all 3 tiers mandatory. Ralph Review is a CODE DELIVERY VERIFICATION pass — it confirms the issue's Acceptance Criteria were delivered. It is DISTINCT from Stage 5 adversarial audit. Ralph passing does NOT substitute for Stage 5 subagent swarm (TB-3 N36). Model-selection rationale for the three Ralph tiers (Haiku surface / Sonnet logic / Opus deep): see `docs/research/model-selection-haiku-4-5.md`.
8. On Ralph FAIL: fix → restart from Tier 1. On Ralph PASS: proceed to Gate 1.
9. Post checkpoint to issue comment when implementation is complete.

### Gate 1: Verification Loop

Run these checks. Repeat until ALL pass:
- [ ] **Graph-backed diff audit (MANDATORY when graph available per STANDARDS.md "Structural Code Queries")**: read `graph_applicable` from Stage 1 research file — do NOT re-classify (TB-2 carry-forward). If `graph_applicable=false`, skip this checkbox and proceed; if `true`, run `mcp__code-review-graph__review base=<default-branch>` on the diff — always wrapped in a subagent with an UPFRONT warning in the prompt: "Expect 4MB+ JSON output — pipe to file + use `jq`/`python` to slice. Do NOT try to read the full payload." (Round-5 overflow data: 7× across 3 rounds / 144K-11.7M chars.) Feed the returned impact + untested-function list + wide-blast-radius flags into the swarm scope. This determines swarm size + angles, NOT replaces subagents. Subagents still handle semantic / intent / cross-document angles per AP #19 12-moments carve-out. If `review` output surfaces wide-blast-radius files, PRE-ASSIGN Layer-1 subagent angles by impacted hub (one subagent per hub) rather than generic-angle coverage. For hybrid diffs (code + docs): run `review` on the full diff — markdown/YAML/JSON files yield no impact edges, and `review` output tolerates that.
- [ ] **Checkbox-MCP coverage gate (AP #20)**: per canonical definition in `../workflow/WORKFLOW.md` "Verification Loop" — run `mcp__github-checkbox__get_issue_checkboxes` (ToolSearch-bootstrap first if deferred) and confirm every phase-completed checkbox is closed via `update_issue_checkbox` with evidence. Comment-only progress = FAIL. Retroactive in-issue closure within Gate 1 run before declaring clean. Do NOT duplicate the rule here — WORKFLOW.md is canonical.
- [ ] All issue checkboxes verified with evidence (file:line, command output)
- [ ] Overengineering check: simpler solution exists?
- [ ] Architecture reuse check: duplicated instead of reused existing code?
- [ ] Code duplication check: needs deduplication?
- [ ] Fallback policy check: silent failures introduced?
- [ ] Wiring check: all changed code actually called by existing functions/processes? No orphaned code?
- [ ] Regression tests: run project test suite, verify no regressions
- [ ] Quality scan: no inefficiencies, no bottlenecks, no memory leaks, no dead code, STANDARDS.md compliant
- [ ] Ralph Review: confirm all 3 tiers (Haiku/Sonnet/Opus) passed — check issue comments for evidence. If NOT yet run, STOP and run `/SST3-solo` Ralph Review first.
- [ ] **AP #18 Sample Invocation Gate (including TA-7 persistent-state triggers — P1.29 drift fix)**: if the change touches pipeline / backtest / SL1 / SL2 / orchestration / CLI-wiring / cross-module function-arg propagation / **persistent-state write (JSONB schema mutation, SQL literal drift across SET and READ sites, DB column rename, enum-value drift)** → real-CLI sample invocation against real DB documented in issue comment with row-count + downstream-consumer verification. Exit code 0 alone INSUFFICIENT. Mocks MUST assert `call_args.kwargs[...]` explicitly. If NOT in-scope, document the scope-skip reason. Canonical: ANTI-PATTERNS.md #18 + STANDARDS.md "Testing Priority — Workflow Validation Gate" + WORKFLOW.md L96.
- [ ] **Skill-canonical verification gate** (N32 Double-Guardrail — per Guardrails principle): run the invoked skill's own verification checks. Examples: `check_voice_tells.py` exit 0 (voice / blog / CV / job-hunter); eBay 21-field count grep + SMART test evidence; claude-api prompt-caching verify; project-specific pre-commit hooks green. Evidence: pass/fail + output in issue comment.

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

1. Read `../templates/user-review-checklist.md`. Use the TEMPLATE. Do NOT invent your own.
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

**DO**: Read the issue thoroughly. Implement all phases. Commit per file. Push frequently. Run Ralph Review. Run all 3 gates sequentially. Use the template files. Verify every step end-to-end. Keep going until done.
**DON'T**: Stop to ask permission between phases. Create unnecessary compact breaks. Skim the issue. Leave phases incomplete. Fire-and-forget commits without verifying push succeeded. Skip the Verification Loop. Make up your own checklist. Defer the merge. Merge without Ralph evidence.

**SIGN-OFF**: When done, tell the user: "Stage 4 (Implement) complete. All phases implemented, Verification Loop passed, Ralph Review passed, merged to main, user-review-checklist posted. Next: `/Leader 5` (Post-Implementation Review — 100% mandatory subagent swarm)."

---

## Stage 5 — Post-Implementation Review (Subagent Swarm)

Subagents audit everything the main agent produced. Main agent produced the work; subagents verify it. Stage 5 is a POST-IMPLEMENTATION ADVERSARIAL AUDIT — what did the main agent miss? 100% mandatory — every `/Leader` invocation terminates here. It is DISTINCT from Ralph Review (which ran at Stage 4 and verified delivery). Ralph PASS does NOT mean Stage 5 is satisfied — different lens, different class of findings (TB-3 N36).

**Process**:
1. Read `graph_applicable` and `invoked_skill` from the Stage 1 research file — do NOT re-classify (TB-2 carry-forward). If `graph_applicable=true`, run `mcp__code-review-graph__graph action=update` to catch any edits since session start (AP #19 freshness — stale snapshots cause false negatives). Launch subagent swarm (scale to implementation size). Each covers ONE angle with a RESULT block. One of those angles is a graph-backed audit (NOT a replacement — one audit input among several) when graph available per STANDARDS.md "Structural Code Queries": `mcp__code-review-graph__review base=<default-branch>` (use `main` or `master` per repo default) on the diff, wrapped in a subagent with an UPFRONT warning in the prompt: "Expect 4MB+ JSON output — pipe to file + use `jq`/`python` to slice. Do NOT try to read the full payload." Feed the returned impact + untested-function list + wide-blast-radius flags into a subagent prompt. If the `review` output surfaces wide-blast-radius files, PRE-ASSIGN Layer-1 subagent angles by impacted hub (one subagent per hub) rather than generic-angle coverage — hub-anchored angles catch regressions that generic angles miss. Subagent checks whether each flagged item is expected or a regression; main agent verifies against source. Additionally, one subagent angle MUST verify skill-canonical compliance per Double-Guardrail Principle (STANDARDS.md) — the angle reads `invoked_skill` + `skill_canonical_files` from the Stage 1 research file and audits the delivered work against those rules. Same verify-against-source discipline as the graph-backed audit.
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
8. Report to user: findings, fixes, regression test results, final state. Record `last_updated` + `total_nodes` + `embeddings_count` in the Stage 5 checkpoint comment — parity with Stage 1a audit trail (TC-10 S3). Reviewers need the same graph-state audit at Stage 5 entry as at Stage 1 entry.

**DO**: Require specific findings from every subagent (file:line, evidence). Fix everything found. Run regression tests.
**DON'T**: Accept "looks fine" from subagents. Defer fixes. Skip regression tests. Fire-and-forget.

**SIGN-OFF**: When done, tell the user: "Stage 5 (Post-Implementation Review) complete. All work audited, fixes applied, regression tests passed. Issue [URL] is done. Close the issue when satisfied."
