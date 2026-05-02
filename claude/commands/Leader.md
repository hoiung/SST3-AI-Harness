# Leader Mode

Direct instructions from the human leader. NOT suggestions. Orders. Do not skim. Do not summarise. Do not skip steps. Execute exactly as written.

## Guardrails (Apply to ALL Stages)

- **Context budget**: Research phase <30% of context. 80%+ = warn user. 90%+ = STOP and create handover.
- **Post-compact recovery**: If context was compacted mid-stage, re-read this skill file + CLAUDE.md + STANDARDS.md + STANDARDS.md §Per-Stage Feedback Capture (in-flight workflow telemetry) + the active Issue before continuing. Do NOT resume from memory.
- **Branch safety**: NEVER switch branches. Commit and push to the CURRENT branch. Ask the user if you need something from main.
- **Commit discipline**: Commit per file. NEVER `git add -A` or `git add .`.
- **AP #16 Monitor**: Every command, script, test, commit, push — verify end-to-end. Check exit codes, tail logs, confirm side effects. "Started" is not "done".
- **Subagent RESULT block**: Every subagent prompt MUST require a fenced `## RESULT` block at the end of its response:
  ```
  ## RESULT
  mcp_graph_available: yes|no   (FIRST line when subagent discusses graph queries — AP #19)
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
- **Governance Enforcement — Checkbox MCP (AP #20)**: at every Acceptance Criteria checkbox completion → invoke `mcp__github-checkbox__update_issue_checkbox(issue_number, checkbox_text, evidence)` with per-deliverable evidence. Comment-only progress is NOT a substitute. **Before invocation**: check for deferred-tool status and load the schema via `ToolSearch` per STANDARDS.md "MCP Tool Schema Loading" — mandatory, not optional. Canonical evidence-quality patterns: `../reference/tool-selection-guide.md` Example 2.

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
0b. **Prior-feedback ground** (per STANDARDS.md §Per-Stage Feedback Capture): read aggregator output via `bash dotfiles/scripts/leader-feedback-aggregate.sh --report` (markdown — pull "Pending Improvements" + "Top 5 Improvements per Stage" sections). For topic-keyword overlap, run `bash dotfiles/scripts/leader-feedback-aggregate.sh --shape-match <kw1>,<kw2>` and pull top 1-3 referenced feedback files. Pull `improvement` field where `improvement_status: pending` into the Stage 1 /tmp scope file as 'patterns to apply / pitfalls to avoid'. When a prior `pending` improvement is satisfied by this run, mark it `applied_in: <this-issue>` in its source file (closure loop). Token budget ~12K total (report ~3K + at most 3 prior feedback files at ~3K each). Skip-cleanly when index empty (mechanism not yet activated, or first issue post-activation).
1. Check `docs/research/` in the active repo for existing research FIRST. Do not re-derive what exists.
1a. **MANDATORY self-test + status CHECK at Stage 1 top** (#447 Phase 4 update): run `bash dotfiles/scripts/sst3-self-test.sh` FIRST — this is the wrapper-lane regression gate. ANY drift line in the NDJSON (`{"kind":"fixture-drift",...}`) means a wrapper has regressed against its frozen known-answer fixture; **ABORT swarm dispatch immediately**, do not proceed to subagent recall. Recovery procedure: open `solo/wrapper-fix-<bug>` branch (NOT this Issue's branch), reproduce the failing fixture, fix the wrapper, run the self-test until `0 drifted`, push the fix branch through Stage 4 in its own Issue, then resume the original `/Leader` invocation here. After self-test passes, run `bash dotfiles/scripts/sst3-code-status.sh` and record `last_updated` + `file_count` in the research file — audit trail for Stage 5 reviewers, even on 12-moments topics. The wrapper-lane is stateless; every query re-parses on disk, so there is no staleness, no build step, no null/0 decision rule (those applied to the displaced upstream MCP). `sst3-code-update.sh` exists only as a no-op contract-preservation shim. For full A+B+C+D audit (code + doc + sync at once), invoke `/sync-check` skill OR `bash dotfiles/scripts/sst3-check.sh --all` (Phase D Layer-2 orchestrator).
    **Error path (G-1 fix, #444; wrapper-lane note Issue #445; semantics clarified by Issue #456)**: Under the wrapper-lane (Issue #445+), MCP-transport errors no longer apply; wrappers exit with code 127 + the documented stderr contract instead. **Post Issue #456**: exit 127 means the inner engine is **genuinely missing on disk** (npm/cargo/pipx install never ran). Pre-#456 the same code ALSO fired when the engine was on disk but PATH was not propagated to non-interactive shells; that PATH-propagation gap is now closed by `sst3-bash-utils.sh` self-bootstrap. Run `scripts/install.sh` to install missing engines — do NOT add custom PATH workarounds in the calling agent. (Retained for historical context: in the MCP-native phase, distinguish transport-layer disconnect from normal error response. If `config status` returns `MCP error -32000: Connection closed` or stdio-EOF symptom → graph disconnected at the transport layer. See `../dotfiles/docs/guides/code-query-playbook.md` "Connection Closed / Disconnected — Recovery".) For wrapper-lane calls: check stderr; if a wrapper exits non-zero, document `[GRAPH unavailable: <reason>]` in the research file and proceed via subagent-only research per `SST3-solo.md` fallback. "MANDATORY" refers to the CHECK being unconditionally attempted, NOT to halting the workflow when the tool is unavailable — fallback is documented and Ralph-acceptable.
1b. **Pre-swarm wrapper-lane SEED**: if the research topic is structural code in a supported language (see STANDARDS.md "Structural Code Queries"), use the wrapper-lane to DEFINE scope BEFORE dispatching the swarm — not to verify pre-formed scope AFTER. Run `bash dotfiles/scripts/sst3-code-callers.sh <symbol> <lang>` / `bash dotfiles/scripts/sst3-code-callees.sh <function_name> <lang>` / `bash dotfiles/scripts/sst3-code-search.sh '<pattern>' <lang>` on every symbol the USER MENTIONED, plus `bash dotfiles/scripts/sst3-code-impact.sh <base-branch>` on user-named files. Feed the resulting call-site / symbol / blast-radius data into subagent prompts so layer-1 angles are scoped to real evidence, not hypothesis. Wrapper-lane findings SEED the swarm; they do NOT replace its different-angle coverage. **Hybrid topics** (code + docs): run wrapper-lane queries on the code portion ONLY; use subagents for the semantic portion. Record `graph_applicable_files` vs `graph_exempt_files` in the research file. Skip-condition: if topic is semantic / voice / intent / cross-document / non-code (12 subagent-only moments per STANDARDS.md), skip wrapper-lane queries and go to step 2 — the 1a status CHECK still ran unconditionally for audit trail. Record wrapper-lane calls + `last_updated` + `file_count` + one spot-check file:line per query in the /tmp research file. (`search` is keyword-only — there are no embeddings; verify with synonym sweep before any "no match" conclusion.) **Cross-validation rule (#447 Phase 5 — wrapper-lane vs raw recall delta gate)**: BEFORE dispatching the swarm, cross-validate the wrapper-lane SEED against ONE raw-tool subagent on the same query (e.g. wrapper `sst3-code-callers.sh foo python` vs subagent grep `^def foo|foo(`). Compare counts. Delta ≤20%: trust the SEED, dispatch the planned swarm. Delta >20%: wrapper-lane is SUSPECT for this query class — dispatch matched wrapper+raw subagent pairs for layer 1 (one subagent per pair) so the swarm covers both signals; record the delta + final reconciliation in the research file. The 20% threshold is empirical (#445 R4 wrappers landed at 0% delta against raw on structural angles; pre-R4 sat at 17% large-fn recall which is why a 20% bound surfaces drift early).
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

**Per-stage feedback (Layer C; per STANDARDS.md §Per-Stage Feedback Capture)**: write the Stage 1 block to the per-issue feedback file before declaring complete. 10 fields (model / worked / didnt / why / improvement / improvement_status / evidence / friction / rule_self_caught / rule_user_caught), soft-cap guidance per STANDARDS.md, no forward-preference phrasing.

**SIGN-OFF**: When done, tell the user: "Stage 1 (Research) complete. Next: `/Leader 2` (Issue Draft)."

---

## Stage 2 — Issue Draft (/tmp, NOT GitHub)

Create `/tmp/issue_draft_<topic>_<date>.md` FIRST. Do NOT create the GitHub issue yet.

**Process**:
1. Read the `/tmp` research file from Stage 1 AND run `python3 scripts/check-stage1-research-fields.py /tmp/research_<topic>_<date>.md` exit 0 BEFORE proceeding (#460 Phase 4 — Stage 1 metadata validator gate). Validator failure = block Stage 2 dispatch until the Stage 1 file declares `graph_applicable` + `invoked_skill` + `skill_canonical_files` per the carry-forward contract.
1b. **Graph scope-completeness recipe** (structural-code topics in supported languages — see playbook "Stage-Mapped Recipes" Stage 2 section): for every function/hook/class named in the scope, run `bash dotfiles/scripts/sst3-code-callers.sh <symbol> <lang>` and compare the count to what Stage 1 research claimed. More call sites than research flagged = expand scope. For every "X doesn't exist" claim, run `bash dotfiles/scripts/sst3-code-search.sh '<pattern>' <lang>` (literal identifier when embeddings unavailable). Record every query + target + count + one spot-check file:line in the draft's References section. Skip if topic is semantic / non-code / one of the 12 subagent-only moments.
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
<!-- Gate, not audit — see AP #23 delimiter (curated trigger list verifies named conditions; comprehensive-walk template does not apply). -->
4a. **Mirror-lane mapping (#460 Phase 8 W5 — AP #9 single-source-edits enforcement)**: when the draft touches CLAUDE.md (template lane A) OR any file tracked in `SST3/drift-manifest.json:vendored_files` (mirror lane B), include a "Mirror Lanes Traversed" subsection in the draft listing the canonical edit locus + the consumer files that will be auto-propagated. Trigger conditions: SST3 section edits → Lane A; new/edited canonical script → Lane B; new GitHub Actions workflow with cross-repo applicability → Lane B. The Stage 4 implementation MUST run BOTH lanes' validators before Gate 1.
5. Launch subagents (layer 1) to check draft scope against research findings. Full coverage — every finding must map to a scope item.
6. Launch subagents (layer 2, DIFFERENT angle) to check for gaps, overengineering, and false positives.
7. Everything needs to be fixed. No excuses, no deferring. No "high priority" or "low priority". ALL must be fixed unless confirmed false positive (document WHY with evidence).
8. Present `/tmp` file path to user for review.

**Skill-canonical at draft-write time (N32 Double-Guardrail)**: while authoring the draft, walk every `## ` and `### ` heading of the invoked-skill canonical (per Stage 1 metadata `skill_canonical_files`) and verify the draft does not violate any rule in any section. Use the comprehensive-walk template per STANDARDS.md "Skill-Canonical Audit Template (Comprehensive Walk)". This is the author-time counterpart to Stage 3's subagent verification. Do NOT shortcut to "verify A, B, C" curated examples — that's the recall-bounded failure mode documented in ANTI-PATTERNS.md AP #23.

**DO**: Follow the template verbatim. Include every mandatory section. Show before/after for every change.
**DON'T**: Create the GitHub issue. Skip sections. Paraphrase quality mantras. Defer fixes.

**Per-stage feedback (Layer C; per STANDARDS.md §Per-Stage Feedback Capture)**: write the Stage 2 block to the per-issue feedback file before declaring complete (10 fields per STANDARDS.md).

**SIGN-OFF**: When done, tell the user: "Stage 2 (Issue Draft) complete. Next: `/Leader 3` (Sanity Check + GitHub Issue Creation)."

---

## Stage 3 — Sanity Check + GitHub Issue Creation

The draft exists. Now verify it is correct before it becomes the contract.

**Process**:
1. Read the `/tmp` issue draft from Stage 2. Read `graph_applicable` from the Stage 1 research file — do NOT re-classify independently (TB-2 single-declaration-carries-forward).
2. Launch subagents (minimum 3, scale up). **Multi-skill dispatch (AP #23)**: when invoked-skill canonical token cost exceeds ~5K (e.g. 3+ skills × deep canonicals), split the skill-canonical compliance angle into multiple subagents — one per canonical file — so each comprehensive-walk stays within its context budget. This is orchestrator-side guidance for the Leader; the per-subagent template (what each subagent receives verbatim) lives in STANDARDS.md "Skill-Canonical Audit Template (Comprehensive Walk)". Each verifies independently:
   - **Scope vs Audit**: 100% of research findings captured? Nothing missing? No gaps?
   - **No overengineering**: Scoped items that solve problems that don't exist? Remove them.
   - **Chat history check**: Review the conversation. Did we discuss and agree on things NOT in the issue? Check for forgotten agreements.
   - **Opposite-scoping check**: Are we scoping the OPPOSITE of what was agreed? This failure mode is documented. Verify explicitly.
   - **Dead/obsolete/legacy code**: Did the audit find cleanup targets? Are they in the issue? Structural layer: `bash dotfiles/scripts/sst3-code-large.sh 200 <lang>` + `bash dotfiles/scripts/sst3-code-impact.sh <base-branch>` on the area the Issue edits, when graph available and fresh (pre-query gate per STANDARDS.md "Structural Code Queries"). Surfaces dead-code / wide-blast-radius candidates that should be in scope. Subagent still verifies intent (intentional duplication vs accidental). **Raw-tool counter-query (#447 Phase 5 — Stage 3 sanity check)**: for any structural scope item the wrapper-lane surfaced (callers count, large-fn list, dead-code candidates, blast-radius), dispatch ONE subagent to run the equivalent raw tool (grep / ast-grep direct / find) on the same target. Compute delta. **Delta >50% wrapper/raw discrepancy = BLOCK Issue creation** until reconciled — either the wrapper missed instances (recall drift, file a separate fix Issue first) or the raw tool double-counted (false positive in raw, document and proceed). Record the counter-query + delta + reconciliation in the draft's References section.
   - **All scope in issue BODY**: Nothing in comments. Everything in the body.
   - **Skill-canonical compliance** (Double-Guardrail Principle — N32): subagent uses the comprehensive-walk template per STANDARDS.md "Skill-Canonical Audit Template (Comprehensive Walk)". Reads the invoked-skill canonical file(s) per Stage 1 metadata `invoked_skill` + `skill_canonical_files`, walks EVERY `## ` and `### ` heading, returns per-section [PASS|FAIL|N/A] with file:line evidence tagged by `source_file`. RESULT block extends with `canonicals_walked` + `section_failures` + `fallback_applied`. Do NOT pre-filter by which rules "look relevant". See ANTI-PATTERNS.md AP #23 for the curator-bounded-recall failure mode this template prevents.
   - **Mirror-lane mapping completeness** (#460 Phase 8 W5 — AP #9): subagent verifies that any draft AC touching CLAUDE.md or SST3-canonical code includes its "Mirror Lanes Traversed" subsection (per Stage 2 step 4a) AND that the propagation tooling (`propagate-template.py` for Lane A, `propagate-mirrors.py` for Lane B) is named explicitly in the AC's verification step. Drafts that edit canonical-mirrored surfaces without naming the lane fail this angle.
3. Layer 2 subagents (DIFFERENT prompt): cross-check layer 1 findings. Specifically verify no false positives and no false negatives in scope.
4. Each subagent returns a RESULT block. Main agent reviews ALL results.
5. If ANY subagent finds a gap: fix the draft. Do NOT create the issue with known gaps.
6. Once ALL subagents agree the draft is complete and accurate: create the GitHub issue using the verified draft verbatim.
7. Report the issue URL to the user.
8. **CONTEXT CHECK REMINDER**: After reporting the issue URL, tell the user their current context usage percentage and advise: "If context is above 50%, consider compacting before invoking `/Leader 4` — Stage 4 re-invokes `/SST3-solo` which reloads STANDARDS.md + CLAUDE.md + WORKFLOW.md + the Issue, so a compact here loses nothing and gives maximum room for implementation."

**DO**: Investigate when subagents disagree. Fix gaps before creating the issue. Verify against chat history. Remind user about context before Stage 4.
**DON'T**: Rubber-stamp. Pick the convenient answer when subagents conflict. Put scope in comments.

**Per-stage feedback (Layer C; per STANDARDS.md §Per-Stage Feedback Capture)**: write the Stage 3 block to the per-issue feedback file before declaring complete (10 fields per STANDARDS.md).

**SIGN-OFF**: When done, tell the user: "Stage 3 (Sanity Check) complete. Issue created: [URL]. Context usage: X%. If above 50%, consider compacting before next step. Next: `/Leader 4` (Implement — re-invokes /SST3-solo)."

---

## Stage 4 — Implement (includes Verification Loop + Merge + User-Review-Checklist)

The issue is created and verified. Now implement it. Do NOT stop. Do NOT pause for compact breaks — you have a 1M context window, use it. The only reason to stop is if you hit 90% context usage, in which case create a handover.

Stage 4 has three sequential gates after the implementation phases complete: Gate 1 Verification Loop, Gate 2 Merge, Gate 3 User-Review-Checklist. Ralph Review runs inside the implementation loop (step 7) BEFORE Gate 1.

**Process**:
1. Invoke `/SST3-solo` FIRST — this reloads STANDARDS.md, CLAUDE.md, and WORKFLOW.md. Mandatory even if already loaded. After a compact, these will be gone. This step ensures the agent is fully armed before touching code.
2. Read the GitHub issue line-by-line. Not skim — READ.
3. Implement every phase in the issue's Acceptance Criteria. Commit per file. Push after each phase.
3a. **Layer 1 — Phase-boundary checkbox close-out (AP #20 Tier A, MANDATORY in execute mode only)**: BEFORE moving from phase N to phase N+1, run `mcp__github-checkbox__update_issue_checkbox(issue_number, checkbox_text, evidence)` for every completed Tier A Acceptance Criteria checkbox in phase N. (Plan mode = read-only per CLAUDE.md; MCP write tools only fire when the user has explicitly entered execute mode via `/Leader 4` or `/SST3-solo` invocation.) Interleaved with the phase commits, not batched. Evidence MUST use canonical patterns from `../reference/tool-selection-guide.md` Example 2: file:line / commit hash / command+output / subagent RESULT comment-id. If the tool is deferred: `ToolSearch(query="select:mcp__github-checkbox__update_issue_checkbox,mcp__github-checkbox__get_issue_checkboxes")` first, then invoke. Comment-only progress is a direct AP #20 violation. **No phase boundary may be crossed with a Tier A `[ ]` box behind it.** (Canonical rule: ANTI-PATTERNS.md AP #20; evidence patterns: `../reference/tool-selection-guide.md` Example 2.) Complemented by Gate 1 Layer 3 final-check below.
4. Do NOT stop between phases to ask "shall I continue?" — the answer is yes. Proceed.
5. Do NOT create artificial compact breaks. You have 1M tokens. Use them.
6. Run the Verification Loop (Gate 1 below) after all phases are complete. **Audit-phase freshness (MANDATORY first step)**: before ANY audit / wiring / `callers_of` / `impact` query in the Verification Loop, run `bash dotfiles/scripts/sst3-code-update.sh` unconditionally — your solo-branch edits rendered any session-start snapshot stale. Same rule applies at the Stage 5 Post-Implementation Review audit phase (see playbook "Audit-phase freshness" bullet under "Stage 4 — Implementation (Verification Loop)"). Skip only if doc-only diff (exempts all graph checks).
7. Run Ralph Review (Haiku → Sonnet → Opus) — all 3 tiers mandatory. Ralph Review is a CODE DELIVERY VERIFICATION pass — it confirms the issue's Acceptance Criteria were delivered. It is DISTINCT from Stage 5 adversarial audit. Ralph passing does NOT substitute for Stage 5 subagent swarm (TB-3 N36). Model-selection rationale for the three Ralph tiers (Haiku surface / Sonnet logic / Opus deep): see `docs/research/model-selection-haiku-4-5.md`. **Terminology note**: Ralph "tiers" (sequential Haiku → Sonnet → Opus, restart on fail) are distinct from Stage 5 subagent "layers" (parallel Layer 1 + Layer 2, different angles per AP #14). Ralph is code-delivery verification; Stage 5 layers are post-implementation adversarial audit. AP #20 "Layer 1/2/3" enforcement in this skill body (step 3a + pre-Gate-1 paragraph + Gate 1 bullet) is a THIRD separate use of "Layer" terminology — execution-time enforcement gates, not review-time subagent dispatches. **Tier 3 Opus raw-tool counter-query rule (#447 Phase 5)**: when ANY Tier 3 finding depends on `../scripts/sst3-code-*.sh` output (recall counts, large-fn lists, callers, blast-radius, untested-py results), Opus MUST dispatch ≥1 raw-tool counter-query subagent on the same target before signing PASS. The counter-query result + delta vs wrapper-lane output is recorded in the Tier 3 review comment. Skipping this when wrapper-lane output is load-bearing = Tier 3 FAIL.
8. On Ralph FAIL: fix → restart from Tier 1. On Ralph PASS: proceed to Gate 1.
9. Post checkpoint to issue comment when implementation is complete.

**Layer 2 — Pre-Gate-1 double-check (MANDATORY before entering the Verification Loop)**: if the tool is deferred, `ToolSearch(query="select:mcp__github-checkbox__get_issue_checkboxes,mcp__github-checkbox__update_issue_checkbox")` first. Then run `mcp__github-checkbox__get_issue_checkboxes` and confirm every phase-completed Tier A checkbox is already `[x]` with canonical evidence (file:line / commit hash / command+output / subagent RESULT comment-id per `../reference/tool-selection-guide.md` Example 2). If any Tier A box corresponds to completed work but is still `[ ]`, close it NOW via `update_issue_checkbox` with canonical evidence — do NOT defer to Gate 1. Gate 1 is the FINAL check, not the first; it must enter from a clean baseline. (Complements Layer 1 at phase-boundary above; Gate 1 below is Layer 3 final-check.)

### Gate 1: Verification Loop

Run these checks. Repeat until ALL pass:
- [ ] **Graph-backed diff audit (MANDATORY when graph available per STANDARDS.md "Structural Code Queries")**: read `graph_applicable` from Stage 1 research file — do NOT re-classify (TB-2 carry-forward). If `graph_applicable=false`, skip this checkbox and proceed; if `true`, run `bash dotfiles/scripts/sst3-code-review.sh <default-branch>` on the diff — always wrapped in a subagent with an UPFRONT warning in the prompt: "Expect 4MB+ JSON output — pipe to file + use `jq`/`python` to slice. Do NOT try to read the full payload." (Round-5 overflow data: 7× across 3 rounds / 144K-11.7M chars.) Feed the returned impact + untested-function list + wide-blast-radius flags into the swarm scope. This determines swarm size + angles, NOT replaces subagents. Subagents still handle semantic / intent / cross-document angles per AP #19 12-moments carve-out. If `review` output surfaces wide-blast-radius files, PRE-ASSIGN Layer-1 subagent angles by impacted hub (one subagent per hub) rather than generic-angle coverage. For hybrid diffs (code + docs): run `review` on the full diff — markdown/YAML/JSON files yield no impact edges, and `review` output tolerates that. **Internal-consistency check (#447 Phase 5)**: if the `review` JSON's `impact` array is EMPTY but the diff is non-trivial (>5 functions touched per `sst3-code-impact.sh`), treat the wrapper output as SUSPECT — dispatch ONE raw-tool subagent (grep / ast-grep direct) to compute the impact independently, compare, and gate on the delta. An empty review JSON paired with a real diff is a known wrapper failure mode that the self-test gate cannot fully cover (engine-broken vs engine-missing on the orchestrator path).
- [ ] **Layer 3 — Checkbox-MCP coverage gate (AP #20 FINAL CHECK)**: per canonical definition in `../workflow/WORKFLOW.md` "Verification Loop" — (1) `ToolSearch(query="select:mcp__github-checkbox__get_issue_checkboxes,mcp__github-checkbox__update_issue_checkbox")` if deferred; (2) run `get_issue_checkboxes` and list every Tier A box still `[ ]` that corresponds to completed work; (3) for each such box, invoke `update_issue_checkbox(issue_number, exact_checkbox_text, evidence)` with canonical evidence (file:line / commit hash / command+output / subagent RESULT comment-id per `../reference/tool-selection-guide.md` Example 2); (4) re-run `get_issue_checkboxes` and confirm every Tier A box is now `[x]`. Comment-only progress = FAIL. Tier B batched-closures applied here are acceptable per Phase 9 cadence (ANTI-PATTERNS.md AP #20). Do NOT duplicate the rule here — WORKFLOW.md is canonical; only the procedure is expanded.
- [ ] All issue checkboxes verified with evidence (file:line, command output)
- [ ] Overengineering check: simpler solution exists?
- [ ] Architecture reuse check: duplicated instead of reused existing code?
- [ ] Code duplication check: needs deduplication?
- [ ] Fallback policy check: silent failures introduced?
- [ ] Wiring check: all changed code actually called by existing functions/processes? No orphaned code?
- [ ] Regression tests: run project test suite, verify no regressions
- [ ] Quality scan: no inefficiencies, no bottlenecks, no memory leaks, no dead code, STANDARDS.md compliant
- [ ] Ralph Review: confirm all 3 tiers (Haiku/Sonnet/Opus) passed — check issue comments for evidence. If NOT yet run, STOP and run `/SST3-solo` Ralph Review first.
- [ ] **AP #18 Sample Invocation Gate (including TA-7 persistent-state triggers — P1.29 drift fix; #447 Phase 5 wrapper-script trigger)**: if the change touches pipeline / backtest / SL1 / SL2 / orchestration / CLI-wiring / cross-module function-arg propagation / **persistent-state write (JSONB schema mutation, SQL literal drift across SET and READ sites, DB column rename, enum-value drift)** / **any `../scripts/sst3-*.sh` wrapper change (#447 trigger)** → real-CLI sample invocation against ≥3 repo shapes (auto_pb / job-hunter / dotfiles) + raw-tool counter-query for recall comparison, documented in issue comment with row-count + downstream-consumer verification + wrapper-vs-raw delta. Exit code 0 alone INSUFFICIENT. Mocks MUST assert `call_args.kwargs[...]` explicitly. If NOT in-scope, document the scope-skip reason. Canonical: ANTI-PATTERNS.md #18 (with the per-shape table added in #447 Phase 7) + STANDARDS.md "Testing Priority — Workflow Validation Gate" + WORKFLOW.md L96.
<!-- Gate, not audit — comprehensive-walk template per AP #23 does not apply (verifies named conditions, not multi-section canonical). -->
- [ ] **Skill-canonical verification gate** (N32 Double-Guardrail — per Guardrails principle): run the invoked skill's own verification checks. Examples: `check-ai-writing-tells.py` exit 0 (voice / blog / CV / job-hunter); eBay 21-field count grep + SMART test evidence; claude-api prompt-caching verify; project-specific pre-commit hooks green. Evidence: pass/fail + output in issue comment.
- [ ] **Mirror-lane verification (Lane A + Lane B)** — per WORKFLOW.md "Verification Loop" Mirror-lane verification rule (#460 Phase 8 W5): canonical authoritative; do NOT duplicate the spec here.
- [ ] **Mirror-lane Lane A + Lane B exit 0** — three separate invocations all exit 0 (per WORKFLOW.md L105 — `--dry-run` and `--validate` are mutually exclusive in propagate-mirrors.py argparse, so they must run as separate commands): (1) `python3 scripts/propagate-template.py --all --dry-run` (Lane A), (2) `python3 scripts/propagate-mirrors.py --dry-run` (Lane B drift-check), (3) `python3 scripts/propagate-mirrors.py --validate` (Lane B manifest-validate). Skip-clean if no canonical-mirrored surface touched.

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

**Per-stage feedback (Layer C; per STANDARDS.md §Per-Stage Feedback Capture)**: write the Stage 4 block to the per-issue feedback file before declaring complete. Stage 4 sub-structure: `worked` / `didnt` carry per-Ralph-tier sub-bullets; `friction` records `ralph_restarts: <N>` + per-tier outcomes.

**SIGN-OFF**: When done, tell the user: "Stage 4 (Implement) complete. All phases implemented, Verification Loop passed, Ralph Review passed, merged to main, user-review-checklist posted. Next: `/Leader 5` (Post-Implementation Review — 100% mandatory subagent swarm)."

---

## Stage 5 — Post-Implementation Review (Subagent Swarm)

Subagents audit everything the main agent produced. Main agent produced the work; subagents verify it. Stage 5 is a POST-IMPLEMENTATION ADVERSARIAL AUDIT — what did the main agent miss? 100% mandatory — every `/Leader` invocation terminates here. It is DISTINCT from Ralph Review (which ran at Stage 4 and verified delivery). Ralph PASS does NOT mean Stage 5 is satisfied — different lens, different class of findings (TB-3 N36).

**Process**:
1. Read `graph_applicable` and `invoked_skill` from the Stage 1 research file — do NOT re-classify (TB-2 carry-forward). If `graph_applicable=true`, run `bash dotfiles/scripts/sst3-code-update.sh` to catch any edits since session start (AP #19 freshness — stale snapshots cause false negatives). Launch subagent swarm (scale to implementation size). Each covers ONE angle with a RESULT block. One of those angles is a graph-backed audit (NOT a replacement — one audit input among several) when graph available per STANDARDS.md "Structural Code Queries": `bash dotfiles/scripts/sst3-code-review.sh <default-branch>` (use `main` or `master` per repo default) on the diff, wrapped in a subagent with an UPFRONT warning in the prompt: "Expect 4MB+ JSON output — pipe to file + use `jq`/`python` to slice. Do NOT try to read the full payload." Feed the returned impact + untested-function list + wide-blast-radius flags into a subagent prompt. If the `review` output surfaces wide-blast-radius files, PRE-ASSIGN Layer-1 subagent angles by impacted hub (one subagent per hub) rather than generic-angle coverage — hub-anchored angles catch regressions that generic angles miss. Subagent checks whether each flagged item is expected or a regression; main agent verifies against source. Additionally, one subagent angle MUST verify skill-canonical compliance per Double-Guardrail Principle (STANDARDS.md) — the angle uses the comprehensive-walk template per STANDARDS.md "Skill-Canonical Audit Template (Comprehensive Walk)", reads `invoked_skill` + `skill_canonical_files` from the Stage 1 research file, walks every `## ` and `### ` heading of each canonical file against the DELIVERED work (commits + diff), and returns per-section [PASS|FAIL|N/A] with file:line evidence tagged by `source_file`. RESULT block extends with `canonicals_walked` + `section_failures` + `fallback_applied`. Same verify-against-source discipline as the graph-backed audit. See ANTI-PATTERNS.md AP #23.
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
   - **Checkbox-coverage audit (AP #20)**: Proof of Work entries in issue body match every `[x]` box (per STANDARDS.md "Governance Evidence Signal (Canonical)"); Tier A interleave verified against solo-branch `git log` (entry order vs commit order) per opus-review.md Governance Drift Audit (lines 23-28). Any Tier A batching against commit cadence = FAIL and must be flagged in Stage 5 findings.
   - **Mirror-lane post-merge regression check (#460 Phase 8 W5)**: confirm both lanes (Lane A `propagate-template.py --all --dry-run` exit 0; Lane B `propagate-mirrors.py --validate` exit 0) STILL pass post-merge. If a consumer drifted between merge and Stage 5 (e.g. parallel work landed there), surface in findings.
2. Layer 2 subagents (DIFFERENT angle): cross-check layer 1. Specifically look for false negatives (problems layer 1 missed). **Raw-tools-only requirement (#447 Phase 5)**: at least ONE Layer-2 subagent angle MUST use RAW tools ONLY — direct grep / direct ast-grep / direct find / git log — and explicitly prohibit `sst3-*.sh` invocation. RESULT block must include `wrapper_invoked: no` and one concrete `single highest-impact fix` finding. This is the audit-time counter-balance to wrapper-lane recall drift: when Stage 4 Verification Loop, Ralph Tier 3, and Stage 5 Layer-1 all use the same wrapper, the swarm becomes blind to wrapper bugs. The raw-only Layer-2 angle is the failsafe.
3. Main agent reviews ALL RESULT blocks. Verify findings against source.
4. Fix ALL problems. No deferrals. No "low priority". All fixed unless confirmed false positive (document why with evidence).
5. If fixes were applied: run regression tests AFTER the fixes. This is mandatory — fixing code can introduce new regressions. Verify no regressions before declaring clean.
6. If fixes applied: commit, push, update the issue.
7. If no fixes needed: run regression tests anyway to confirm clean state.
7a.0. **MANDATORY pre-completeness /tmp sweep** (#469 Phase 4): run `bash dotfiles/scripts/sweep-parked-feedback.sh <issue-number> [--repo <repo>]` BEFORE the existing 7a completeness gate. Exit 0 mandatory; on non-zero (BLOCK class hit), parked feedback exists in /tmp and MUST be applied to canonical (`dotfiles/SST3-metrics/leader-feedback/feedback-<repo>-<issue>.md`) before sign-off. NEVER auto-apply (branch-safety + stale-parked-drift risk per Stage 1 F6) — surface to operator with the suggested apply commands the script prints, then resume. WARN class (HANDOVER files) + INFO class (sst3-feedback-test-* tempdirs) are advisory and do NOT gate sign-off; apply WARN class at operator discretion.
7a. **MANDATORY pre-sign-off completeness gate** (#460 Phase 7 W4 Layer A): run `bash scripts/leader-stage5-completeness-check.sh <issue-number>` BEFORE the sign-off comment is posted. Exit 0 mandatory; on FAIL, fix the missing invariant(s) and re-run. JSON summary captured in the Stage 5 checkpoint comment for audit trail. Layer B post-flight failsafe (#460 Phase 7b GitHub Actions workflow `stage5-completeness.yml`) replays the same gate server-side after the comment is posted — both are mandatory; neither replaces the other.
8. Report to user: findings, fixes, regression test results, final state. Record `last_updated` + `file_count` in the Stage 5 checkpoint comment — parity with Stage 1a audit trail (TC-10 S3). Reviewers need the same wrapper-lane status audit at Stage 5 entry as at Stage 1 entry.

**DO**: Require specific findings from every subagent (file:line, evidence). Fix everything found. Run regression tests.
**DON'T**: Accept "looks fine" from subagents. Defer fixes. Skip regression tests. Fire-and-forget. Create new GitHub issues autonomously — propose Stage 5 findings as comments on the parent issue; creating new issues requires explicit user authorization in chat (AP #21, added #431 Phase 2b).

**Per-stage feedback (Layer C; per STANDARDS.md §Per-Stage Feedback Capture)**: write the Stage 5 block to the per-issue feedback file before declaring complete (10 fields per STANDARDS.md). After writing, update frontmatter `stages_logged` to include 5 + bump `last_updated`; aggregator regenerates index automatically on next commit.

**SIGN-OFF**: When done, tell the user: "Stage 5 (Post-Implementation Review) complete. All work audited, fixes applied, regression tests passed. Issue [URL] is done. Close the issue when satisfied."
