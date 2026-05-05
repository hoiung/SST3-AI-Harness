# SST3 Solo Workflow

**Subagents**: research, read, audit, plan, verify. NEVER write code, create issues, or implement. **Main agent**: collates findings, writes /tmp, creates issues, implements, commits, merges.

## The 5-Stage Sequential Workflow

**CRITICAL**: ORDER-DEPENDENT. No skipping, no reordering.

### Stage 1 — Research (Subagent Swarm → /tmp)

- [ ] Check `docs/research/` for existing research on this domain first
- [ ] **MANDATORY status CHECK at Stage 1 top**: run `bash dotfiles/scripts/sst3-code-status.sh` unconditionally and record `last_updated` + `file_count` in the research file — audit trail for Stage 5 reviewers, even on 12-moments topics. The wrapper-lane is stateless; there is no staleness or build step. `bash dotfiles/scripts/sst3-code-update.sh` is a no-op contract-preservation shim and may be invoked anywhere docs cite it without effect. For doc + sync auditing, the Layer-2 orchestrator `bash dotfiles/scripts/sst3-check.sh` (Phase D) composes A+B+C — invoke via `/sync-check` skill or directly. See `docs/guides/code-query-playbook.md`.
- [ ] **Pre-swarm graph SEED** (STANDARDS.md "Structural Code Queries"): if the research topic is structural code in a supported language, use graph to DEFINE scope BEFORE dispatching the swarm — not to verify pre-formed scope AFTER. Run `bash dotfiles/scripts/sst3-code-callers.sh <symbol> <lang>` / `bash dotfiles/scripts/sst3-code-search.sh '<pattern>' <lang>` on every symbol the USER MENTIONED in the task description, plus `bash dotfiles/scripts/sst3-code-impact.sh <base-branch>` on user-named files. Feed the resulting evidence into subagent prompts so layer-1 angles are scoped to real call-sites / symbols / blast-radius — not hypothesis. Graph SEEDS the swarm; it does NOT replace its different-angle coverage. Skip-condition: if the topic is semantic / voice / intent / cross-document / non-code (one of the 12 subagent-only moments), skip graph queries; go straight to swarm. (The status freshness CHECK above still runs unconditionally for audit trail.)
- [ ] Launch MANY parallel subagents, each with focused area (5 files max per subagent). Subagents remain required for the 12 subagent-only moments.
- [ ] **Layer-2 adversarial gap-finder MANDATORY** (Theme 8, #477; AP #14 instantiation): after the Layer-1 swarm completes, dispatch a Layer-2 subagent with prompt: "Layer-1 found X, Y, Z. Find 3 things they missed — false-positive claims with modern equivalents OR genuine gaps not yet surfaced." Layer-2 prompt MUST differ from Layer-1 (per AP #14c). For infrastructure / governance / cross-cutting Issues this angle is load-bearing — generic Layer-1 coverage misses scope-adjacent gaps. Canonical rule: STANDARDS.md "Stage 1 Layer-2 Adversarial Gap-Finder Discipline"; cross-reference: ANTI-PATTERNS.md AP #14d. Procedure expanded in Leader.md Stage 1 step 2a.
- [ ] Main context = orchestrator only — NEVER read source files directly in main context
- [ ] Research phase must use <30% of context budget
- [ ] Main agent collates all subagent findings into /tmp file containing: **findings + gaps + plan**. Record any wrapper-lane calls used + `last_updated` + `file_count` + spot-check source file:line. Also record `graph_applicable: true|false (reason: <class>)` — downstream stages MUST read this field and NOT re-derive the classification independently (single-declaration-carries-forward). (`graph_applicable` is the historical field name retained for downstream-stage carry-forward; it gates whether wrapper-lane queries are run.)
- [ ] Output /tmp file for user review before proceeding to Stage 2
- [ ] Per-stage feedback per STANDARDS.md §Per-Stage Feedback Capture — write the Stage 1 block before declaring complete

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
- [ ] Per-stage feedback per STANDARDS.md §Per-Stage Feedback Capture — write the Stage 2 block before declaring complete

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
- [ ] Per-stage feedback per STANDARDS.md §Per-Stage Feedback Capture — write the Stage 3 block before declaring complete

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
- [ ] Per-stage feedback per STANDARDS.md §Per-Stage Feedback Capture — write the Stage 4 block (per-Ralph-tier sub-bullets in `worked` + `ralph_restarts` in `friction`) before declaring complete

### Stage 5 — Post-Implementation Review (Subagent Swarm)

- [ ] Review against issue body scope, goal alignment, and design doc
- [ ] **Audit Research Preservation**: if the issue research phase produced 3+ external sources, verify all have been captured in `docs/research/` per `research-reference-guide.md` schema (YAML frontmatter, canonical filename `YYYY-MM-DD-topic-description-issue-NNN.md`, quality score ≥8/10). Checklist template: `archive/stage-6-retrospective.md` Section 3.1 [SST2 legacy].
- [ ] **Wiring check**: Everything wired up properly — common failure: fix/enhance/refactor but forget to wire up to existing functions
- [ ] **Graph-backed diff audit** (when graph available per STANDARDS.md "Structural Code Queries"): `bash dotfiles/scripts/sst3-code-review.sh <default-branch>` (use `main` or `master` per repo default) generates a diff-scoped context block (changed files + blast radius + untested-function warnings + wide-blast-radius flags). Feed this into ONE of the subagent audit prompts. Subagents still do the semantic wiring / intent / cross-document audits. Graph findings feed subagents, never replace them.
- [ ] Check for: inefficiencies, dead code from refactors, optimisation opportunities
- [ ] Reliable and robust (not prone to breakage or failing)
- [ ] Duplications that need dedupe, bottlenecks
- [ ] No memory leaks using preventions
- [ ] Follows STANDARDS.md
- [ ] Check issue body scope 100% completed — no gaps
- [ ] Fix ALL problems — no deferrals, no excuses
- [ ] Run regression tests — if not run yet, run them now
- [ ] Per-stage feedback per STANDARDS.md §Per-Stage Feedback Capture — write the Stage 5 block before declaring complete

### Stage 5 Layer-B Failsafe — DOTFILES_READ_TOKEN (closes #473 via #477 Phase 8)

**Why it exists**: Layer-B failsafe `.github/workflows/stage5-completeness.yml` checks out canonical `dotfiles` (private) on every Stage 5 sign-off via `actions/checkout`. The default `secrets.GITHUB_TOKEN` is repo-scoped; cross-repo private-repo checkout returns `Repository not found` and the workflow silently FAILs across all 7 consumer repos. **Path A choice rationale**: a fine-grained PAT (`DOTFILES_READ_TOKEN`) scoped to `Contents:Read` on `dotfiles` ONLY is the minimum-scope fix — no `repo` write, no other-repo access, no organization-wide GitHub App overhead.

**Rotation cadence**: PAT expires 1 year from creation. Calendar reminder set 11 months out. When the PAT expires, Layer-B will resume failing silently — re-issue PAT in GitHub UI, re-run `setup-dotfiles-read-token.sh` against all 7 consumers (no canonical workflow change needed since the secret name `DOTFILES_READ_TOKEN` is unchanged). The `--validate` mode of any future iteration of `setup-dotfiles-read-token.sh` should grep `gh secret list` for `DOTFILES_READ_TOKEN` presence on every consumer; absence = re-run helper.

**Recovery procedure (Layer-B failures post-rotation)**:
1. **Symptom**: GHA workflow `stage5-completeness.yml` fails on a consumer-repo Stage 5 sign-off with `Repository not found` or `Bad credentials`. Verify via `gh run view <run-id> --repo hoiung/<consumer>` log output.
2. **Diagnose**: `gh secret list --repo hoiung/<consumer> | grep DOTFILES_READ_TOKEN` — empty = secret absent or expired.
3. **Re-issue PAT**: GitHub UI → Settings → Developer settings → Personal access tokens → Fine-grained tokens → Regenerate `DOTFILES_READ_TOKEN`. Same scope: `Contents → Read-only` on `dotfiles` only. New 1-year expiration.
4. **Redistribute**: paste new PAT into `/tmp/.dotfiles-pat`, `chmod 600 /tmp/.dotfiles-pat`, run `bash scripts/setup-dotfiles-read-token.sh --token-file /tmp/.dotfiles-pat`, verify all 7 consumers via `gh secret list --repo hoiung/<consumer> | grep DOTFILES_READ_TOKEN`. Delete `/tmp/.dotfiles-pat`.
5. **Re-trigger failed workflow**: `gh workflow run stage5-completeness.yml --repo hoiung/<consumer> -f issue=<closed-issue#>` and confirm receipt comment posts with PASS verdict.

**Security note**: `DOTFILES_READ_TOKEN` carries `Contents:Read` permission on `dotfiles` ONLY. It cannot:
- Perform write operations on `dotfiles` (cannot push, cannot create issues, cannot edit issue bodies — the workflow's `gh api PATCH` calls use the consumer-side `secrets.GITHUB_TOKEN` for that, which is repo-scoped to the consumer).
- Access any other repository under `hoiung/` or any organization.
- Read GitHub Actions secrets (cannot exfiltrate sibling secrets via the same token).

The token's blast radius is bounded to "read public + private file contents of `dotfiles` master branch" — equivalent to the read access an authorized collaborator would have on the canonical repo. Compromise impact: same as a clone of the dotfiles repo at the moment the token was leaked. Compromise response: regenerate per the Recovery procedure above.

## Verification Loop

- [ ] **Scope completeness gate**: Enumerate every Acceptance Criteria checkbox from issue body. For EACH one: state file:line that implements it. Any checkbox without file:line = NOT DONE. Do NOT proceed until all checkboxes have evidence.
- [ ] **Checkbox-MCP coverage gate (AP #20)**: **(0) Auto-tick precondition** (#477 Phase 6 AC 6.6 — Theme 6): inspect `SST3-metrics/.tier-a-auto-tick/<issue#>-<phase>.json` and the Issue body for `PoW [<ac_id>]: ... (auto-ticked via tier-a-auto-tick.yml)` lines. If every Tier-A box for the just-completed phase is already `[x]` with auto-tick evidence, document in the checkpoint comment ("Tier-A auto-tick processor closed N/N boxes for Phase M") and skip directly to step (4) re-verification. If no (hook unavailable / GHA disabled / sentinel never written / box-text drift caused matcher miss / network failure), proceed with manual MCP invocation in steps (1)-(3) below. Manual MCP override remains the AP #20 fallback. **(1)** if `mcp__github-checkbox__get_issue_checkboxes` is deferred, load its schema via `ToolSearch(select:mcp__github-checkbox__get_issue_checkboxes,mcp__github-checkbox__update_issue_checkbox)` per STANDARDS.md "MCP Tool Schema Loading" — bootstrap step, mandatory before the gate runs. **(2)** run `get_issue_checkboxes` and list every Tier-A box still `[ ]` that corresponds to completed work. **(3)** for each such box, invoke `update_issue_checkbox(issue_number, exact_checkbox_text, evidence)` with canonical evidence (file:line / commit hash / command+output / subagent RESULT comment-id per `../reference/tool-selection-guide.md` Example 2). **(4)** re-run `get_issue_checkboxes` and confirm every Tier-A box is `[x]`. Comment-only progress = FAIL. If this gate fails, use `update_issue_checkbox` to close every remaining box with evidence within this Gate 1 run (in-issue retroactivity, not historical — historical drift is handled separately) before declaring Gate 1 clean.
- [ ] All checkboxes verified with evidence
- [ ] Overengineering check: simpler solution exists?
- [ ] Architecture reuse check: duplicated instead of reused?
- [ ] Code duplication check: needs deduplication?
- [ ] Fallback policy check: silent failures?
- [ ] **Wiring check — 4 parts** (structural layer: `bash dotfiles/scripts/sst3-code-callers.sh <function> <lang>` + `bash dotfiles/scripts/sst3-code-impact.sh <base-branch>` when graph available per STANDARDS.md "Structural Code Queries"; semantic layer: subagent verifies each caller handles the new contract correctly. Document both layers in the RESULT block. If graph unavailable / stale / unsupported-language, fall back to grep + subagent and document why.):
  1. Every new function/method is called from at least one caller (`query callers_of(<name>)` first; grep fallback for unsupported languages)
  2. Every config key added to YAML is read by code (grep for key name in source — zero results = dead config). YAML is unsupported by graph, so grep is the primary tool here.
  3. Every SQL query's column names exist in the target table (verify with `\d tablename` or migration file)
  4. Every None-producing code path: confirm callee's type annotation accepts `Optional` / has null guard
- [ ] **Marker-substring enumeration (AP #24, #477 Phase 4 AC 4.4)**: if the change introduces, modifies, or removes a marker substring (error-message partition, counter name, diagnostic flag, feature-gate literal, status-enum value, log-line prefix, partition key), run `grep -rn -F '<exact_marker_substring>' src/ tests/ scripts/ --include='*.py'` (or per-language equivalent) and confirm the count matches the Stage 1 baseline recorded in the Issue body as "Known Emit Sites: (N)". Mismatch = FAIL — either implementation added emission sites that should have been in scope (expand scope) or removed sites that shouldn't have changed (revert removal). Skip-clean if no marker substring change in this Issue. Canonical rule: `ANTI-PATTERNS.md` AP #24 (Marker-Substring Changes Without Full Emit-Site Enumeration); cross-reference: `STANDARDS.md` "Marker-Substring Discipline".
- [ ] **Regression tests**: Run project test suite, verify no regressions
- [ ] **Quality scan**: No inefficiencies, no bottlenecks, no memory leaks, no dead code, STANDARDS.md compliant
- [ ] **AP #18 Sample Invocation Gate (#447 Phase 5 wrapper-script trigger)**: if the change touches pipeline / backtest / SL1 / SL2 / orchestration / CLI-wiring / cross-module function-arg propagation / **persistent-state write (JSONB schema mutation, SQL literal drift across SET and READ sites, DB column rename, enum-value drift)** / **any `../scripts/sst3-*.sh` wrapper change** → a REAL-CLI sample invocation must be run BEFORE close. For service shapes: 8-item liquid basket against real DB. **For wrapper-script shapes: real-CLI invocation against ≥3 repo shapes (auto_pb / job-hunter / dotfiles) + raw-tool counter-query for recall comparison**. Exit code 0 alone insufficient — verify row-count landed, downstream consumers succeeded, contamination audit OK, wrapper-vs-raw delta within tolerance. Document the sample log path + verification queries + wrapper/raw delta in an Issue comment. If NOT in-scope, document the scope-skip reason. Canonical: ANTI-PATTERNS.md #18 (per-shape table from #447 Phase 7) + STANDARDS.md "Testing Priority — Workflow Validation Gate".
- [ ] **Raw-tool cross-validation gate (#447 Phase 5)**: if any Verification-Loop check above used `../scripts/sst3-code-*.sh` output as load-bearing evidence (callers count, large-fn list, dead-code candidates, blast-radius, untested-py results), dispatch ONE Layer-3 subagent to run the raw equivalent (grep / direct ast-grep / find / git log) and compute delta. Wrapper says 0 + raw says ≥1 = wrapper recall miss = FAIL the originating check until reconciled. Wrapper says N + raw says M with `|N-M|/max(N,M) > 0.2` = wrapper-lane SUSPECT, file a `solo/wrapper-fix-<bug>` Issue. The 20% bound is empirical (#445 R4 wrappers landed at 0% delta on structural angles).
- [ ] **Mirror-lane verification (#460 Phase 8 W5 — AP #9 single-source-edits enforcement)**: when ANY change touches a canonical file with mirror entries in `SST3/drift-manifest.json` (`vendored_files` lane B) OR the SST3 section above the boundary marker in CLAUDE.md (template lane A), BOTH lanes must be exercised. Lane A: `python3 scripts/propagate-template.py --all --dry-run` exit 0 (no SST3 section drift across consumers). Lane B: `python3 scripts/propagate-mirrors.py --dry-run` exit 0 + `python3 scripts/propagate-mirrors.py --validate` exit 0 (no mirror drift, no missing manifest entries). Failure on either lane blocks Gate 1 until reconciled. Skip-clean when the diff touches no canonical-mirror-tracked surface.

## Per-Stage Feedback Capture

Canonical: STANDARDS.md §Per-Stage Feedback Capture (the single source of truth — schema, channel-separation rule, FP-handling rule, DRIFT ALERT spec, activation-sha gate, post-compact reconstruction protocol, 3-layer enforcement). Each stage above ends with a per-stage feedback bullet. Aggregator + reporter + shape-match: see `../scripts/leader-feedback-aggregate.sh --report | --summarize | --shape-match | --staleness`. Pre-commit hook `sst3-metrics-feedback-present` is Layer A; persistent sentinels under `.sentinels/` (gitignored) are Layer B; the per-stage bullets above are Layer C.

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
