# SST3 Anti-Patterns

> 26 documented failure modes. Origin: Issue #79.

<!-- stages: 4 -->
## Anti-Pattern #1: Propagation Failures

**Problem**: Changes in one repo don't reach others, causing inconsistency
**Evidence**: Issue #79, Issue #417 (Ralph file drift to SST3-AI-Harness mirror, caught only by post-closure sanity check)
**Root Cause**: Canonical-side edits without propagation — no hook previously fired in dotfiles when SST3 files changed

**Prevention (automated — Issue #418)**:
- `../dotfiles/SST3/drift-manifest.json` lists every vendored file with required transforms (or `divergent + mirror_sha256` for hand-authored structural rewrites)
- `../scripts/propagate-mirrors.py --validate` runs in dotfiles pre-commit — for `transforms` mode files, fails when canonical edit is staged without the mirror synced. **Caveat**: `divergent` mode compares mirror sha256 against the manifest-recorded hash only — canonical content never enters the comparison. Hand-edit divergent mirror copies in the same commit and run `--apply` to refresh the hash.
- `../scripts/check-mirror-drift.py` runs in each mirror pre-commit — fails when mirror drifted from canonical after expected transforms, OR (divergent mode) when mirror sha256 no longer matches the recorded hash
- `../scripts/propagate-mirrors.py --apply` syncs transform-mode mirrors AND refreshes divergent-mode hashes; error messages from both hooks include the exact invocation
- New canonical files: validator warns unless the file is in `unmirrored_canonical_files` allow-list or has a mirror entry

**Prevention (behavioural — still apply alongside automation)**:
- ✓ DO: Edit canonical in dotfiles/SST3/, propagate via script, never hand-edit mirrors
- ✓ DO: Verify per-phase Ralph Review catches any silent bypass
- ✗ DON'T: Make direct mirror edits without updating canonical
- ✗ DON'T: Use `SKIP=<hook-id> git commit` without filing an issue for the underlying false positive

**Self-Healing**: Automated hooks catch drift on commit. Residual occurrences → escalate after 3 → trigger full cross-repo audit.

---

<!-- stages: 2 -->
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

<!-- stages: 4 -->
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

<!-- stages: 4 -->
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

<!-- stages: 4 -->
## Anti-Pattern #5: Workflow Shortcuts

**See AP #3 + AP #6 — subsumed.**

[Historical: original AP #5 ("Workflow Shortcuts") covered skipped verification + skipped pre-commit validation as one pattern; split into AP #3 + AP #6 for separate enforcement. `git log --grep="AP #5"` for full history.]

---

<!-- stages: 4 -->
## Anti-Pattern #6: Skipping Pre-Commit Validation

**Problem**: Committing without validating branch hygiene, file counts, or syntax
**Evidence**: Issue #195 - Branch contamination (15 unrelated files, 6593 lines) caught in Stage 4 instead of during Verification Loop
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

<!-- stages: 4 -->
## Anti-Pattern #7: Silent Fallbacks & Fake Data

**Problem**: Code uses hardcoded defaults, fake data, or silent fallback behavior when required dependencies/config missing.
**Evidence**: Issue #269 — script silently fell back to parsing all headers instead of failing when Stage headers missing. Issue #667: 5 `.get("value", [9])` fallbacks; frontend showed "MVWAP10", backend served MVWAP9. Issue #670/672: `setMarkers()` never called — feature appeared to work but did nothing.
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
python scripts/check-fallbacks.py --severity warning .

# Exit 0 = clean, Exit 1 = violations found
# Use --exclude-dir tests to skip test files
# Use .fallback-allowlist for intentional fallbacks
```

---

<!-- stages: 4 -->
## Anti-Pattern #8: Unverifiable Claims & Assumed Facts

**Problem**: Numbers in documentation/issues/CV without a verifiable source — estimates as facts, numbers copied without re-verification, "sounds right" as evidence.
**Evidence**: Unverified agent count propagated across docs as rhetorical framing. Financial figure misquoted as "average" when source said "up to". Both passed review.
**Root Cause**: "Never Assume — Always Check" enforced for code but not documentation metrics.

**Prevention**: Back every number with a reproducible source (command, query, line ref). Label estimates. Re-verify copied numbers. Maintain provenance (`~/DevProjects/voice-doc-repo/cv-linkedin/METRIC_PROVENANCE.md`).

**Self-Healing**: `git blame` origin → verify or remove → update provenance. See STANDARDS.md "Factual Claims Must Have Provenance" + "User Assertion = Immediate Source Verification".

**Enforcement**: Ralph Review Tier 2 (Sonnet) Evidence Quality + Tier 3 (Opus) Factual Claims Audit. User Review Checklist Section 3.

---

<!-- stages: 1 -->
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

<!-- stages: 4 -->
## Anti-Pattern #10: Duplicate Rules / Harnesses / Logic (Failure to Search Before Adding)

**Problem**: Creating a new rule/helper/hook/component without checking whether one already exists. Applies to ANY artefact. **Skimming and assuming "it's not there" is the failure mode.**

**Evidence**: 2026-04-07/08 — new memory files re-documented rules already in `cv_linkedin_project.md`, HIRER_PROFILE.md, or voice-doc-repo SKILL.md (e.g. `feedback_one_target_role_only.md`, deleted as duplicate). Same in code: helpers reimplemented in 3 places, hooks duplicated, subagent prompts copy-pasted with drift.

**Prevention**:
- ✓ DO: Grep relevant directories with multiple synonyms BEFORE writing. Read index files (MEMORY.md, STANDARDS.md, ANTI-PATTERNS.md, CLAUDE.md) first.
- ✓ DO: Similar exists → UPDATE in place. Genuinely new → name semantically, link from index in same commit. Conflict → reconcile to one canonical, delete duplicate.
- ✗ DON'T: Skip the search. Copy-paste subagent prompts with minor variations instead of factoring a shared template.

**Self-Healing**: identify canonical (oldest, most-referenced, most-complete) → merge unique content → delete duplicates → repoint references → cross-link in index.

**Enforcement**: STANDARDS.md "Use Existing Before Building" + "Research Must Be Applied Collectively". Ralph Tier 2 duplicate-rule check.

**Documented Exception**: The `../dotfiles/SST3/` → `SST3-AI-Harness/` parallel mirror is INTENTIONAL architectural design (scrubbed public mirror, see `memory/project_sst3_dotfiles_vs_harness.md`). Edit BOTH on every SST3 file change. Drift between them is sanitisation, not duplication. Do NOT flag this pair as an AP #10 violation.

---

<!-- stages: 4 -->
## Anti-Pattern #11: Stopping to Ask vs Applying Without False-Positive Check

**See AP #14c (main agent verifies swarm output against source) + AP #13 (User authorisation NEVER bypasses workflow).**

[Historical: AP #11a = stopping-to-ask for standards-mandated fixes; AP #11b = applying without false-positive sweep against intentional architectural design. Both behaviours subsumed under AP #14c's source-verification discipline + AP #13's "Proceed ≠ Bypass" rule. Scope distinction vs Plan Mode (task-initiation vs within-task audit findings) covered by STANDARDS.md "Plan Mode by Default" + execution-mode contract. `git log --grep="AP #11"` for full history.]

---

<!-- stages: 4 -->
## Anti-Pattern #12: No Observability (Code Without Logs, Metrics, or Audit Trails)

**Problem**: Code that runs without structured logs, metrics, or audit trails. (Silent fallbacks → AP #7. This is about *absence of instrumentation*.) Every silent decision boundary is a future incident.

**Evidence**: Recurring "it just stopped working" incidents. State transitions with no audit trail. Decisions in loops with no log of which branch fired. Production bugs taking days because nothing was instrumented at write time.

**Prevention**:
- ✓ DO: Log every decision boundary, state transition, and external call AT WRITE TIME (structured key=value or JSON). Metrics on counts/durations/ratios. Append-only audit trail for production/money/user-visible state changes. Treat "no log here" as a code smell.
- ✗ DON'T: Empty `except`, bare `pass`, silent `return None`, `continue` on unexpected state. `print()` as logging. Free-text prose in logs. Skip audit trail because "DB has the data" — rows show state, not transition.

**Self-Healing**: Undebuggable incident → instrument FIRST, bugfix second.

**Enforcement**: STANDARDS.md "Observability". Pre-commit hook for `print(` in non-script files, empty `except`, bare `pass`, unannotated `return None`. Ralph Tier 2 observability audit on code commits.

---

<!-- stages: 4 -->
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

<!-- stages: 4 -->
## Anti-Pattern #14: Stingy / Single-Layer / Trusted-Without-Verification Subagent Use

**14a — Stingy count**: 2-3 subagents when 10-20 needed. Misses 40-60% of issues. Stinginess masquerades as efficiency.

**14b — Single-layer**: One wave treated as ground truth. Different lenses catch different blind spots; one lens = systematic blind spot.

**14c — Trusted without verification**: Main agent treats subagent output as authoritative without reading source. Subagents miss structured data, grep too narrowly, contradict each other. Swarm recommends; main agent verifies; source decides.

**14d — Scope-gap blindness (Stage 1 research specific)** (Theme 8, #477): Layer-1 Stage 1 swarm covers the named scope but misses scope-adjacent surfaces (genuine gaps) AND/OR cites legacy implementations when modern equivalents already exist (false positives). Single-layer Stage 1 research = systematic blind spot. Failure mode: Issues drafted from incomplete scope, leading to mid-Stage-2 AC rewrites or post-Stage-4 false-positive bug-hunts. Prevention: Stage 1 swarm dispatches a Layer-2 adversarial gap-finder subagent (different prompt than Layer-1) with the explicit task: "Layer-1 found X, Y, Z. Find 3 things they missed — either (a) false-positive claims already covered by modern equivalents, or (b) genuine gaps not yet surfaced." Main agent verifies Layer-2 corrections against source before accepting them (per 14c). Cross-reference: Leader.md Stage 1 step 2a + STANDARDS.md "Stage 1 Layer-2 Adversarial Gap-Finder Discipline".

**14e — Sibling-fix-pattern enumeration discipline (pattern-class extension)** (dotfiles#495 Ralph Tier 3 + Stage 5 L1-G): when the scope of an Issue extends a regex / glob / pattern class across multiple files (e.g. adding `worktree-solo+issue-*` recognition alongside existing `solo/issue-*`), the implementation phase MUST enumerate every site of the class via raw grep AT SCOPE TIME (Stage 1 or Stage 2 latest) and either fix all OR document the intentional non-fix in the same commit. Partial-fix is silent worktree-blindness (or class-blindness) on canonical paths. This is the most-frequent 14d instantiation: 3-of-4-files-updated-symmetrically-1-missed pattern. **Mechanism**: Stage 1 identifies the canonical pattern → runs `grep -rnE '<class-pattern>' SST3/ scripts/ claude/ tests/ .github/ --include='*.py' --include='*.sh' --include='*.yml' --include='*.md'` with synonym sweeps → classifies every match as (a) canonical-aligned, (b) intentionally narrower (with WHY), or (c) BUG (silent class-blindness). Class-(c) hits are in-scope ACs; partial-fix is not an option. Stage 4 Verification Loop re-runs the same enumeration and gates on count-drift (generalisation of AP #24 marker-substring enumeration from string-literals to pattern-classes). Cost: 2-5 minutes grep + triage. Benefit: avoids 1-2 Ralph restart cycles or a Stage 5 fix-phase. Cross-reference: AP #24 (marker-substring enumeration is the same discipline at string-literal granularity), STANDARDS.md "Marker-Substring Discipline" (Leader Stage 1 step 2.1).

**Evidence**: 2026-04-07/08 — Quality DO List deleted based on ONE sonnet subagent's duplication finding; false-positive sweep later restored it. **2026-05-05 (#477 research)** — initial 8-theme scope from Stage 1 swarm missed 6 candidate themes (9-14, ~31-42% pending-entry coverage gap); C1 false-negative sweep subagent recovered the gap and surfaced themes 9+10 for inclusion. Without C1 (Layer-2-style gap-finder), the rollup would have shipped covering only themes 1-8 of the 10 needed. **2026-05-19 (dotfiles#495)** — pattern class `^(?:solo/|worktree-solo\+)issue-(\d+)-` was extended across 4 files (cadence-gate BRANCH_RE + branch-guard `is_solo()` + metrics-feedback SOLO_BRANCH_RE) but missed `sst3-tier-a-auto-tick.py:82 parse_issue_from_branch` (Ralph Tier 3 caught after Verification Loop) + missed `.github/workflows/tier-a-auto-tick.yml:20 branches:` GHA trigger (Stage 5 L1-G caught post-merge). Two distinct sites missed in one Issue = 14e (sibling-fix-pattern enumeration discipline) instantiation. Both fixes landed: `35669c1` (parse_issue_from_branch) + `464c6be` (GHA trigger).

**The rule**: MANY subagents, LAYERS, different angles per layer. Main agent verifies every finding against source. Document proof method inline.

**Prevention**:
- ✓ DO: Count scaled to cover every directory/file/claim line-by-line. Layer 2 uses DIFFERENT prompt/lens than layer 1. Main agent reads source before applying any change. Document proof method (file:line, command, query) inline. Mark intentional design inline so audits skip it.
- ✗ DON'T: 2-3 subagents "to save time/tokens". Trust single-layer finding without cross-check. Apply without main-agent source verification. Leave claims without documented proof method.

**Self-Healing**: Single-layer finding applied and later wrong → revert → layered swarm → re-evaluate → add inline proof-method so same false-positive doesn't recur.

**Enforcement**: STANDARDS.md "Subagent Orchestration Discipline". Ralph Tier 3 (Opus) checks every audit-driven commit lists at least 2 swarm layers in its source-consultation note.

---

<!-- impact-roi-carve-out -->

<!-- stages: always -->
## Anti-Pattern #15: Voice Prose Without iamhoi Markers

**The pattern**: Writing or editing prose in the operator's voice (CV bullet, LinkedIn About, cover letter paragraph, blog post, profile narrative) without wrapping it in `<!-- iamhoi --> ... <!-- iamhoiend -->` markers. The marker-driven voice guard is default-SKIP — untagged prose ships unprotected, and the next AI-tells contamination won't be caught by pre-commit or CI.

**Why it happens**: Old habit (whole-file scan via `PUBLIC_FACING_GLOBS` legacy whitelist), or writing in a file that happens to be in the whitelist and assuming it's auto-protected, or quoting JD/banned-word examples and getting hit by false positives, or duplicating banned-word lists in a new doc instead of updating `voice_rules.py`.

**Evidence**: 2026-04-07 voice rework destroyed factual accuracy because the sequential voice-then-fact pattern bypassed both the marker convention and the dual-lens rule (AP #9). 2026-04-08 fact rework drifted the voice for the same reason. The marker design was introduced in dotfiles#404 / hoiboy-uk#3 as the load-bearing mechanism that lets voice + hirer + fact lenses all run in the same pass.

**Prevention**:
- ✓ DO: Wrap prose in `<!-- iamhoi --> ... <!-- iamhoiend -->`. Use `<!-- iamhoi-skip --> ... <!-- iamhoi-skipend -->` for quoted JD content / proper-noun usage. Edit `voice_rules.py` AND `~/DevProjects/voice-doc-repo/cv-linkedin/VOICE_PROFILE.md` Section 8 in the SAME pass when adding a banned word. Re-vendor + drift-cmp when changing canonical.
- ✗ DON'T: Write voice prose untagged. Duplicate banned-word lists. Add KEEP_LIST words to BANNED_WORDS. Bypass the hook with `--no-verify`. Apply voice fixes in isolation from hirer/fact lenses (AP #9 sequential lens failure).

**Self-Healing**: Pre-commit + CI catch unprotected violations only inside marker regions. Untagged regressions surface at user review. When that happens: wrap the offending paragraph in markers, fix the violation inside, re-run hook, document why the section was previously untagged.

**Enforcement**: `scripts/check-ai-writing-tells.py` (canonical, unified `--mode {cv,blog}` post-#460; byte-identical mirror across hoiboy-uk, voice-doc-repo, voice-staging, SST3-AI-Harness), `validate.yml` voice-tells job (dotfiles, `--mode cv`), `ci.yml` voice-tells step (hoiboy-uk, `--mode blog --check-only-new`), `voice-rules-drift` cmp hook (hoiboy-uk pre-commit). STANDARDS.md "Voice Content Protection (Marker-Driven)" section.

---

<!-- stages: 4 -->
## Anti-Pattern #16: Fire-and-Forget Script Execution

**The pattern**: Launching a script / command / subprocess / deployment / test run / commit / push / background process and immediately moving on without verifying it completed, succeeded, or produced the expected effect. Treats "started" as "done". Bypasses every observability surface the codebase has been instrumented with.

**Evidence**: User repeatedly catches this and has to ask "did it work?" / "did you check?" / "what happened?". the operator 2026-04-08: *"you have a tendency to just fire and forget scripts, when what I need you to do is fire and monitor and ensure no problems... we build observability everywhere, we need you to be our eyes and ears, not just our executioner."*

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

<!-- stages: 4 -->
## Anti-Pattern #17: Premature Stopping Mid-Work

**Problem**: Agent stops mid-phase to ask permission, wait for user confirmation, or "check in" when there's no blocker and context is nowhere near the stop threshold. Caused by 200K-era habits ("stop at phase boundary to compact") bleeding into 1M-context sessions, plus over-application of the Claude Code baseline safety prompt ("transparently communicate the action and ask for confirmation before proceeding") to routine work.

**Evidence**: 2026-04-15 — subagents were stopping at 50%, 70%, 80% context REMAINING (far below the actual stop threshold) with self-commentary like *"old habit from earlier sessions, user-rule caution that doesn't apply here. Executing — no more stops until 80% context or done."* The agent catches itself, but only after wasting user time. User quote: *"they are stopping randomly for no reason... it's like 80%, 70%, 50% remaining, yet they keep stupidly stopping"*.

**Rule — Keep Going Until Done:**
Do not stop mid-phase for permission, confirmation, or a "check in". Stop only for:
1. Context at 80%+ of the model window (800K of 1M, 160K of 200K) — the actual hard threshold
2. Irreversible destructive action needing user consent (force-push, rm -rf, drop table, branch deletion)
3. Genuinely stuck after investigation (not as a first-response-to-friction reflex)
4. Task actually complete

Phase checkpoints post a comment to the Issue — they DO NOT pause work. Post the comment and continue. Warnings at 70% context are informational, not stop signals.

**Threshold update (2026-04-15):** previously documented as "80% warn / 90% stop" from the 200K era. Now 70% warn / 80% stop. Reason: 80%+ of 1M (>800K) is where degradation becomes severe; the 10-point earlier warning gives enough runway to wrap up cleanly.

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

<!-- stages: 4 -->
## Anti-Pattern #18: Smoke-Tested Pipeline Shipped Without End-to-End Sample Run (Workflow-Tier validation)

> **Three-Tier placement** (STANDARDS.md "Three-Tier Testing Framework"): this AP is the **Workflow Tier** gate — the assembled component (pipeline / orchestration / CLI-wiring) runs end-to-end. The distinct **E2E / System Tier** (the whole system, real DB + real downstream consumers, environmental drift) is **AP #26 "E2E System Verification"**. The **Unit Tier** primitive is the call-seam check (STANDARDS.md "Test-Prod Call Coverage Discipline"). The three compose; none substitutes for another.

**Problem**: Closing a pipeline / backtest / SL1 / SL2 / orchestration / CLI-wiring issue on the strength of unit tests + smoke tests + synthetic fixtures alone. Smoke validates local code paths; it does NOT validate multi-module workflow wiring across CLI flags → function signatures → DB writes → downstream consumers.

**Evidence**: 2026-04-15 — Issue #1424 merged after green unit tests and synthetic smoke. Shipped a workflow regression: `check_sl1_coverage` remained window-agnostic (production-path `is_production=TRUE` join) while the downstream `_fetch_sl1_optimal_mvwaps_batch` became window-aware (exact-match `window_start`/`window_end`). Pre-flight incorrectly reported coverage, auto-SL1 skipped, downstream fetch rejected the mismatched rows with `SL1WindowMismatchError`. Caught operationally by Issue #1426 Phase 1 Step 0 (pipeline_operations op_id=2501 aborted: "SL1 promoted 0 winners for 8 tickers"), NOT by the test suite. Unit tests mocked `**kwargs` and never asserted window propagation. User quote: *"I need you to run samples of backtests to ensure whatever you build fucking works. Smoke tests ok for small logics, but it doesn't test workflow logics."*

**Rule — Sample Invocation Validates Workflow Logic**:
For any change that touches pipeline / backtest / SL1 / SL2 / orchestration / CLI-wiring / cross-module function-arg propagation, run an actual end-to-end sample invocation matching the intended user workflow BEFORE closing the issue. Real DB. Real CLI. Real downstream consumers. Unit + smoke tests are necessary but NOT sufficient.

**Service/backend scope triggers** (ANY of these → sample invocation mandatory; auto_pb-shape canonical):
- New or modified CLI flags and their threading into downstream function signatures
- SL1 / SL2 / backtest / queue-orchestrator wiring changes
- Pipeline operations tracker, coverage pre-flights, auto-bootstrap paths
- Snapshot-suffix / window-scoped / experiment-path logic
- Multi-module function-arg propagation chains (>1 hop from CLI to DB write)
- Any change where a `**kwargs`-accepting mock could silently hide the regression
- Any change to `../scripts/sst3-*.sh` (#447 Phase 5+6 wrapper-script trigger)
- **Idempotency re-run paths** (#477 Phase 5 AC 5.1a, dotfiles#474 evidence): for changes claiming idempotency or feature-detect logic (install-path scripts, bootstrap guards, "if X already configured: skip" branches), the sample invocation MUST cover BOTH the first-install path AND the re-run-with-feature-already-present path. Single-direction sample (only first install) hides the bug class where the re-run branch silently corrupts already-good state.
- **Documentation cross-reference resolution** (#477 Phase 5 AC 5.1b, dotfiles#474 evidence): for infrastructure-shape work (homelab bootstrap, runbook scripts, multi-node setup), Stage 5 swarm MUST include an angle that walks every script-path / URL / file-reference / cross-link in the Issue's docs and confirms each resolves (`ls <path>` exit 0, `curl -fsI <url>` HTTP 2xx, `grep -F <ref> <target>` exit 0). Surfaces dangling references that ship with no immediate failure but break next runner.
- **Every-return-path wiring** (#477 Phase 5 AC 5.1c, Issue #1451 evidence): for cache-read or guard-helper additions (functions whose job is "check state and return early"), Stage 4 must enumerate every `return` statement in the guarded function via `grep -n "return" <file>` and confirm each return path either (a) emits the new instrumentation/cache-write OR (b) is documented as exempt with rationale. Missing return-path = silent skip of the new behaviour on the missed branch.

**Per-shape recipe table** (#447 Phase 7 — codifies what already works across the 6 repo shapes; auto_pb is shape "Service" canonical above):

| Shape | Sample artefact | Real-downstream | "8-ticker basket" analogue | Scope triggers | Safety constraints | Tier coverage (Unit / Workflow / E2E) |
|---|---|---|---|---|---|---|
| **Service** (auto_pb-shape: backend pipeline + DB + queue) | `project-a/scripts/sample_invocation_issue<N>.py` (real CLI, real DB, real queue) | Postgres rows present, contamination audit passes, downstream consumer (SL1 fetch / queue tail) succeeds | 8-ticker liquid basket | CLI flag / SL1 / SL2 / queue-orchestrator / pipeline-tracker / cross-module arg propagation | Never touch production positions from E2E tests; RTH-only for IBKR-mediated tests; chunked not monolithic backtests | Workflow+E2E (sample_invocation = component wiring + real DB/queue system); Unit = repo pytest suite (separate, not this recipe) |
| **Docs-only** (research notes / runbooks / handover memory) | `/tmp/sample_<topic>_<date>.md` showing 1 representative path traversed end-to-end (frontmatter validated, related_code paths resolve, every claim has a file:line provenance) | `bash dotfiles/scripts/sst3-doc-frontmatter.sh --strict` exits 0 + `sst3-doc-links.sh` exits 0 + `sst3-sync-related-code.sh` exits 0 on every changed `.md` | n/a — read every file the change touches end-to-end, not a sample basket | Frontmatter add/change, related_code link change, runbook step add/change | No fabricated numbers/dates; every claim backed by file:line / commit / URL | Workflow (sst3-doc-* on every changed .md = the doc component); Unit = per-file frontmatter/link validate; E2E n/a (no runtime system) |
| **Static-blog** (hoiboy-uk Hugo content) | `hoiboy-uk/scripts/pre-publish.sh` output (Hugo build + lychee on rendered HTML — NOT raw markdown) | `public/posts/<slug>/index.html` renders with no broken links, voice-guard passes (`check-ai-writing-tells.py --mode blog --check-only-new` exit 0), banned-words clean (`voice_rules.py` exit 0) | Build ALL drafts (`hugo --buildDrafts`) before publish so cross-links resolve | New post, voice-affecting edit, image-asset add (Drive subfolder hero), cross-link to other post | Publish requires EXPLICIT user approval ("publish it" / "let's go live"); never auto-push to main of hoiboy-uk; Drive case-insensitive collision check (NTFS via WSL); no em dashes | Workflow (Hugo build + lychee on rendered HTML = site builds) + E2E (live URL post-publish smoke); Unit = per-file voice-guard/banned-words |
| **Config-heavy** (dotfiles, package.json + .github/scripts setups) | Pre-commit dry-run `/tmp/precommit_sample_<date>.txt` showing every modified hook fires + statusline syntax-check + propagate-template.py runs clean across all consumer repos | All consumer repos pass `check-claude-template-propagation`; `propagate-template.py` exits 0 with `5/7 repositories updated successfully`; statusline `node -c` clean | Run pre-commit against the changed file glob + 1 file from each consumer repo | New pre-commit hook, statusline edit, settings.json change, propagate-template / propagate-mirrors edit | Never commit secrets to public repo; secret-scan before issue body posts; mirror-drift hazard documented when canonical changes | Workflow (pre-commit dry-run + propagate across consumers = harness component) + E2E (all consumer repos pass propagation); Unit = statusline node -c / jq |
| **Infra-as-code** (.github/workflows, install.ps1, runbooks) | One workflow run on a non-default branch with `act` (local) OR PR-trigger run captured to `/tmp/ci_run_<workflow>_<date>.log` showing every step exits 0 | CI badge green on solo branch; `act -l` lists the new workflow; install.ps1 dry-run on a clean Windows VM (or PowerShell `-WhatIf`) | n/a — exercise every code path the workflow added (matrix, conditional, secret-using job) | New workflow, new install step, new conditional gate, new secret consumer | Never modify CI/CD pipelines without dry-run; treat workflow YAML as production code | Workflow (one full workflow run, every step exit 0); E2E (CI green on branch / install.ps1 dry-run on clean VM); Unit = act -l / yaml-lint |
| **GAS** (Google Apps Script — project-b, future projects) | `project-b/scripts/sample_test.gs` runs against the test project URL; outputs identical to live project URL when the same input is fed | Test project sheet shows expected rows; live project URL invocation against a sandbox sheet matches | n/a — exercise the test/live project pair with one real input row before merging | Trigger change, sheet schema change, deployed-as-add-on edit | Test project for rehearsal, live project for production; never edit live project directly; GAS deploys are atomic + irreversible | Workflow (test-project URL run); E2E (live-project URL parity on a sandbox sheet); Unit = single function output assertion |
| **Homelab-bootstrap shape** (single-node provisioning, operator-initiated) | Operator-private consumer-repo phase-gate script — multi-invariant hardware + push-model checks | Master-side verifier script exit 0 + multi-port reachability | Per-invariant test scope is operator-private | New node, OS-level config change, push-model orchestration edit | Wired-only convention; lab-role only for auto-login; secret-management policy is operator-private | E2E + Workflow + Unit (full invariant catalog + script names + hostname patterns are in the operator-private consumer repo CLAUDE.md) |
| **Pre-publication research-staging shape** (voice-guarded private staging before publish) | Operator-private consumer-repo sample-invocation — 6-step voice-guard + secret-scan + frontmatter chain | `check-ai-writing-tells.py --mode blog --no-check-only-new` exit 0 + iamhoi-marker balance + frontmatter validator | Run the 6-step gate against one representative prep file | New research file, draft-state transition, publish candidate | Drafts stay private until all gates pass; auto-promotion forbidden | Workflow + Unit + E2E (full sample-invocation recipe in operator-private consumer repo CLAUDE.md) |

**How to apply (MANDATORY in Stage 4 Verification Loop)**:
1. Run real-CLI sample invocation on a small liquid basket (8 tickers typical) exercising the full pipeline end-to-end.
2. Verify row counts land in DB, contamination audit passes, downstream consumers succeed.
3. Smoke first (cheap, fast). If smoke passes → STILL run the sample. Exit gate = sample succeeds.
4. Assertions MUST verify arg propagation explicitly (`mock.call_args.kwargs["window_start"] == expected`), NOT rely on `**kwargs` swallowing.
5. Add a Stage 5 integration test covering the sample path when the change introduces cross-module signatures or CLI flags.

**Do / Don't**:
- ✓ DO: run 8-ticker real-CLI sample on every pipeline-touching issue before close
- ✓ DO: assert function-arg propagation with explicit `call_args` checks
- ✓ DO: write a regression integration test when adding/changing cross-module function signatures
- ✗ DON'T: close on unit + smoke alone for pipeline / wiring / CLI changes
- ✗ DON'T: defer the sample run to "the next issue's smoke" — that is how #1424 shipped broken
- ✗ DON'T: rely on mocks that discard kwargs to prove propagation

**Self-Healing**: If you catch yourself about to close a pipeline/wiring issue without running a real sample → run the sample first. If you already closed one → reopen, run the sample, and add the missing Workflow-Tier test (the integration / sample-invocation coverage that would have caught it — STANDARDS.md "Three-Tier Testing Framework"; not a bare "regression test", which is the union suite, not a single tier) in the same fix.

**Enforcement**: STANDARDS.md "Testing Priority — Workflow Validation Gate"; `WORKFLOW.md` Verification Loop (canonical gate); `CLAUDE_TEMPLATE.md` behavioural rule bullet; `issue-template.md` PREREQUISITE CHECKPOINT includes sample-run confirmation; Ralph `sonnet-review.md` AP #18 checklist (three sub-checks covering scope, evidence, and mock-assertion discipline). Note: all five enforcement points are documentation-level + honour-system checklists — there is currently no CI job that blocks a merge when a pipeline-touching diff lacks a sample log. Adding such a CI gate is tracked as a future hardening task.

---

<!-- stages: 4 -->
## Anti-Pattern #19: Structural Question Answered By Grep Alone, Or Wrapper-Lane Result Trusted Without Source Check

**Lineage note**: this AP originated under the deprecated daemon-MCP that #445 displaced; the canonical interface is now the stateless wrapper-lane (`bash dotfiles/scripts/sst3-code-*.sh`) — no database, no embeddings (`sst3-code-search.sh` is keyword-only by design), no staleness (every call re-parses on disk). Wrapper-lane queries are the documented first step; documented grep / subagent fallback is the EXPECTED path, never a degradation.

**Pattern (two sides of one coin)**:
- (a) **Under-use**: dispatching an Explore subagent or running a multi-pass grep to answer a purely structural question (who calls X? callers/callees? blast radius of editing Y? dead functions? tests for Z?) in a wrapper-lane-supported language (Python, TypeScript, TSX, JavaScript, Rust), when a single `bash dotfiles/scripts/sst3-code-*.sh` call would answer it authoritatively in sub-second time. This is the wrapper-lane instance of AP #10 ("Failure to Search Before Adding" / grep-before-writing).
- (b) **Over-trust**: taking a wrapper-lane result at face value — especially a "no results" response — without a source spot-check. Silent failure modes include: unsupported-language drop (YAML/SQL/shell edits are invisible to the ast-grep engine), cross-language boundary (Py→HTTP→Rust contract), and keyword-fallback masquerading as a semantic match (`sst3-code-search.sh` is ripgrep/ast-grep keyword-only — there are no embeddings; synonym-sweep before any "no match" conclusion). This is the wrapper-lane instance of AP #11b ("Applying without false-positive check") + AP #14c ("Main agent verifies swarm output against source").

**12 subagent-only moments (the wrapper-lane carve-out scope — STANDARDS.md "Structural Code Queries" references this list as canonical)**:
1. Voice Content Protection + AI-tells — STANDARDS.md "Voice Content Protection (Marker-Driven)" + `../scripts/voice_rules.py`
2. Intentional-vs-accidental architecture — STANDARDS.md "Subagent Orchestration Discipline" + AP #11b false-positive sweep
3. Research Applied Collectively (cross-lens) — STANDARDS.md "Research Must Be Applied Collectively, Never Singularly"
4. Chat-history scope-drift / opposite-scoping — WORKFLOW.md Stage 3
5. False-positive sweep for confirmed violations — AP #11, `user-review-checklist.md` §7
6. Scope vs audit 100% alignment — WORKFLOW.md Stage 3, `issue-template.md` AC section
7. Overengineering / out-of-scope detection — WORKFLOW.md Verification Loop, `issue-template.md` Cleanup Requirements
8. Design rationale explanation — STANDARDS.md "Use Existing Before Building"
9. Factual claims provenance validation — STANDARDS.md "Factual Claims Must Have Provenance" + "User Assertion = Immediate Source Verification"
10. YAML/JSON/SQL/shell/TOML/Dockerfile/Jinja/HTML/CSS semantic audits — STANDARDS.md "Structural Code Queries" unsupported-languages list
11. Markdown voice-prose AI-tells — STANDARDS.md "Voice Content Protection (Marker-Driven)", AP #15
12. AC prose → code file:line evidence mapping — WORKFLOW.md Stage 4, `user-review-checklist.md` §1

**How to apply, dynamic-dispatch 5 subtypes, Ralph tier-split enforcement, RESULT-block discipline, fallback recipes, `mcp_graph_available` field rule, "wrapper-lane available" precise definition**: canonical procedure lives in STANDARDS.md "Structural Code Queries" (pre-query gate + three-signal contract + raw-tool cross-validation moments + AI-agent fallback heuristic + RESULT-block first-line rule + Issue #456 exit-127 semantics); `../reference/tool-selection-guide.md` "Decision Tree: Code-Understanding Queries" (4-quadrant matrix); `../dotfiles/docs/guides/code-query-playbook.md` (dynamic-dispatch 5-subtype belt-and-braces at L454, fallback recipes, synonym sweeps, cadence). Ralph haiku/sonnet/opus review files contain per-tier under-use + over-trust enforcement criteria (haiku=under-use evidence gate, sonnet=under-use+over-trust logic check, opus=full compliance).

**Self-Healing**: caught reaching for `Agent(Explore)` on a who-calls question in a supported language with the wrapper-lane available → stop, run `bash dotfiles/scripts/sst3-code-callers.sh` first, narrow the subagent prompt with the result. Caught trusting a "no results" without spot-checking → read one matching file from the area and confirm, then proceed.

**Cross-reference**: AP #10 (grep-before-writing), AP #11b (false-positive sweep), AP #14c (main agent verifies swarm output against source). AP #19 extends those disciplines to wrapper-lane tool output.

---

<!-- stages: 4 -->
## Anti-Pattern #20: Comment-Only Progress Tracking Without Checkbox+Evidence

**Pattern**: Reporting Acceptance Criteria completion via narrative comment ("Phase 2 done, all tests pass") instead of invoking `mcp__github-checkbox__update_issue_checkbox(issue_number, checkbox_text, evidence)` per checkbox. The Issue body — the permanent scope contract — remains a sea of `[ ]` while completion lives only in comment history, which is easy to re-read out of order, hard to audit, and impossible to reconcile against original scope without manual cross-referencing.

**Why it happens**:
- The MCP tool schema is **deferred** by the Claude Code harness and the agent sees only the tool name — calling it directly errors out with `InputValidationError`, so the agent falls back to comments without ever loading the schema via `ToolSearch`. (Canonical fix: STANDARDS.md "MCP Tool Schema Loading".)
- Active workflow prompts (Leader.md, SST3-solo.md) historically lacked a strong "MUST invoke" directive; strong wording lived only in `../archive/ORCHESTRATOR.md:738-763` (archived historical source; canonical post-#429 location is `../reference/tool-selection-guide.md` Example 2).
- Model regressions — commit `b9cf036` (2026-04-08, Opus 4.6) cut the canonical `Example 1` + `Example 2` blocks from `../reference/tool-selection-guide.md`, removing the copy-paste template agents relied on. Restored in #429.
- 1M-context "Keep Going Until Done" (AP #17) paradigm encouraged batched narrative over per-deliverable governance updates — the failure mode this AP documents explicitly.

**Evidence (measurable governance drift — 2026-04-21 audit)**:
- `hoiung/project-a#1346` (closed): 209 checkboxes, 0 checked, no body-PATCH events
- `hoiung/project-a#1353` (closed): 100 checkboxes, 0 checked, 6 comment checkpoints only
- `hoiung/project-a#1359` (closed): 137 checkboxes, 0 checked
- `hoiung/project-a#1364` (closed): 143 checkboxes, 0 checked
- **589 unchecked acceptance criteria across completed work** — no per-checkbox evidence trail.

**Relationship to AP #17 (Keep Going Until Done)**:

AP #17 and AP #20 are **complementary, not contradictory**. AP #17 means: do not stop to ask permission between phases — keep working until done or a real blocker. AP #20 means: as each Acceptance Criterion completes, update the checkbox with evidence via MCP. Combined: **keep going AND update-as-you-go — never batch-report at phase end via narrative comment**. An agent that stops mid-work to batch checkbox updates is violating AP #17; an agent that keeps going but reports only in comments is violating AP #20. Both must hold at once.

**How to apply**:
- At every Acceptance Criteria completion → invoke `mcp__github-checkbox__update_issue_checkbox(issue_number, checkbox_text, evidence)` with evidence matching the canonical patterns in `../reference/tool-selection-guide.md` "Example 2: Stage 4 Checkbox Update".
- If the tool returns `InputValidationError` (deferred schema), load via `ToolSearch(select:mcp__github-checkbox__update_issue_checkbox,...)` per STANDARDS.md "MCP Tool Schema Loading" — never silent-fallback to comments.
- Comment checkpoints SUPPLEMENT checkbox updates (narrative context, blockers, next steps) — they do NOT REPLACE them.
- Stage 4 Verification Loop "Checkbox-MCP coverage gate" fails if the mismatch is detected — retroactively close boxes with evidence before merge.
- Ralph Review tiers (haiku / sonnet / opus) independently verify MCP-sourced evidence at review time — external defence-in-depth on top of agent self-enforcement.

**Tier-A Automation (post-commit hook + sentinel + GHA processor — #477 Theme 6)**:

The manual `mcp__github-checkbox__update_issue_checkbox` invocation is the canonical floor. On top of that, dotfiles#477 Phase 6 ships an opportunistic automation layer that auto-ticks Tier-A boxes whose AC text references files touched by a Stage 4 commit:

1. **Post-commit hook** (`.pre-commit-config.yaml` registers `sst3-tier-a-auto-tick` at the post-commit stage). Fires after every commit. Runs `scripts/sst3-tier-a-auto-tick.py` which: (a) parses the commit message's `Phase: 4` trailer + `(#N Phase M ...)` subject; (b) queries the parent Issue body via `gh issue view`; (c) extracts Tier-A `[ ]` boxes in phase M; (d) for each box whose AC text references a file touched by the commit, accumulates an entry into `SST3-metrics/.tier-a-auto-tick/<issue#>-<phase>.json`. Graceful degrade: any failure → exit 0 + stderr log (post-commit MUST NOT block the commit chain).
2. **GitHub Actions processor** (`.github/workflows/tier-a-auto-tick.yml`). Fires on push to `solo/issue-*` OR `worktree-solo+issue-*` branches (and on `workflow_dispatch`). The second pattern is the EnterWorktree-renamed canonical form per the dotfiles#488 Fix-A worktree-first isolation model — `EnterWorktree` substitutes `/` → `+` because git refspecs cannot contain `/` in worktree branch names; without this trigger pattern the GHA processor silently no-ops on every Stage-4 commit in the canonical isolation model (dotfiles#495 Stage 5 L1-G — same class of defect Ralph Tier 3 caught for `parse_issue_from_branch`, but at the workflow layer). For each sentinel: GET the Issue body via `gh api`, regex-replace the unchecked box anchored on `**(<ac_id>)**` with `[x]`, append a Proof of Work line `- PoW [<ac_id>]: <evidence> (auto-ticked via tier-a-auto-tick.yml)`, PATCH the Issue body via `gh api`. Then delete processed sentinels and commit cleanup with `[skip ci]` + `Phase: 4` trailer.

**Manual MCP override remains the AP #20 fallback** when the automation is unavailable (network failure, GHA disabled, sentinel write blocked, AC text drift away from box-text matcher). The Verification Loop Layer 3 + Stage 5 checkbox-coverage audit STILL run regardless — they enforce the 100% Tier A coverage invariant whether automation or manual closed the boxes.

**Operational notes**:
- Sentinel JSONs land in the repo (NOT gitignored at the directory level) so the GHA processor can read them on push. The `.gitignore` entry is scoped to `SST3-metrics/.tier-a-auto-tick/.cache/` + `*.tmp` markers only.
- Sentinel filename pattern: `<issue#>-<phase>.json`. Multiple commits in one phase accumulate entries (deduped by `(ac_id, commit_sha)` tuple).
- Box-text matching is anchored on the `**(<ac_id>)**` prefix for resilience against text drift in box body wording. AC text drift requires manual MCP override.
- Automation fires only on Stage 4 (Leader stage) commits (`Phase: 4` trailer). Other stages' commits are no-op.

**Canonical invocation points**: `../dotfiles/.claude/commands/Leader.md` Guardrails block + `../dotfiles/.claude/commands/SST3-solo.md` "Governance Enforcement" section. Rule lives there; this AP documents the failure mode.

**Cadence — two-tier rule (#429 Phase 9 refinement)**:
- **Tier A — Phase-deliverable checkboxes** (concrete file edit / commit / function / section / example named in Acceptance Criteria Phase 1..N): **STRICT interleaving required**. Close each with `update_issue_checkbox` + evidence within the same phase's commit window. Cluster-at-end violates AP #20.
- **Tier B — Cross-cutting meta-checkboxes** (Triple-Check Gate items, Engineering Requirements meta-items, Cleanup Requirements, Verification Loop self-gates, PREREQUISITE CHECKPOINT, Expected Behavior post-conditions): **batched-at-end acceptable**. These describe conditions observable only post-all-phases — closing them mid-phase would be dishonest. Ralph Opus (Tier 3) audits this distinction via `../ralph/opus-review.md` "Governance Drift Audit" classification heuristic.

**See also**: STANDARDS.md "MCP Tool Schema Loading" (canonical ToolSearch rule), STANDARDS.md "Governance Evidence Signal (Canonical)" (canonical audit signal — Proof of Work body section, added #431 Phase 1), `../reference/tool-selection-guide.md` Example 2 (canonical evidence-requirements table), AP #17 (Keep Going Until Done — complementary discipline), `../ralph/opus-review.md` Governance Drift Audit (codependent — do not edit in isolation, see #429 Phase 9 + #431 Phase 2a).

---

<!-- stages: 2 -->
## Anti-Pattern #21: Autonomous Follow-up Issue Creation

**Pattern**: during Stage 5 adversarial audit (or any Layer-2 subagent review), the swarm identifies speculative future-failure-modes and autonomously creates a follow-up GitHub issue bundling them as "medium/low severity follow-ups" without explicit user direction.

**Why it fails**: user authorization is binary (proceed / do not proceed). Bundling speculative findings into a new issue presumes authorization the user never gave, converts research-phase output into contract-phase scope, and forces the user to retroactively accept scope the research did not validate against the operator's binding rules ("no deferrals, no priority levels", "no fabricated numbers").

**Evidence**: dotfiles#430 created 2026-04-21 by Layer-2 subagent during #429 Stage 5; user response: "where did #430 come from?" + required full `/Leader 1→5` cycle retrofit (#431 supersedes #430). The 6 speculative phases in #430 were evaluated by proper Stage 1 research and 4 of 6 were discarded entirely (observability metric, rule versioning, token budget, pre-commit hook); the 2 kept phases (bootstrap-paradox doc, harness smoke test) simplified to 2-line edits + ~12-line block respectively.

**How to apply**: Layer-2 subagents present follow-up findings as a COMMENT on the parent issue's Stage 5 summary, NOT as a new GitHub issue. Creating a new issue requires the main agent to surface the proposed scope to the user in chat and obtain explicit approval BEFORE calling `mcp__github__create_issue`. When in doubt, comment don't create.

**Related**: STANDARDS.md "Subagent Orchestration Discipline" (subagent read-only contract); Leader.md Stage 5 DON'T list (added #431 Phase 2b — "Create new GitHub issues autonomously…"); AP #13 ("Proceed" ≠ "Bypass Process" — user authorisation never bypasses workflow, and the inverse: never presume authorisation for scope not discussed).

---

<!-- stages: 4 -->
## Anti-Pattern #22: Cross-Repo `cd` Operations Leak CWD State

**Pattern**: scripts that operate on multiple repos use bare `cd <other-repo>` to change directory before running git or other commands. The CWD remains in the new repo for any subsequent commands in the same shell, leaking state to whatever runs next (subagent, parent process, parallel hook).

**Why it fails**: bash subshell semantics + caller assumptions diverge silently. When a Stage 4 verification script calls `cd ../SST3-AI-Harness && git status` to inspect a sibling mirror, the unprotected `cd` mutates the calling shell's CWD. Subsequent commands that assumed CWD == dotfiles run against the wrong repo. Worst case: the next `git add` or `git commit` lands on the WRONG repo. Carry-forward from `dotfiles#448` Stage 4 third-bullet improvement (applied here in #460 Phase 9).

**Evidence**: `dotfiles#448` Stage 4 friction note "cd-drift: `cd ../SST3-AI-Harness && git status` consumed the implicit cwd assumption" → bullet captured for AP #16 working notes update in a follow-up Issue → applied here in #460 Phase 9.

**How to apply**: Two exemption-classes both explicitly permitted:
- (a) **pure git subcommands**: use `git -C <path> <subcmd>` (no CWD change at all). MANDATORY for any cross-repo git operation. Examples: `git -C ../SST3-AI-Harness status`, `git -C $HOME/DevProjects/voice-staging log --oneline`.
- (b) **non-git commands** (pre-commit install, bash scripts, custom binaries): use a **subshell-protected** form `(cd <path> && command)` so the CWD change is scoped to the subshell and dies with it. Existing canonical examples explicitly permitted: `../dotfiles/scripts/install.sh:228` `(cd "$repo_dir" && pre-commit install ...)`; `../scripts/sst3-code-at-ref.sh:108`.

Bare `cd <path>` without subshell-protection or trailing `cd -` is **prohibited** in any script that has commands following the cd. A `cd -` pattern is fragile (skipped on early-exit / set -e); prefer subshell.

**Enforcement**: `../scripts/check-ap22-cross-repo-cd.sh` (#460 Phase 9 AC 9.7) — pre-commit hook scans canonical script directories for `cd <path> && git ` patterns NOT wrapped in subshell parens; reports the offending file:line. Wired as a pre-commit hook gated on shell + Python script edits (lightweight).

**Related**: AP #16 (Fire-and-Forget Script Execution — cd-drift surfaces there as a verification gap); STANDARDS.md / CLAUDE.md branch safety — under the worktree-per-agent canonical (dotfiles#488 Fix-A) each Stage-4 agent works in its own isolated worktree (own working dir + HEAD + index), so "NEVER switch branches" is the *in-worktree* invariant (correct inside an isolated worktree). cd-drift is *more* dangerous under this model, not less: a wrong-repo / wrong-worktree CWD lands `git` work in the wrong isolated tree, defeating the very isolation the worktree provides.

---

<!-- stages: 4 -->
## Anti-Pattern #23: Curator-Bounded Audit Recall

**Problem**: Skill-canonical audit subagents given a curated rule list ("verify A, B, C") miss rules outside the curator's enumeration. The audit's recall is bounded by the curator's memory — and the curator IS the Leader agent, which is precisely the entity the audit is delegated AWAY from.

**Evidence**: Issue #4 Phase 6.4 forensic — `consumer-private-A/.claude/skills/ebay-seller-tool/SKILL.md` L651 ("HPE P/N, HPE GPN, HPE spare number") missed at Stage 2 Layer-1 audit because the curated rule list did not include item-specifics field guidance. Caught only at Stage 2 Layer-2 by a different angle. See `dotfiles/SST3-metrics/leader-feedback/feedback-consumer-private-A-4.md` L35-37 for the authoritative trail. Filed as dotfiles#458; resolved by this Issue.

**Root Cause**: Subagent prompt phrasing of the form "verify A, B, C; Examples: X, Y, Z" anchors the subagent's audit scope to the enumerated examples. Rules in the canonical that aren't in the example list are silently skipped because the subagent treats the examples as the scope, not as illustrations.

**Detection Patterns** (must match all to avoid false positives on innocent "Examples:" prose):
- Subagent prompt is for a SKILL-CANONICAL COMPLIANCE angle (not a gate, not a generic example list)
- Prompt contains an "Examples:" block enumerating 2+ specific named rules (banned-words, Seagate HARD CONTRACT, prompt-caching, etc.)
- Prompt does NOT instruct the subagent to walk every section of the canonical OR cite the comprehensive-walk template per STANDARDS.md
- RESULT block lacks `canonicals_walked` or per-source `section_failures` attribution

**Prevention**:
- ✓ DO: Use the comprehensive-walk template per STANDARDS.md "Skill-Canonical Audit Template (Comprehensive Walk)" — subagent walks every `## ` and `### ` heading of the canonical, returns per-section pass/fail.
- ✓ DO: Include coverage data in RESULT block (`canonicals_walked` matches Stage 1 `skill_canonical_files`; per-failure `source_file` tagging) so coverage gaps are visible.
- ✗ DON'T: Use "Examples: A, B, C" as the audit scope — examples become the scope ceiling.
- ✗ DON'T: Trust an audit verdict without checking section coverage — verdict against an undersized scope is a false-pass.

**Delimiter (applies to AUDIT prompts only)**: this rule does NOT apply to invariant gates (Ralph Review checklists, Stage 4 Gate 1 verification gates, AC verification checkboxes, Mirror-lane trigger conditions, file:line / command + exit-code checks). Gates verify named conditions and are correctly curated by design. The comprehensive-walk template is for AUDIT prompts that verify a draft or delivered work against a multi-section canonical body.

**Self-Healing** (trigger mechanism — explicit per AP #21 no-autonomous-issue-creation):
- Stage 5 subagent flags an audit verdict that used a curated-list pattern (detection criteria above) → propose comprehensive-walk re-audit as a comment on the parent Issue (NOT a new Issue per AP #21)
- Operator authorises re-audit OR defers to the next Issue on that skill
- If re-audit surfaces a previously-missed rule: apply fix + cross-reference inline at the canonical site so the same rule isn't dropped again
- Do NOT auto-trigger re-audit; require explicit operator authorisation

**Cross-Reference**: STANDARDS.md "Double-Guardrail Principle" → "Skill-Canonical Audit Template (Comprehensive Walk)" subsection. Companion rule: AP #14 (Multi-Layer Subagent Discipline) — different angles per layer + main-agent verification. AP #23 ensures the audit is comprehensive at the SCOPE level; AP #14 ensures multiple angles cover the same scope.

---

<!-- stages: 4 -->
## Anti-Pattern #24: Marker-Substring Changes Without Full Emit-Site Enumeration

**Problem**: When introducing, modifying, or removing a marker substring (error-message partition string, counter name, diagnostic flag, feature-gate literal, status-enum value, log-line prefix), implementing the change at the obvious emission point WITHOUT enumerating and auditing every other site that emits / reads / references / asserts that substring. The scope-incomplete change lands with one of two failure modes: (a) **orphaned/stale references** in test fixtures, mocks, guard clauses, or downstream aggregation logic that silently skip the new wording; (b) **non-deterministic split** where some emission paths use the new substring and others retain the old one, creating downstream inconsistency that surfaces only under certain load patterns.

**doc-emit-site extension (#498 F-17 — dotfiles#468 evidence)**: marker substring changes apply to BOTH code emit sites AND documentation emit sites. dotfiles#468 evidence: a `13/13` invariant count appeared in 5 different documentation locations (CLAUDE.md homelab section, phase5-gate.ps1 banner, two runbook references, and one Issue-body example block); a phase-count update changed the *.ps1 emitter but missed the 5 doc references, leaving stale `13/13` quotes scattered across the canon. Stage 1 enumeration MUST grep `--include='*.md'` `--include='*.txt'` alongside the code globs (the doc-emit class is in scope, not an afterthought); Stage 4 Gate 1 count-drift check MUST cover doc references too. doc-emit-sites fail the same way code-emit-sites fail: silent inconsistency, surfaced only at the next audit.

**Evidence**: project-a#1450 + #1451 — error-marker partition introduction. Implementer changed the emission site without running `grep -rn -F` over the codebase, missing 2-3 downstream references per feature. Stage 4 sample passed locally because the sample exercised the changed emission path; downstream aggregation logic that referenced the OLD marker silently dropped the new emissions. Surfaced only at production observation. Issue #1448 follow-up: same class of bug, different feature (status enum partition). See `dotfiles/SST3-metrics/leader-feedback/feedback-project-a-1450.md` + `feedback-project-a-1451.md` for the authoritative trail. Filed as #477 Theme 2 (this Issue, Phase 4).

**Root Cause**: Marker substrings are conceptually atomic but mechanically scattered across emission sites, test fixtures, mocks, downstream consumers, and assertion clauses. The implementer's mental model treats the marker as "one thing to change" because its semantic role IS one thing — but the codebase reality is N places that all need to move together. Without an enumeration pass at Stage 1, the scope is implicitly bounded by the implementer's recall of where the marker lives.

**Relationship to AP #10 (Search Before Adding)**: AP #10 prevents creating a duplicate of something that already exists. AP #24 prevents incomplete change of something that already exists. Different scope: AP #10 = "does this marker already exist anywhere?"; AP #24 = "have I found EVERY reference to this specific marker substring?".

**Relationship to AP #18 (Sample Invocation)**: Complementary, both fire when the marker change affects pipeline / CLI args / cross-module propagation. AP #18 validates the end-to-end sample lands rows; AP #24 validates the scope of marker references is enumerated and updated. AP #18's sample run can pass even when AP #24 is violated (the sample exercises the changed path; the orphaned references are silently inactive). Both gates required.

**Detection Patterns** (must match all to avoid false positives on non-marker substring changes):
- Change introduces, modifies, or removes a string literal that gates downstream behaviour (error-message text checked by aggregator, status enum compared with `==`, feature-gate literal in `if config["mode"] == "X"`, log-line prefix consumed by parser, partition key in dict / DB column / queue topic)
- The literal is referenced from MORE than one source location (emitter + at least one consumer / asserter / mock / fixture)
- The change is applied at the emitter without prior enumeration (no Stage 1 `grep -rn -F '<exact_literal>'` evidence in research file)

**Prevention**:
- ✓ DO: Run `grep -rn -F '<exact_literal>' src/ tests/ scripts/ --include='*.py'` (or per-language equivalent) at Stage 1 BEFORE any implementation. Record count + per-site triage (emission / fixture / mock / stale) in research file as "Known Emit Sites: (N)".
- ✓ DO: At Stage 4 Gate 1, re-run the same grep AND confirm count matches Stage 1 baseline. Mismatch (new sites added without scope expansion) = FAIL.
- ✓ DO: Use `-F` (fixed-string) flag — marker literals often contain regex metacharacters that get mis-interpreted under default `-E`.
- ✗ DON'T: Trust the change is scope-complete because the obvious emitter was updated. Marker scope is mechanical, not semantic.
- ✗ DON'T: Skip the Stage 4 count-drift check because Stage 1 was thorough — the diff itself can introduce new references that need to land in the count baseline.
- ✗ DON'T: Substring-grep without `-F` on markers containing `(`, `)`, `.`, `*`, `?`, `[`, `]`, `|`, `+`, `^`, `$`, `\` — silent regex failure is the worst failure mode.

**How to apply** (procedural):
- **Stage 1 enumeration angle**: dispatch a dedicated subagent with the prompt "Find every site in the codebase where this exact substring `<literal>` is emitted, referenced, or checked. Use `grep -rn -F '<literal>' src/ tests/ scripts/ --include='*.py'` BEFORE any implementation. List every match with file:line + triage (emission / fixture / mock / stale)." Record count + triage in Issue body as "Known Emit Sites: (N)".
- **Stage 4 count-drift verification gate**: at Verification Loop, re-run the same grep. Compare count to Stage 1 baseline. Mismatch = either (a) implementation added new emission sites that should have been in scope (fix: expand scope to include them) OR (b) implementation removed sites that shouldn't have changed (fix: revert removal). Either way, FAIL the gate until reconciled.

**Self-Healing** (trigger mechanism — explicit per AP #21 no-autonomous-issue-creation):
- Stage 5 subagent flags an Issue that introduced/modified/removed a marker substring without a Stage 1 enumeration step → propose retroactive count-baseline + drift-check as a Stage 5 fix (NOT a new Issue per AP #21)
- Operator authorises retroactive enumeration OR defers to a follow-up Issue
- If retroactive enumeration surfaces a missed site: apply fix + cross-reference inline at the marker definition site so the same marker isn't fragmented again

**Enforcement**:
- `STANDARDS.md` "Marker-Substring Discipline" subsection (cross-reference paragraph).
- `.claude/commands/Leader.md` Stage 1 step 2.1 (Marker-enumeration angle subagent dispatch).
- `WORKFLOW.md` Verification Loop "Marker-substring enumeration (AP #24)" checkbox (Stage 4 Gate 1).

**Codependencies**: AP #18 (Sample Invocation) — both fire when marker change affects pipeline; AP #10 (Search Before Adding) — adjacent failure mode (duplicate vs incomplete change); AP #14 (Multi-Layer Subagent Discipline) — Layer-2 adversarial gap-finder catches missed marker sites that Layer-1 generic-angle coverage misses.

**See also**: STANDARDS.md "Marker-Substring Discipline".

---

<!-- stages: 4 -->
## Anti-Pattern #25: Twisting operator-supplied Content

**The pattern**: Integrating operator-supplied content (a rough paragraph, sentence, point he wrote) into a draft — blog, LinkedIn, CV, cover letter — and silently reshaping its interpretive frame while "polishing": adding qualifiers ("at that size", "by comparison", "fundamentally"), dropping his hedges ("probably", "just"), or reframing a comparison as a verdict (`costs vs value` → `costs outweigh value`). The surface words can be near-identical; the reader's interpretation is not. The marker-driven voice guard (AP #15) catches banned WORDS — it is structurally blind to semantic FRAME drift.

**Why it happens**: The instinct to "improve / sharpen / tighten" prose comes from training on generic blog-writing. the operator writes rough thoughts to AI specifically to have them turned into publishable prose, so SOME editing is mandatory — which makes the boundary (clean up = allowed, twist = forbidden) easy to overshoot. Over-correcting the other way (verbatim copy-paste of his rough phrasing) is the symmetric failure and equally wrong — it defeats the point of having an editor.

**Evidence**: 2026-05-12 meeting-notes blog publish session — three same-session catches: (1) fabricated "I forget stuff" workflow the operator never had (sibling memory `internal-handwriting-memory`); (2) "old laptop in lab cupboard" mis-framing in 4 places — NAD9 is the main production machine (`internal-production-memory`); (3) `costs vs value` twisted to `outweigh the value at that size, by comparison` — 3 qualifiers added, comparison-frame → verdict-frame. Operator double-correction, verbatim: *"can you please read my wordss careful and not make assumptions or twist it?"* and *"I didn't say you have to literal phrase what I wrote, I write in rough to you, so just copying and pasting what I write to you, what's the point? I may as well do it myself? I said dont twist my words or do weird shit to it!"*

**Prevention**:
- ✓ DO: Follow the STANDARDS.md "Polish vs Twist (Semantic Frame Preservation)" 5-step mechanical procedure — quote literal → identify interpretive load → polish grammar/flow → test against the twist checklist → show before final push. Clean up grammar / boundaries / connectors freely; preserve every claim / hedge / comparison exactly as the operator framed it.
- ✗ DON'T: Add interpretation-shifting qualifiers, reframe comparisons as verdicts, drop or add hedges, or impose analytical lenses the operator did not apply. Equally: do NOT over-correct to verbatim copy-paste — polish is mandatory, twist is forbidden, the two are not opposites.

**Self-Healing**: Caught twisting (self-caught or at user review) → restore the operator's interpretive frame, re-apply ONLY grammar/flow polish, show the diff against his literal phrasing. If a draft already shipped with a twist, treat it as a voice regression: revert the frame, keep the clean-up, document which qualifier / hedge / reframe was the twist so the same one is not re-introduced.

**Enforcement**: STANDARDS.md "Polish vs Twist (Semantic Frame Preservation)" (canonical rule). Ralph `sonnet-review.md` "Voice-Frame Preservation (semantic)" angle — subagent-only; no programmatic detector is architecturally possible (`voice_rules.py` has no source-vs-draft input channel; the canonical example has 0% lexical separability). Leader.md Stage 3 + Stage 5 skill-canonical twist sub-prompt when `invoked_skill ∈ {blog, voice-doc-repo}` and prose is in-diff. Memory `feedback_use_hoi_literal_phrasing_no_twist.md` is the ≤30-line pointer. Companion: AP #15 (Voice Prose Without iamhoi Markers — lexical guard; AP #25 is its semantic-frame sibling).

---

<!-- stages: 4 -->
## Anti-Pattern #26: E2E System Verification

**The pattern**: Closing a change with whole-system blast radius (cross-component, schema, contract, or environment change) on the strength of Unit-Tier + Workflow-Tier tests alone — without exercising the WHOLE system end to end against the real environment. The Workflow Tier (AP #18) proves a component's internal wiring; it does NOT prove all components together survive the real DB, the real downstream consumers, and the real environment. This is the **E2E / System Tier** — the operator's "driving test": the engine bench-testing fine (Workflow) does not mean the car passes a driving test (E2E).

**Why it happens**: E2E tests are the slowest and most environment-coupled, so they are first skipped under time pressure. A component sample (AP #18) feels like "end to end" but exercises only one component's path; the gap is the seams BETWEEN components and the assumptions only the live system encodes (the DB schema actually deployed, the downstream consumer's actual contract, the environment config). Building parallel test logic instead of reusing production code paths hides the real integration entirely.

**Evidence**: same class as AP #18's #1424 — a window-aware downstream rejected rows that a window-agnostic pre-flight reported as covered; the COMPONENT tests passed, only the full system (real DB + real downstream consumer) revealed the schema/contract drift, caught operationally not by the suite. The general lesson the operator stated (verbatim Source block, originating Issue): the system test is "taking the car for a driving test ... everything is working together no breakage and the results are expected as intended" — distinct from the engine (component) running.

**Prevention**:
- ✓ DO: For whole-system-blast-radius changes, run the E2E Tier against the real environment (real DB, real downstream consumers, real interfaces) before close. **E2E tests MUST reuse production code paths** (calculators, order gateways, price validation, the real CLI) — never build parallel test logic; search production code before writing any helper. Verify downstream consumers actually succeeded, not just exit code 0.
- ✗ DON'T: Treat a single-component sample (AP #18 Workflow Tier) as system proof. Build a parallel mock pipeline that never touches the real schema/contract. Skip E2E because "Workflow passed".

**Self-Healing**: Caught about to close a whole-system change with no E2E run → run it first against the real environment. Already closed → reopen, run the E2E Tier, add the missing system test reusing production paths.

**Enforcement**: STANDARDS.md "Three-Tier Testing Framework" → E2E Tier (canonical tier definition; absorbs the former STANDARDS heading "E2E Tests Must Reuse Production Code", now a pointer here). WORKFLOW.md Verification Loop E2E-Tier checkbox; Ralph `sonnet-review.md` E2E-Tier system gate; issue-template.md PREREQUISITE E2E-Tier bullet. Companion: AP #18 (Workflow Tier — the component gate; AP #26 is the system gate above it). The BUILD-vs-USE rule (STANDARDS.md "Three-Tier Testing Framework") governs WHEN the E2E Tier must fire vs merely exist.

---

<!-- stages: 4 -->
## Pattern Detection

Monitor for these anti-patterns:
1. **Propagation**: Diff between dotfiles and repos > 0
2. **Templates**: File count in */templates/* > 1
3. **Verification**: Commits without Stage 5 logs
4. **Documentation**: Checksum mismatch between docs
5. **Shortcuts**: Direct commits bypassing Solo workflow
6. **Pre-Commit Validation**: Commits without Verification Loop completion

<!-- stages: always -->
## Escalation Protocol

When anti-pattern detected:
1. First occurrence: Log warning
2. Second occurrence: Alert main agent
3. Third occurrence: Block operations, require manual review
4. Pattern persists: Trigger full system audit (Issue #79 process)

---
