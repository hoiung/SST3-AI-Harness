# SST3 Anti-Patterns

> 19 documented failure modes. Origin: Issue #79.

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

## Anti-Pattern #8: Unverifiable Claims & Assumed Facts

**Problem**: Numbers in documentation/issues/CV without a verifiable source — estimates as facts, numbers copied without re-verification, "sounds right" as evidence.
**Evidence**: Unverified agent count propagated across docs as rhetorical framing. Financial figure misquoted as "average" when source said "up to". Both passed review.
**Root Cause**: "Never Assume — Always Check" enforced for code but not documentation metrics.

**Prevention**: Back every number with a reproducible source (command, query, line ref). Label estimates. Re-verify copied numbers. Maintain provenance (`~/DevProjects/job-hunter/cv-linkedin/METRIC_PROVENANCE.md`).

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

**Documented Exception**: The `../dotfiles/SST3/` → `SST3-AI-Harness/` parallel mirror is INTENTIONAL architectural design (scrubbed public mirror, see `memory/project_sst3_dotfiles_vs_harness.md`). Edit BOTH on every SST3 file change. Drift between them is sanitisation, not duplication. Do NOT flag this pair as an AP #10 violation.

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
- ✓ DO: Wrap prose in `<!-- iamhoi --> ... <!-- iamhoiend -->`. Use `<!-- iamhoi-skip --> ... <!-- iamhoi-skipend -->` for quoted JD content / proper-noun usage. Edit `voice_rules.py` AND `~/DevProjects/job-hunter/cv-linkedin/VOICE_PROFILE.md` Section 8 in the SAME pass when adding a banned word. Re-vendor + drift-cmp when changing canonical.
- ✗ DON'T: Write voice prose untagged. Duplicate banned-word lists. Add KEEP_LIST words to BANNED_WORDS. Bypass the hook with `--no-verify`. Apply voice fixes in isolation from hirer/fact lenses (AP #9 sequential lens failure).

**Self-Healing**: Pre-commit + CI catch unprotected violations only inside marker regions. Untagged regressions surface at user review. When that happens: wrap the offending paragraph in markers, fix the violation inside, re-run hook, document why the section was previously untagged.

**Enforcement**: `scripts/check-ai-writing-tells.py` (canonical, unified `--mode {cv,blog}` post-#460; byte-identical mirror across hoiboy-uk, job-hunter, blog-priv, SST3-AI-Harness), `validate.yml` voice-tells job (dotfiles, `--mode cv`), `ci.yml` voice-tells step (hoiboy-uk, `--mode blog --check-only-new`), `voice-rules-drift` cmp hook (hoiboy-uk pre-commit). STANDARDS.md "Voice Content Protection (Marker-Driven)" section.

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

## Anti-Pattern #18: Smoke-Tested Pipeline Shipped Without End-to-End Sample Run

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

**Per-shape recipe table** (#447 Phase 7 — codifies what already works across the 6 repo shapes; auto_pb is shape "Service" canonical above):

| Shape | Sample artefact | Real-downstream | "8-ticker basket" analogue | Scope triggers | Safety constraints |
|---|---|---|---|---|---|
| **Service** (auto_pb-shape: backend pipeline + DB + queue) | `auto_pb_swing_trader/scripts/sample_invocation_issue<N>.py` (real CLI, real DB, real queue) | Postgres rows present, contamination audit passes, downstream consumer (SL1 fetch / queue tail) succeeds | 8-ticker liquid basket | CLI flag / SL1 / SL2 / queue-orchestrator / pipeline-tracker / cross-module arg propagation | Never touch production positions from E2E tests; RTH-only for IBKR-mediated tests; chunked not monolithic backtests |
| **Docs-only** (research notes / runbooks / handover memory) | `/tmp/sample_<topic>_<date>.md` showing 1 representative path traversed end-to-end (frontmatter validated, related_code paths resolve, every claim has a file:line provenance) | `bash dotfiles/scripts/sst3-doc-frontmatter.sh --strict` exits 0 + `sst3-doc-links.sh` exits 0 + `sst3-sync-related-code.sh` exits 0 on every changed `.md` | n/a — read every file the change touches end-to-end, not a sample basket | Frontmatter add/change, related_code link change, runbook step add/change | No fabricated numbers/dates; every claim backed by file:line / commit / URL |
| **Static-blog** (hoiboy-uk Hugo content) | `hoiboy-uk/scripts/pre-publish.sh` output (Hugo build + lychee on rendered HTML — NOT raw markdown) | `public/posts/<slug>/index.html` renders with no broken links, voice-guard passes (`check-ai-writing-tells.py --mode blog --check-only-new` exit 0), banned-words clean (`voice_rules.py` exit 0) | Build ALL drafts (`hugo --buildDrafts`) before publish so cross-links resolve | New post, voice-affecting edit, image-asset add (Drive subfolder hero), cross-link to other post | Publish requires EXPLICIT user approval ("publish it" / "let's go live"); never auto-push to main of hoiboy-uk; Drive case-insensitive collision check (NTFS via WSL); no em dashes |
| **Config-heavy** (dotfiles, package.json + .github/scripts setups) | Pre-commit dry-run `/tmp/precommit_sample_<date>.txt` showing every modified hook fires + statusline syntax-check + propagate-template.py runs clean across all consumer repos | All consumer repos pass `check-claude-template-propagation`; `propagate-template.py` exits 0 with `5/7 repositories updated successfully`; statusline `node -c` clean | Run pre-commit against the changed file glob + 1 file from each consumer repo | New pre-commit hook, statusline edit, settings.json change, propagate-template / propagate-mirrors edit | Never commit secrets to public repo; secret-scan before issue body posts; mirror-drift hazard documented when canonical changes |
| **Infra-as-code** (.github/workflows, install.ps1, runbooks) | One workflow run on a non-default branch with `act` (local) OR PR-trigger run captured to `/tmp/ci_run_<workflow>_<date>.log` showing every step exits 0 | CI badge green on solo branch; `act -l` lists the new workflow; install.ps1 dry-run on a clean Windows VM (or PowerShell `-WhatIf`) | n/a — exercise every code path the workflow added (matrix, conditional, secret-using job) | New workflow, new install step, new conditional gate, new secret consumer | Never modify CI/CD pipelines without dry-run; treat workflow YAML as production code |
| **GAS** (Google Apps Script — tradebook_GAS, future projects) | `tradebook_GAS/scripts/sample_test.gs` runs against the test project URL; outputs identical to live project URL when the same input is fed | Test project sheet shows expected rows; live project URL invocation against a sandbox sheet matches | n/a — exercise the test/live project pair with one real input row before merging | Trigger change, sheet schema change, deployed-as-add-on edit | Test project for rehearsal, live project for production; never edit live project directly; GAS deploys are atomic + irreversible |
| **Homelab-bootstrap** (single-node NUC provisioning, operator-initiated from master) | TBD pending Phase 9 verification — see [dotfiles#455](Issue #455) | TBD | TBD | `bootstrap-nuc.ps1` / `provision.sh` / `secrets-pull.sh` / `verify-node.sh` / `setup-wsl-service.ps1` / `setup-portproxy.ps1` / wsl/packages.txt / homelab runbooks | TBD |
| **Pre-publication blog research** (blog-priv — voice-guarded private staging for hoiboy-uk) | `blog-priv/scripts/sample_invocation_issue<N>.py` (real CLI: voice-guard + iamhoi balance + secret-scan + commit-msg scan + marker-balance grep + frontmatter validator — 6 distinct steps) | `check-ai-writing-tells.py --mode blog --no-check-only-new` exit 0 (#460 Phase 1: research files commonly pre-date HOIBOY_CUTOFF_DATE; cutoff filter must be off so they are actually scanned) + `check-iamhoi-wrapping.py` exit 0 + `check-public-repo-secrets.py --enforce-on-private` exit 0 + commit-message scan exit 0 + marker-balance check (open `<!-- iamhoi -->` count == close `<!-- iamhoiend -->` count) + frontmatter validator (status ∈ {research, drafting, archived, published}; published_to set iff status=published; wordcount ≤3000) | n/a — run the 6-step gate against ONE representative prep file (clean research preferred, e.g. BOOKS_READING_LIST_RESEARCH.md) | New research file, draft-state transition, hoiboy-uk publish candidate | Drafts stay private until ALL 6 gates pass; published_to SHA captured AFTER hoiboy-uk commit lands; never auto-promote published-archived → drafting without explicit user authorisation |

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

**Self-Healing**: If you catch yourself about to close a pipeline/wiring issue without running a real sample → run the sample first. If you already closed one → reopen, run the sample, and add the missing regression test in the same fix.

**Enforcement**: STANDARDS.md "Testing Priority — Workflow Validation Gate"; `WORKFLOW.md` Verification Loop (canonical gate); `CLAUDE_TEMPLATE.md` behavioural rule bullet; `issue-template.md` PREREQUISITE CHECKPOINT includes sample-run confirmation; Ralph `sonnet-review.md` AP #18 checklist (three sub-checks covering scope, evidence, and mock-assertion discipline). Note: all five enforcement points are documentation-level + honour-system checklists — there is currently no CI job that blocks a merge when a pipeline-touching diff lacks a sample log. Adding such a CI gate is tracked as a future hardening task.

---

## Anti-Pattern #19: Structural Question Answered By Grep Alone, Or Wrapper-Lane Result Trusted Without Source Check

**Wrapper-lane epoch preamble (Issue #445 Stage 5 — naming-honesty audit)**: this AP was written for the daemon-MCP epoch. Under the wrapper-lane, several semantics shift but the disciplines stay the same: (1) there is no graph database, no SQLite, no embeddings — every `search` is keyword-only by design (treat `embeddings_count=0` references throughout this AP as "always-true under wrapper-lane"); (2) there is no staleness — every wrapper call re-parses on disk (treat "fresh / stale" references as "the wrapper-lane returns repo-HEAD-time results per call, no cache invalidation needed"); (3) wrapper output uses `file_count`, not `total_nodes` — the field-rename happened in Issue #445 Stage 5. Disciplines that REMAIN mandatory: synonym sweep before any "no match" conclusion, mechanical per-query spot-check by reading source, subagent fallback for unsupported-language regions (Markdown, YAML, JSON, SQL, TOML, shell, HTML, Jinja, Dockerfile, Go, Java, etc.), and the 12 subagent-only moments listed in STANDARDS.md "Structural Code Queries". Where the prose below references "graph" / "freshness" / "embeddings", read it as wrapper-lane / per-call repo-state / "always keyword".

**Pattern (two sides of one coin)**:
- (a) **Under-use**: dispatching an Explore subagent or running a multi-pass grep to answer a purely structural question (who calls X? callers/callees? blast radius of editing Y? dead functions? tests for Z?) in a language the graph supports, when a single `query` call would answer it authoritatively in sub-second time. This is the graph-specific instance of AP #10 ("Failure to Search Before Adding" / grep-before-writing) — AP #10 covers grep for existing files/rules, AP #19 extends the same discipline to graph queries.
- (b) **Over-trust**: taking a graph result at face value — especially a "no results" response — without a source spot-check. Silent failure modes include: stale graph (code changed since last build), unsupported-language drop (YAML/SQL/shell edits are invisible to the graph), cross-language boundary (Py→HTTP→Rust contract), and keyword-fallback masquerading as semantic search when `embeddings_count=0`. This is the graph-specific instance of AP #11b ("Applying without false-positive check") + AP #14c ("Main agent verifies swarm output against source") — those APs cover audit findings and subagent output respectively; AP #19 extends the same verification discipline to graph tool output.

**Why it happens**:
- Under-use: agents default to the subagent pattern from muscle memory; the graph isn't mentioned in WORKFLOW/Leader/SST3-solo decision points.
- Over-trust: structured JSON with `status: ok` reads as authoritative; the 5 tools' help text doesn't call out freshness or language-coverage gaps per call.

**Evidence (file:line citations — 12 subagent-only moments that must NOT be demoted by a "graph-first" rule)**:
1. Voice Content Protection + AI-tells — `STANDARDS.md:357-377` + `../scripts/voice_rules.py`
2. Intentional-vs-accidental architecture — `STANDARDS.md:183` + `ANTI-PATTERNS.md:198-206` (AP #11b)
3. Research Applied Collectively (cross-lens) — `STANDARDS.md:158-171` (Rule #9)
4. Chat-history scope-drift / opposite-scoping — `WORKFLOW.md:41-42` (Stage 3)
5. False-positive sweep for confirmed violations — `ANTI-PATTERNS.md:203`, `user-review-checklist.md:71-77`
6. Scope vs audit 100% alignment — `WORKFLOW.md:39`, `issue-template.md:121-126`
7. Overengineering / out-of-scope detection — `WORKFLOW.md:40`, `issue-template.md:223`
8. Design rationale explanation — `STANDARDS.md:87`, `user-review-checklist.md:106-107`
9. Factual claims provenance validation — `STANDARDS.md:111-157` (user-assertion rule)
10. YAML/JSON/SQL/shell/TOML/Dockerfile/Jinja/HTML/CSS semantic content audits — `STANDARDS.md:239` (unsupported-languages list in "Structural Code Queries")
11. Markdown voice-prose AI-tells — `STANDARDS.md:357` (Voice Content Protection), `ANTI-PATTERNS.md:270-285` (AP #15)
12. Acceptance-criteria prose → code file:line evidence mapping — `WORKFLOW.md:82`, `user-review-checklist.md:9-15`

**How to apply**:
- Before answering a structural question: run the STANDARDS.md "Structural Code Queries" pre-query safety gate. If it passes, use the graph. If it fails on freshness, `graph update`. If it fails on language, use subagents.
- **Mechanical per-query spot-check (not judgment)**: after EVERY `callers_of` / `callees_of` / `impact` / `inheritors_of` call, Read one result's source line and record `spot-check: <file:line>` in the RESULT block. After every `search` call with `embeddings_count=0`, Read TWO results (keyword-fallback false-positive risk is higher). "I'll spot-check the important ones" is not compliance — every query gets a check.
- **At parallel-subagent scale (≥5 concurrent subagents — round-5 TB-8 N48)**: subagents STILL embed per-query spot-checks in their RESULT blocks (Rule unchanged). But the main agent verifies ONE spot-check per SUBAGENT on receipt (not one per query). Only findings that DRIVE A SCOPE CHANGE require main-agent per-query verification before acting. This reduces main-agent verification load from O(N_subagents × N_queries) to O(N_subagents) + O(scope-changing-findings). Preserves rigour where it matters; removes ritual where it does not. Field evidence: agent5 found per-query main-agent verification breaks at 9 concurrent subagents (2026-04-20).
- "No matches" in an area that includes unsupported-language files (YAML/SQL/shell/TOML/Dockerfile/Jinja/HTML/CSS) → explicitly broaden to subagent exploration before drawing a negative conclusion. Graph is blind to non-code.
- RESULT block discipline (per STANDARDS.md Subagent Orchestration): when a graph query was used, the RESULT block **MUST** record the query type + target, `last_updated`, `embeddings_count`, spot-check source file:line, and result count. When graph was unavailable or unsupported, the RESULT block MUST record WHY it was skipped. If `embeddings_count=0` AND the query was `search`, the RESULT block MUST ALSO include `keyword_fallback: true` so reviewers don't misread keyword matches as semantic similarity.

**Do / Don't**:
- ✓ DO: run graph `query callers_of` / `query impact` for structural questions in supported languages **FIRST** when the pre-gate passes, grep only as fallback when graph returns insufficient detail — not the reverse. Grep-first-then-graph-confirm wastes 2 grep passes and returns less precise evidence (string match vs AST CALLS edge).
- ✓ DO: always use fully-qualified `file.py::symbol` targets for `callers_of` / `callees_of` / `impact` / `inheritors_of` — ambiguous-name failures (File+Function collision) are easy to forget under time pressure. Upstream fix tracked at `n24q02m/better-code-review-graph#316`.
- ✓ DO: spot-check EVERY graph result by reading source — mechanical, not judgment call (per-query, not per-batch)
- ✓ DO: document graph-call output (query, target, `last_updated`, `embeddings_count`, result count, spot-check file:line) in the RESULT block
- ✓ DO: explicitly broaden to subagent when "no results" lands in an area with unsupported-language files
- ✓ DO: cap `impact max_depth=1` by default (depth-2 fans out to 1000+ nodes on shared hooks/utils; wrap in subagent with summarisation)
- ✓ DO: check `embeddings_count` BEFORE using `search` on non-literal-identifier queries — keyword-fallback is silent
- ✓ DO: after `callers_of` / `callees_of` returns `not_found`, run `search <symbol>` FIRST to check whether the symbol exists as any node type. If `search` returns 0 too → grep. NEVER treat `not_found` as authoritative "no callers" — it conflates "symbol not indexed" with "zero callers". Specific non-indexed classes observed in round-5: instance methods (use fully-qualified `file.py::Class.method` form, not `file.py::method`), Pydantic validators, framework-decorator-registered routes (`@router.get/post`, `@app.get`, `@celery.task`). Upstream disambiguation tracked at the `not_found` response-shape issue filed by #427 Phase 2.
- ✗ DON'T: dispatch Explore subagents for who-calls / blast-radius questions in supported languages when the graph is fresh
- ✗ DON'T: trust `status: ok` JSON as authoritative without a source spot-check
- ✗ DON'T: silently skip graph checks when available — document the skip reason
- ✗ DON'T: apply a "graph-first" rule to any of the 12 subagent-only moments above
- ✗ DON'T: invoke `large_functions` during Sanity Check on unchanged-function-size diffs (lint noise)
- ✗ DON'T: trust `callers_of` / `callees_of` result when the target file contains dynamic dispatch. Five known subtypes (round-5 5× corroboration: N2+N16 to_thread / N24 f-string / N41 framework decorators):
  1. **async indirection**: `asyncio.to_thread(func, ...)`, `asyncio.ensure_future(func, ...)`, `map(func, ...)`, `functools.partial(func, ...)`
  2. **dict-of-Callable registries** and `getattr(obj, name)()` lookups
  3. **f-string-constructed identifiers** + `getattr`: e.g. `handler = getattr(self, f"handle_{event_type}")` — grep the prefix (`handle_`) not the full name
  4. **decorator-based routing**: FastAPI `@router.get/post/put/delete/patch`, Flask `@app.get/post/route`, Celery `@celery.task` / `@task`, Django `@path` registrations, pytest `@pytest.fixture`/`@pytest.mark.parametrize`
  5. **class-based dispatch**: generic `__call__`, `__getitem__` indirection, metaclass-registered handlers
  Grep the target file for these patterns as a belt-and-braces (Python, e.g. `grep -E "asyncio.to_thread|asyncio.ensure_future|functools.partial|@router|@app\.|@celery|getattr"`). Field-tested: 2 independent round-4 agents hit silent-miss on `to_thread` — graph returned 1 caller, reality was 3. Round-5 adds f-string + FastAPI `@router` as distinct subtypes. Upstream extension tracked at `n24q02m/better-code-review-graph#331`.
- ✗ DON'T: use `search` on verb-phrases / multi-word queries when `embeddings_count=0` (keyword fallback returns garbage)

**Enforcement — split by tier** (Haiku is surface-check speed, Sonnet+Opus do deep reasoning):
- **Ralph Tier 1 (Haiku) — under-use evidence gate**: for any structural question in a supported language with a fresh graph available, the RESULT block MUST show at least ONE graph-query evidence line (target + result count + spot-check file:line) OR a documented skip reason (one of: unsupported language, graph empty, subagent has no MCP access per the MCP-inheritance note below). Attestation alone ("graph was attempted") is INSUFFICIENT — evidence or documented skip required. This elevation catches the muscle-memory default-back-to-grep failure mode observed in round-4.
- **Ralph Tier 2 (Sonnet) — under-use + over-trust logic check**: if graph was used, was at least one result spot-checked by reading source (evidence: file:line in the RESULT block)? If graph was available but not used for a structural question, FAIL.
- **Ralph Tier 3 (Opus) — full AP #19 compliance**: includes Sonnet checks plus: no false-negative from "no results" in areas with unsupported-language files; no false confidence from structured JSON; graph freshness documented.
- Subagent-only moments listed in STANDARDS.md "Structural Code Queries" section are explicitly out of AP #19 scope — they are correctly solved by subagents.
- **"Wrapper-lane available" is defined precisely**: `bash dotfiles/scripts/sst3-code-status.sh` exits 0 and emits valid JSON `{last_updated, file_count, source_languages}`. Wrapper-lane is stateless — every call re-parses on disk; there is no staleness check, no `total_nodes`, no `embeddings_count`. A wrapper that exits non-zero (typically exit 127 = inner engine missing per the documented stderr contract) counts as "unavailable" for Ralph FAIL purposes — document the reason in RESULT and proceed with subagent fallback. **Exit 127 semantics (post Issue #456)**: means the engine is **genuinely missing on disk** (npm/cargo/pipx install never ran). Pre-#456 the same code ALSO fired when the engine was on disk but PATH was not propagated to non-interactive shells; that PATH-propagation gap is now closed by `sst3-bash-utils.sh` self-bootstrap (see STANDARDS.md "Structural Code Queries — Non-interactive shell PATH bootstrap"). If exit 127 fires post-fix, run `scripts/install.sh` — do NOT add custom PATH workarounds.
- **Subagent wrapper-lane access (post Issue #445)**: under the wrapper-lane, graph queries are bash-tool calls (no MCP server). Whether subagents inherit the main agent's bash-tool set is harness-dependent — treat as unknown-per-session until empirically verified per dispatch. **Every subagent RESULT block that discusses graph queries MUST include `mcp_graph_available: yes|no` as the first line** (field name retained for cross-tier compatibility; under wrapper-lane this is effectively `wrapper_invokable: yes|no`). **Wrapper-lane semantics (Issue #445)**: under the wrapper-lane this field is **always `no`** — wrappers are bash-tool calls, not MCP-protocol calls; subagents do not inherit the bash-tool set in the same way. Documented fallback (grep + manual file reads) is the EXPECTED path, not a degradation. The historical-MCP semantics below describe the legacy daemon-MCP behaviour and apply only if MCP transport is ever re-enabled. **Historical MCP-era semantics (G-3 fix, #444; retained for reference)**: in the MCP-native phase the field reflected the LAST graph call's outcome. Verify via no-op `bash dotfiles/scripts/sst3-code-status.sh`; record `yes` if that and every subsequent wrapper call returned exit 0; record `no` if any wrapper exited non-zero (e.g. exit 127 stderr-contract on missing engine). Ralph Tier 1 uses this field to distinguish "no access" (acceptable grep fallback, PASS) from "lazy fallback" (had access but skipped, FAIL).

**Self-Healing**: If you catch yourself reaching for `Agent(Explore)` on a who-calls question in a supported language with a fresh graph → stop, run the graph query first, narrow the subagent prompt with the graph result. If you catch yourself trusting a "no results" without spot-checking → read one matching file from the area and confirm, then proceed.

**Cross-reference**: AP #10 (grep-before-writing), AP #11b (false-positive sweep), AP #14c (main agent verifies swarm output against source). AP #19 extends those disciplines to graph tool output.

**See also**: `STANDARDS.md` "Structural Code Queries" (canonical rule + 5-item pre-query gate), `../reference/tool-selection-guide.md` "Decision Tree: Code-Understanding Queries" (4-quadrant matrix + edge cases + invocation reference), `../dotfiles/docs/guides/code-query-playbook.md` (operational recipe: freshness, fallback, embeddings, cadence).

---

## Anti-Pattern #20: Comment-Only Progress Tracking Without Checkbox+Evidence

**Pattern**: Reporting Acceptance Criteria completion via narrative comment ("Phase 2 done, all tests pass") instead of invoking `mcp__github-checkbox__update_issue_checkbox(issue_number, checkbox_text, evidence)` per checkbox. The Issue body — the permanent scope contract — remains a sea of `[ ]` while completion lives only in comment history, which is easy to re-read out of order, hard to audit, and impossible to reconcile against original scope without manual cross-referencing.

**Why it happens**:
- The MCP tool schema is **deferred** by the Claude Code harness and the agent sees only the tool name — calling it directly errors out with `InputValidationError`, so the agent falls back to comments without ever loading the schema via `ToolSearch`. (Canonical fix: STANDARDS.md "MCP Tool Schema Loading".)
- Active workflow prompts (Leader.md, SST3-solo.md) historically lacked a strong "MUST invoke" directive; strong wording lived only in `../archive/ORCHESTRATOR.md:738-763` (archived historical source; canonical post-#429 location is `../reference/tool-selection-guide.md` Example 2).
- Model regressions — commit `b9cf036` (2026-04-08, Opus 4.6) cut the canonical `Example 1` + `Example 2` blocks from `../reference/tool-selection-guide.md`, removing the copy-paste template agents relied on. Restored in #429.
- 1M-context "Keep Going Until Done" (AP #17) paradigm encouraged batched narrative over per-deliverable governance updates — the failure mode this AP documents explicitly.

**Evidence (measurable governance drift — 2026-04-21 audit)**:
- `hoiung/auto_pb_swing_trader#1346` (closed): 209 checkboxes, 0 checked, no body-PATCH events
- `hoiung/auto_pb_swing_trader#1353` (closed): 100 checkboxes, 0 checked, 6 comment checkpoints only
- `hoiung/auto_pb_swing_trader#1359` (closed): 137 checkboxes, 0 checked
- `hoiung/auto_pb_swing_trader#1364` (closed): 143 checkboxes, 0 checked
- **589 unchecked acceptance criteria across completed work** — no per-checkbox evidence trail.

**Relationship to AP #17 (Keep Going Until Done)**:

AP #17 and AP #20 are **complementary, not contradictory**. AP #17 means: do not stop to ask permission between phases — keep working until done or a real blocker. AP #20 means: as each Acceptance Criterion completes, update the checkbox with evidence via MCP. Combined: **keep going AND update-as-you-go — never batch-report at phase end via narrative comment**. An agent that stops mid-work to batch checkbox updates is violating AP #17; an agent that keeps going but reports only in comments is violating AP #20. Both must hold at once.

**How to apply**:
- At every Acceptance Criteria completion → invoke `mcp__github-checkbox__update_issue_checkbox(issue_number, checkbox_text, evidence)` with evidence matching the canonical patterns in `../reference/tool-selection-guide.md` "Example 2: Stage 4 Checkbox Update".
- If the tool returns `InputValidationError` (deferred schema), load via `ToolSearch(select:mcp__github-checkbox__update_issue_checkbox,...)` per STANDARDS.md "MCP Tool Schema Loading" — never silent-fallback to comments.
- Comment checkpoints SUPPLEMENT checkbox updates (narrative context, blockers, next steps) — they do NOT REPLACE them.
- Stage 4 Verification Loop "Checkbox-MCP coverage gate" fails if the mismatch is detected — retroactively close boxes with evidence before merge.
- Ralph Review tiers (haiku / sonnet / opus) independently verify MCP-sourced evidence at review time — external defence-in-depth on top of agent self-enforcement.

**Canonical invocation points**: `../dotfiles/.claude/commands/Leader.md` Guardrails block + `../dotfiles/.claude/commands/SST3-solo.md` "Governance Enforcement" section. Rule lives there; this AP documents the failure mode.

**Cadence — two-tier rule (#429 Phase 9 refinement)**:
- **Tier A — Phase-deliverable checkboxes** (concrete file edit / commit / function / section / example named in Acceptance Criteria Phase 1..N): **STRICT interleaving required**. Close each with `update_issue_checkbox` + evidence within the same phase's commit window. Cluster-at-end violates AP #20.
- **Tier B — Cross-cutting meta-checkboxes** (Triple-Check Gate items, Engineering Requirements meta-items, Cleanup Requirements, Verification Loop self-gates, PREREQUISITE CHECKPOINT, Expected Behavior post-conditions): **batched-at-end acceptable**. These describe conditions observable only post-all-phases — closing them mid-phase would be dishonest. Ralph Opus (Tier 3) audits this distinction via `../ralph/opus-review.md` "Governance Drift Audit" classification heuristic.

**See also**: STANDARDS.md "MCP Tool Schema Loading" (canonical ToolSearch rule), STANDARDS.md "Governance Evidence Signal (Canonical)" (canonical audit signal — Proof of Work body section, added #431 Phase 1), `../reference/tool-selection-guide.md` Example 2 (canonical evidence-requirements table), AP #17 (Keep Going Until Done — complementary discipline), `../ralph/opus-review.md` Governance Drift Audit (codependent — do not edit in isolation, see #429 Phase 9 + #431 Phase 2a).

---

## Anti-Pattern #21: Autonomous Follow-up Issue Creation

**Pattern**: during Stage 5 adversarial audit (or any Layer-2 subagent review), the swarm identifies speculative future-failure-modes and autonomously creates a follow-up GitHub issue bundling them as "medium/low severity follow-ups" without explicit user direction.

**Why it fails**: user authorization is binary (proceed / do not proceed). Bundling speculative findings into a new issue presumes authorization the user never gave, converts research-phase output into contract-phase scope, and forces the user to retroactively accept scope the research did not validate against Hoi's binding rules ("no deferrals, no priority levels", "no fabricated numbers").

**Evidence**: dotfiles#430 created 2026-04-21 by Layer-2 subagent during #429 Stage 5; user response: "where did #430 come from?" + required full `/Leader 1→5` cycle retrofit (#431 supersedes #430). The 6 speculative phases in #430 were evaluated by proper Stage 1 research and 4 of 6 were discarded entirely (observability metric, rule versioning, token budget, pre-commit hook); the 2 kept phases (bootstrap-paradox doc, harness smoke test) simplified to 2-line edits + ~12-line block respectively.

**How to apply**: Layer-2 subagents present follow-up findings as a COMMENT on the parent issue's Stage 5 summary, NOT as a new GitHub issue. Creating a new issue requires the main agent to surface the proposed scope to the user in chat and obtain explicit approval BEFORE calling `mcp__github__create_issue`. When in doubt, comment don't create.

**Related**: STANDARDS.md "Subagent Orchestration Discipline" (subagent read-only contract); Leader.md Stage 5 DON'T list (added #431 Phase 2b — "Create new GitHub issues autonomously…"); AP #13 ("Proceed" ≠ "Bypass Process" — user authorisation never bypasses workflow, and the inverse: never presume authorisation for scope not discussed).

---

## Anti-Pattern #22: Cross-Repo `cd` Operations Leak CWD State

**Pattern**: scripts that operate on multiple repos use bare `cd <other-repo>` to change directory before running git or other commands. The CWD remains in the new repo for any subsequent commands in the same shell, leaking state to whatever runs next (subagent, parent process, parallel hook).

**Why it fails**: bash subshell semantics + caller assumptions diverge silently. When a Stage 4 verification script calls `cd ../SST3-AI-Harness && git status` to inspect a sibling mirror, the unprotected `cd` mutates the calling shell's CWD. Subsequent commands that assumed CWD == dotfiles run against the wrong repo. Worst case: the next `git add` or `git commit` lands on the WRONG repo. Carry-forward from `dotfiles#448` Stage 4 third-bullet improvement (applied here in #460 Phase 9).

**Evidence**: `dotfiles#448` Stage 4 friction note "cd-drift: `cd ../SST3-AI-Harness && git status` consumed the implicit cwd assumption" → bullet captured for AP #16 working notes update in a follow-up Issue → applied here in #460 Phase 9.

**How to apply**: Two exemption-classes both explicitly permitted:
- (a) **pure git subcommands**: use `git -C <path> <subcmd>` (no CWD change at all). MANDATORY for any cross-repo git operation. Examples: `git -C ../SST3-AI-Harness status`, `git -C ~/DevProjects/blog-priv log --oneline`.
- (b) **non-git commands** (pre-commit install, bash scripts, custom binaries): use a **subshell-protected** form `(cd <path> && command)` so the CWD change is scoped to the subshell and dies with it. Existing canonical examples explicitly permitted: `../dotfiles/scripts/install.sh:228` `(cd "$repo_dir" && pre-commit install ...)`; `../scripts/sst3-code-at-ref.sh:108`.

Bare `cd <path>` without subshell-protection or trailing `cd -` is **prohibited** in any script that has commands following the cd. A `cd -` pattern is fragile (skipped on early-exit / set -e); prefer subshell.

**Enforcement**: `../scripts/check-ap22-cross-repo-cd.sh` (#460 Phase 9 AC 9.7) — pre-commit hook scans canonical script directories for `cd <path> && git ` patterns NOT wrapped in subshell parens; reports the offending file:line. Wired as a pre-commit hook gated on shell + Python script edits (lightweight).

**Related**: AP #16 (Fire-and-Forget Script Execution — cd-drift surfaces there as a verification gap); STANDARDS.md branch safety (NEVER switch branches — cd-drift can land work on wrong branch via wrong-repo CWD).

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
