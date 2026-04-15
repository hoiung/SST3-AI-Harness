# SST3 Anti-Patterns

> 18 documented failure modes. Origin: [Issue #79](https://github.com/hoiung/dotfiles/issues/79).

## Anti-Pattern #1: Propagation Failures

**Problem**: Changes in one repo don't reach others, causing inconsistency
**Evidence**: [Issue #79](https://github.com/hoiung/dotfiles/issues/79) (#406 F3.11: stale 2024 percentages stripped — keep the rule, drop the unsourced numbers)
**Root Cause**: Manual propagation, no verification after changes

**Prevention**:
- ✓ DO: Use dotfiles as single source, automated sync via main agent
- ✓ DO: Verify propagation with cross-repo checks (Stage 5)
- ✗ DON'T: Make direct repo edits without updating dotfiles
- ✗ DON'T: Assume propagation worked without verification

**Self-Healing**: If this pattern appears, escalate after 3 occurrences → trigger full cross-repo audit

---

## Anti-Pattern #2: Template Chaos

**Problem**: Too many templates create confusion and inconsistency
**Evidence**: Issue #79
**Root Cause**: Template explosion (67→5 in SST3), variant proliferation

**Prevention**:
- ✓ DO: Use ONE universal template (CLAUDE_TEMPLATE.md)
- ✓ DO: Reject any template variants or customizations
- ✗ DON'T: Create "specialized" templates for edge cases
- ✗ DON'T: Allow repo-specific template modifications

**Self-Healing**: If new templates appear, immediately delete and redirect to CLAUDE_TEMPLATE.md

---

## Anti-Pattern #3: Skipped Verification

**Problem**: Bugs merge because verification stage was skipped
**Evidence**: Issue #79
**Root Cause**: Verification seen as optional, time pressure

**Prevention**:
- ✓ DO: Make Stage 5 mandatory
- ✓ DO: Run automated checks before any merge
- ✗ DON'T: Skip verification for "simple" changes
- ✗ DON'T: Trust manual testing alone

**Self-Healing**: If verification skipped, block merge until Stage 5 completes

---

## Anti-Pattern #4: Documentation Drift

**Problem**: Docs don't match actual implementation
**Evidence**: Issue #79
**Root Cause**: Duplication, cross-references, manual updates

**Prevention**:
- ✓ DO: Single source of truth in dotfiles
- ✓ DO: Auto-generate docs from working code
- ✗ DON'T: Duplicate documentation across repos
- ✗ DON'T: Use cross-references between docs

**Self-Healing**: If drift detected, regenerate from dotfiles source

---

## Anti-Pattern #5: Workflow Shortcuts

Subsumed by AP #3 (Skipped Verification) + AP #6 (Skipped Pre-Commit Validation). Same root cause, same fix. See those.

---

## Anti-Pattern #6: Skipping Pre-Commit Validation

**Problem**: Committing without validating branch hygiene, file counts, or syntax
**Evidence**: [Issue #195](https://github.com/hoiung/dotfiles/issues/195) - Branch contamination (15 unrelated files, 6593 lines) caught in Stage 4 instead of during Verification Loop
**Root Cause**: Verification Loop interpreted as optional, no branch hygiene check

**Prevention**:
- ✓ DO: Run Verification Loop for ALL changes (minimum 1 iteration)
- ✓ DO: Check branch hygiene before every commit (`git log --oneline <branch> ^master`)
- ✓ DO: Verify file count matches plan
- ✓ DO: Run syntax validators and linters
- ✗ DON'T: Skip Verification Loop for "simple" or "obvious" changes
- ✗ DON'T: Assume branch is clean without verification
- ✗ DON'T: Commit without comparing to implementation plan

**Self-Healing**: If branch contamination detected, create clean branch and cherry-pick issue-specific commits

---

## Anti-Pattern #7: Silent Fallbacks & Fake Data

**Problem**: Code uses hardcoded defaults, fake data, or silent fallback behavior when required dependencies/config missing.
**Evidence**: [Issue #269](https://github.com/hoiung/dotfiles/issues/269) — script silently fell back to parsing all headers instead of failing when Stage headers missing. Issue #667: 5 `.get("value", [9])` fallbacks; frontend showed "MVWAP10", backend served MVWAP9. Issue #670/672: `setMarkers()` never called — feature appeared to work but did nothing.
**Root Cause**: Workarounds instead of fail-fast error handling.

**Detection Patterns**:
- `os.getenv('VAR') or '.'` (silent fallback to cwd)
- `try: real_logic() except: return []` (swallowed error)
- `if not specific_condition: use_generic_fallback()` (undocumented behavior change)

**Fix Pattern**:
```python
# BAD: config_file = os.getenv('CONFIG_PATH') or '.'
# GOOD:
config_file = os.getenv('CONFIG_PATH')
if not config_file:
    print("ERROR: CONFIG_PATH not set."); sys.exit(1)
```

**Prevention**:
- ✓ DO: Fail at startup with clear error + fix instructions. Document required vs optional deps.
- ✗ DON'T: Silent fallbacks, degraded execution without warning, default values for critical config.

**Cross-Reference**: See STANDARDS.md "Never Assume — Always Check" and "Fail Fast" sections (Fail Fast, No Silent Fallbacks)

**Self-Healing**: If silent fallbacks detected, replace with explicit error handling and fail-fast validation

**Automated Enforcement**:
```bash
# Run during Stage 4 verification
python SST3/scripts/check-fallbacks.py --severity warning .

# Exit 0 = clean, Exit 1 = violations found
# Use --exclude-dir tests to skip test files
# Use .fallback-allowlist for intentional fallbacks
```

---

## Anti-Pattern #8: Unverifiable Claims & Assumed Facts

**Problem**: Numbers in documentation/issues/CV without a verifiable source — estimates as facts, numbers copied without re-verification, "sounds right" as evidence.
**Evidence**: Unverified agent count propagated across docs as rhetorical framing. Financial figure misquoted as "average" when source said "up to". Both passed review.
**Root Cause**: "Never Assume — Always Check" enforced for code but not documentation metrics.

**Prevention**: Back every number with a reproducible source (command, query, line ref). Label estimates. Re-verify copied numbers. Maintain provenance (`cv-linkedin/METRIC_PROVENANCE.md`).

**Self-Healing**: `git blame` origin → verify or remove → update provenance. See STANDARDS.md "Factual Claims Must Have Provenance" + "User Assertion = Immediate Source Verification".

**Enforcement**: Ralph Review Tier 2 (Sonnet) Evidence Quality + Tier 3 (Opus) Factual Claims Audit. User Review Checklist Section 3.

---

## Anti-Pattern #9: Single-Source Edits (Research Applied Singularly)

**Problem**: Editing a multi-research artefact after consulting only ONE source. The edit silently overrides constraints baked in by every other source. Applies to any domain with multiple referenced docs.

**Evidence**: 2026-04-07/08 CV/LinkedIn — VOICE_PROFILE pass violated HIRER_PROFILE coverage; HIRER_PROFILE pass violated VOICE rhythm. Each pass undid the prior. Same in code: refactor applies one architecture doc without checking type-contract, schema, test-strategy, or perf-budget docs.

**Root Cause**: Reading one doc feels productive; research forms a collective picture — single-source edits collapse it.

**Prevention**:
- ✓ DO: Load ALL mandatory-reading files before the first edit. Check every change against every lens in the SAME pass.
- ✓ DO: Resolve source conflicts EXPLICITLY. Treat new audit output as ADDITIVE, not replacement.
- ✓ DO: List every consulted file in the commit message.
- ✗ DON'T: Read one doc, fix one dimension, ship. Trust one subagent without cross-check. Apply a fix without checking budgets/locked facts/contracts in other docs.

**Self-Healing**: Commit message lists fewer files than mandatory-reading list → revert and redo as single integrated pass.

**Enforcement**: STANDARDS.md "Research Must Be Applied Collectively, Never Singularly". Ralph Review Tier 3 (Opus) cross-source consistency check. Commit message must enumerate every consulted source.

---

## Anti-Pattern #10: Duplicate Rules / Harnesses / Logic (Failure to Search Before Adding)

**Problem**: Creating a new rule/helper/hook/component without checking whether one already exists. Applies to ANY artefact. **Skimming and assuming "it's not there" is the failure mode.**

**Evidence**: 2026-04-07/08 — new memory files re-documented rules already in `cv_linkedin_project.md`, HIRER_PROFILE.md, or job-hunter SKILL.md (e.g. `feedback_one_target_role_only.md`, deleted as duplicate). Same in code: helpers reimplemented in 3 places, hooks duplicated, subagent prompts copy-pasted with drift.

**Prevention**:
- ✓ DO: Grep relevant directories with multiple synonyms BEFORE writing. Read index files (MEMORY.md, STANDARDS.md, ANTI-PATTERNS.md, CLAUDE.md) first.
- ✓ DO: Similar exists → UPDATE in place. Genuinely new → name semantically, link from index in same commit. Conflict → reconcile to one canonical, delete duplicate.
- ✗ DON'T: Skip the search. Copy-paste subagent prompts with minor variations instead of factoring a shared template.

**Self-Healing**: identify canonical (oldest, most-referenced, most-complete) → merge unique content → delete duplicates → repoint references → cross-link in index.

**Enforcement**: STANDARDS.md "Use Existing Before Building" + "Research Must Be Applied Collectively". Ralph Tier 2 duplicate-rule check.

**Documented Exception**: The `dotfiles/SST3/` → `SST3-AI-Harness/` parallel mirror is INTENTIONAL architectural design (scrubbed public mirror, see `memory/project_sst3_dotfiles_vs_harness.md`). Edit BOTH on every SST3 file change. Drift between them is sanitisation, not duplication. Do NOT flag this pair as an AP #10 violation.

---

## Anti-Pattern #11: Stopping to Ask vs Applying Without False-Positive Check

**11a — Stopping to ask**: After finding clear violations, stopping to ask "want me to apply?" wastes a round-trip. Rules already authorise the fix.

**11b — Applying without false-positive check**: Running audit → immediately editing without verifying the "violation" isn't intentional architectural design (defence-in-depth, intentional verbosity, intentional graceful degradation) silently breaks architectural decisions.

**Evidence**: 2026-04-08 — agent presented 12 STANDARDS.md findings and stopped to ask. Rule: dispatch swarm first, then apply; never stop to ask for standards-mandated fixes.

**Prevention**:
- ✓ DO: Dispatch a swarm sized to full coverage (per STANDARDS Subagent Orchestration Discipline) to confirm each violation is NOT architectural design before fixing. Apply immediately once confirmed. Treat audit + sweep + fix + commit as one flow.
- ✗ DON'T: Ask permission for standards-mandated fixes. Apply without false-positive sweep. Skip sweep "to save time".

**Self-Healing**: Fix applied to intentional design → revert + add inline architectural-design comment so future audits skip it.

**Enforcement**: Audit-then-fix flows must include a swarm false-positive sweep. Ralph Review Tier 3 (Opus) checks every audit-driven commit against architectural-design comments.

**Scope distinction (vs Plan Mode by Default)**: STANDARDS.md "Plan Mode by Default" governs *task initiation* (must qualify for immediate execution under 5-min/10-line/reversible criteria, or plan first). AP #11 governs *within-task audit findings* where the standards already mandate the fix. Different scopes, no contradiction. When a task is in execution mode and an audit surfaces a documented violation, apply the fix; do not stop and re-plan.

---

## Anti-Pattern #12: No Observability (Code Without Logs, Metrics, or Audit Trails)

**Problem**: Code that runs without structured logs, metrics, or audit trails. (Silent fallbacks → AP #7. This is about *absence of instrumentation*.) Every silent decision boundary is a future incident.

**Evidence**: Recurring "it just stopped working" incidents. State transitions with no audit trail. Decisions in loops with no log of which branch fired. Production bugs taking days because nothing was instrumented at write time.

**Prevention**:
- ✓ DO: Log every decision boundary, state transition, and external call AT WRITE TIME (structured key=value or JSON). Metrics on counts/durations/ratios. Append-only audit trail for production/money/user-visible state changes. Treat "no log here" as a code smell.
- ✗ DON'T: Empty `except`, bare `pass`, silent `return None`, `continue` on unexpected state. `print()` as logging. Free-text prose in logs. Skip audit trail because "DB has the data" — rows show state, not transition.

**Self-Healing**: Undebuggable incident → instrument FIRST, bugfix second.

**Enforcement**: STANDARDS.md "Observability". Pre-commit hook for `print(` in non-script files, empty `except`, bare `pass`, unannotated `return None`. Ralph Tier 2 observability audit on code commits.

---

## Anti-Pattern #13: Misinterpreting User Authorisation as License to Bypass Process

**Problem**: "okay" / "proceed" / "yes" / "go ahead" treated as license to skip sweeps, Ralph reviews, or other mandated steps. The agent ships shortcuts the user never authorised.

**Evidence**: 2026-04-08 — user said "of course apply", agent skipped the AP #11 false-positive swarm sweep and logged the skip as a "caveat". Rule: "giving green light means follow process" — not bypass it.

**Prevention** (the rule in full): User authorisation NEVER bypasses workflow, process, guardrails, or harnesses. "Proceed" means proceed using the full standard process — never skip verification, sweeps, Ralph review, false-positive check, mandatory reading, or any documented step.
- ✓ DO: Run the full process — every sweep, every gate. If tempted to skip a step, that's the anti-pattern signal. Treat workflow/guardrails as load-bearing.
- ✗ DON'T: Compress "go ahead" into "go ahead without the checks". Log a skipped step as a "caveat". Decide unilaterally a step is unnecessary this time.

**Valid exemptions**: (1) step is explicitly inapplicable, (2) user EXPLICITLY names and waives the step (vague approval ≠ waiver), (3) running the step would violate a higher-priority rule → escalate, don't silently skip.

**Self-Healing**: Catch yourself about to skip → STOP and run the step. Already skipped → run it now, amend the work, don't ship the partial result.

**Enforcement**: STANDARDS.md governs the process. Ralph Review Tier 3 (Opus) checks that every audit-driven commit ran the false-positive sweep. Every commit message that touches standards or anti-patterns must name the sweep that ran or explicitly cite the documented exemption.

---

## Anti-Pattern #14: Stingy / Single-Layer / Trusted-Without-Verification Subagent Use

**14a — Stingy count**: 2-3 subagents when 10-20 needed. Misses 40-60% of issues. Stinginess masquerades as efficiency.

**14b — Single-layer**: One wave treated as ground truth. Different lenses catch different blind spots; one lens = systematic blind spot.

**14c — Trusted without verification**: Main agent treats subagent output as authoritative without reading source. Subagents miss structured data, grep too narrowly, contradict each other. Swarm recommends; main agent verifies; source decides.

**Evidence**: 2026-04-07/08 — Quality DO List deleted based on ONE sonnet subagent's duplication finding; false-positive sweep later restored it.

**The rule**: MANY subagents, LAYERS, different angles per layer. Main agent verifies every finding against source. Document proof method inline.

**Prevention**:
- ✓ DO: Count scaled to cover every directory/file/claim line-by-line. Layer 2 uses DIFFERENT prompt/lens than layer 1. Main agent reads source before applying any change. Document proof method (file:line, command, query) inline. Mark intentional design inline so audits skip it.
- ✗ DON'T: 2-3 subagents "to save time/tokens". Trust single-layer finding without cross-check. Apply without main-agent source verification. Leave claims without documented proof method.

**Self-Healing**: Single-layer finding applied and later wrong → revert → layered swarm → re-evaluate → add inline proof-method so same false-positive doesn't recur.

**Enforcement**: STANDARDS.md "Subagent Orchestration Discipline". Ralph Tier 3 (Opus) checks every audit-driven commit lists at least 2 swarm layers in its source-consultation note.

---

## Anti-Pattern #15: Voice Prose Without iamhoi Markers

**The pattern**: Writing or editing prose in Hoi's voice (CV bullet, LinkedIn About, cover letter paragraph, blog post, profile narrative) without wrapping it in `<!-- iamhoi --> ... <!-- iamhoiend -->` markers. The marker-driven voice guard is default-SKIP — untagged prose ships unprotected, and the next AI-tells contamination won't be caught by pre-commit or CI.

**Why it happens**: Old habit (whole-file scan via `PUBLIC_FACING_GLOBS` legacy whitelist), or writing in a file that happens to be in the whitelist and assuming it's auto-protected, or quoting JD/banned-word examples and getting hit by false positives, or duplicating banned-word lists in a new doc instead of updating `voice_rules.py`.

**Evidence**: 2026-04-07 voice rework destroyed factual accuracy because the sequential voice-then-fact pattern bypassed both the marker convention and the dual-lens rule (AP #9). 2026-04-08 fact rework drifted the voice for the same reason. The marker design was introduced in dotfiles#404 / hoiboy-uk#3 as the load-bearing mechanism that lets voice + hirer + fact lenses all run in the same pass.

**Prevention**:
- ✓ DO: Wrap prose in `<!-- iamhoi --> ... <!-- iamhoiend -->`. Use `<!-- iamhoi-skip --> ... <!-- iamhoi-skipend -->` for quoted JD content / proper-noun usage. Edit `voice_rules.py` AND `cv-linkedin/VOICE_PROFILE.md` Section 8 in the SAME pass when adding a banned word. Re-vendor + drift-cmp when changing canonical.
- ✗ DON'T: Write voice prose untagged. Duplicate banned-word lists. Add KEEP_LIST words to BANNED_WORDS. Bypass the hook with `--no-verify`. Apply voice fixes in isolation from hirer/fact lenses (AP #9 sequential lens failure).

**Self-Healing**: Pre-commit + CI catch unprotected violations only inside marker regions. Untagged regressions surface at user review. When that happens: wrap the offending paragraph in markers, fix the violation inside, re-run hook, document why the section was previously untagged.

**Enforcement**: `check-ai-writing-tells.py` + `check_voice_tells.py` (vendored), `validate.yml` voice-tells job (dotfiles), `ci.yml` voice-tells step (hoiboy-uk), `voice-rules-drift` cmp hook (hoiboy-uk pre-commit). STANDARDS.md "Voice Content Protection (Marker-Driven)" section.

---

## Anti-Pattern #16: Fire-and-Forget Script Execution

**The pattern**: Launching a script / command / subprocess / deployment / test run / commit / push / background process and immediately moving on without verifying it completed, succeeded, or produced the expected effect. Treats "started" as "done". Bypasses every observability surface the codebase has been instrumented with.

**Evidence**: User repeatedly catches this and has to ask "did it work?" / "did you check?" / "what happened?". Hoi 2026-04-08: *"you have a tendency to just fire and forget scripts, when what I need you to do is fire and monitor and ensure no problems... we build observability everywhere, we need you to be our eyes and ears, not just our executioner."*

**Why**: Agent treats `subprocess.run()` exit code as the only signal and ignores stdout/stderr / log files / DB state / file creation / side effects. `run_in_background: true` is particularly prone — BashOutput exists to poll but agent forgets to call it.

**Prevention**:
- ✓ DO: Verify every launch end-to-end — tail logs, check exit code, verify expected output, confirm side effects.
- ✓ DO: Poll `run_in_background` via BashOutput at sensible intervals or set up notification.
- ✓ DO: Verify commits landed, pushes succeeded, CI started, CI finished.
- ✓ DO: Report test runs with pass/fail counts, not just "tests ran".
- ✓ DO: Read subagent output and verify it did what was asked, not assume.
- ✗ DON'T: Treat exit code 0 alone as success. The script may have done nothing.
- ✗ DON'T: Move on after `run_in_background` without polling or notification.
- ✗ DON'T: Make the user ask "did it work?" — that question is a self-trigger to verify NOW.

**Test**: if you cannot answer "what happened?" with specifics, you fired and forgot.

**Self-Healing**: Caught firing-and-forgetting → check the result NOW (tail log, query metric, read output, `gh run view`). Don't wait for the user to ask. Document the verification step in the next commit.

**Enforcement**: STANDARDS.md "Monitor, Don't Fire-and-Forget". Ralph Tier 2 checks every script-invoking commit lists the verification step. AP #12 provides the surfaces; AP #16 enforces reading them.

---

## Anti-Pattern #17: Premature Stopping Mid-Work

**Problem**: Agent stops mid-phase to ask permission, wait for user confirmation, or "check in" when there's no blocker and context is nowhere near the stop threshold. Caused by 200K-era habits ("stop at phase boundary to compact") bleeding into 1M-context sessions, plus over-application of the Claude Code baseline safety prompt ("transparently communicate the action and ask for confirmation before proceeding") to routine work.

**Evidence**: 2026-04-15 — subagents stopped at 50%, 70%, 80% context REMAINING (far below the actual stop threshold) with self-commentary like *"old habit from earlier sessions, user-rule caution that doesn't apply here. Executing — no more stops until 80% context or done."* The agent catches itself, but only after wasting user time.

**Rule — Keep Going Until Done:**
Do not stop mid-phase for permission, confirmation, or a "check in". Stop only for:
1. Context at 80%+ of the model window (800K of 1M, 160K of 200K) — the actual hard threshold
2. Irreversible destructive action needing user consent (force-push, rm -rf, drop table, branch deletion)
3. Genuinely stuck after investigation (not as a first-response-to-friction reflex)
4. Task actually complete

Phase checkpoints post a comment to the Issue — they DO NOT pause work. Post the comment and continue. Warnings at 70% context are informational, not stop signals.

**Threshold update (2026-04-15):** previously documented as "80% warn / 90% stop" from the 200K era. Now 70% warn / 80% stop.

**Do / Don't:**
- ✓ DO: post phase checkpoint to Issue, immediately start next phase
- ✓ DO: warn at 70% context, keep working
- ✓ DO: confirm before destructive actions only
- ✗ DON'T: stop to ask "should I continue?" when nothing destructive is pending
- ✗ DON'T: treat "transparently communicate the action" as "pause and wait"
- ✗ DON'T: stop at 50% / 70% / 80% REMAINING — the 1M window exists to be used

**Self-Healing**: If you catch yourself about to stop without hitting a real threshold → don't write the "I'll pause here" message, just do the next action. If you already stopped → resume immediately on the next turn, note the lapse in the next commit.

**Enforcement**: STANDARDS.md "Keep Going Until Done". All phase templates (`issue-template.md`, `subagent-solo-template.md`) updated to 70%/80% thresholds.

---

## Anti-Pattern #18: Smoke-Tested Pipeline Shipped Without End-to-End Sample Run

**Problem**: Closing a pipeline / backtest / data-processing / orchestration / CLI-wiring issue on the strength of unit tests + smoke tests + synthetic fixtures alone. Smoke validates local code paths; it does NOT validate multi-module workflow wiring across CLI flags → function signatures → DB writes → downstream consumers.

**Evidence (pattern, scrubbed)**: A CLI-threading change added window-aware filtering at one layer of a pipeline but left the pre-flight coverage check at an earlier layer window-agnostic. Unit tests passed (mocks accepted `**kwargs` and silently discarded window args). Synthetic smoke passed (did not exercise the real CLI against real DB). Regression caught operationally by the next phase's first real invocation, NOT by the test suite. Sample invocation on a small liquid basket would have surfaced it before merge.

**Rule — Sample Invocation Validates Workflow Logic**:
For any change that touches pipeline / data-processing / orchestration / CLI-wiring / cross-module function-arg propagation, run an actual end-to-end sample invocation matching the intended user workflow BEFORE closing the issue. Real DB. Real CLI. Real downstream consumers. Unit + smoke tests are necessary but NOT sufficient.

**Scope triggers** (ANY of these → sample invocation mandatory):
- New or modified CLI flags and their threading into downstream function signatures
- Pipeline coverage pre-flights, auto-bootstrap paths, experiment-path logic
- Snapshot / window-scoped / period-scoped code paths
- Multi-module function-arg propagation chains (>1 hop from CLI to DB write)
- Any change where a `**kwargs`-accepting mock could silently hide the regression

**How to apply (MANDATORY in Stage 4 Verification Loop)**:
1. Run real-CLI sample invocation on a small liquid basket (8 items typical) exercising the full pipeline end-to-end.
2. Verify row counts land in DB, downstream consumers succeed, audit queries return OK.
3. Smoke first (cheap, fast). If smoke passes → STILL run the sample. Exit gate = sample succeeds.
4. Assertions MUST verify arg propagation explicitly (`mock.call_args.kwargs["window_start"] == expected`), NOT rely on `**kwargs` swallowing.
5. Add a Stage 5 integration test covering the sample path when the change introduces cross-module signatures or CLI flags.

**Do / Don't**:
- ✓ DO: run small-basket real-CLI sample on every pipeline-touching issue before close
- ✓ DO: assert function-arg propagation with explicit `call_args` checks
- ✓ DO: write a regression integration test when adding/changing cross-module function signatures
- ✗ DON'T: close on unit + smoke alone for pipeline / wiring / CLI changes
- ✗ DON'T: defer the sample run to "the next issue's smoke" — shipped regressions originate there
- ✗ DON'T: rely on mocks that discard kwargs to prove propagation

**Self-Healing**: If you catch yourself about to close a pipeline/wiring issue without running a real sample → run the sample first. If you already closed one → reopen, run the sample, and add the missing regression test in the same fix.

**Enforcement**: STANDARDS.md "Testing Priority — Workflow Validation Gate"; `WORKFLOW.md` Verification Loop (canonical gate); `CLAUDE_TEMPLATE.md` behavioural rule bullet; `issue-template.md` PREREQUISITE CHECKPOINT includes sample-run confirmation; Ralph `sonnet-review.md` AP #18 checklist (three sub-checks covering scope, evidence, and mock-assertion discipline). Note: all five enforcement points are documentation-level + honour-system checklists — there is currently no CI job that blocks a merge when a pipeline-touching diff lacks a sample log. Adding such a CI gate is tracked as a future hardening task.

---

## Pattern Detection

Monitor for these anti-patterns:
1. **Propagation**: Diff between dotfiles and repos > 0
2. **Templates**: File count in */templates/* > 1
3. **Verification**: Commits without Stage 5 logs
4. **Documentation**: Checksum mismatch between docs
5. **Shortcuts**: Direct commits bypassing Solo workflow
6. **Pre-Commit Validation**: Commits without Verification Loop completion

## Escalation Protocol

When anti-pattern detected:
1. First occurrence: Log warning
2. Second occurrence: Alert main agent
3. Third occurrence: Block operations, require manual review
4. Pattern persists: Trigger full system audit (Issue #79 process)

---
