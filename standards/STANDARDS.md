# Engineering Standards

## Foundational Philosophy

**Quality First**: SST3 sets the execution standard for all projects built with it.

**Quality Attributes**: Maintainability, Accuracy, Standardized, No Regression, Transparency, Intentional, Enforcement, Reusable, Predictability, Testability, Robustness, Reliability, Discoverability, Prevention > Cure.

**ROI = Quality Execution** (not token/time savings). Token efficiency is a byproduct, not the goal.

**Clarity > Brevity** (Issue #141): Prune based on quality (JBGE + LMCE), never to hit a number. Clear instructions prevent rework.

## Core Principles

## Achieving Quality

**Quality Attributes Table**: AI-optimized reference for execution standards

| Attribute | Definition | How to Achieve | Enforcement |
|-----------|-----------|----------------|-------------|
| **Maintainability** | Self-cleaning, organized, evolves without cruft | Follow housekeeping checklists, document files, archive superseded | Verification Loop, pre-commit hooks |
| **Accuracy** | Conforms to evidence, results, factual requirements | Verify against actual values, test with real data, cite sources | Stage 1 Research, Verification Loop |
| **Standardized** | Consistent patterns, uniform naming, predictable organization | Use templates, follow tool standards, maintain structure | issue-template.md, Tool Standardization |
| **No Regression** | Changes don't break existing functionality | Check call sites, run existing tests, verify compatibility | Verification Loop, pre-commit hooks |
| **Transparency** | Factual reporting, researched claims, honest analysis | Provide evidence not claims, challenge assumptions, document sources | Critical Thinking, Ralph Review evidence |
| **Intentional** | Deliberate decisions, not accidental changes | Plan before implementing, document rationale, avoid scope drift | Stage 1 Research, Triple-Check Gate |
| **Enforcement** | Validation through checkboxes, gates, scripts - not honor system | Verification Loop, Ralph Review, pre-commit hooks | SST3 is Enforcement principle |
| **Reusable** | Designed for reuse, not one-off solutions | Modular components, clear interfaces, avoid hardcoding | Modularity, Codebase Review |
| **Predictability** | Expected results, no surprises, consistent behavior | Document behavior, test edge cases, fail fast with clear errors | Fail Fast, Verification Loop |
| **Testability** | Code designed to be verifiable and validated | Write tests first, isolate dependencies, provide test fixtures | Verification Loop, regression tests |

**Behavioural enforcement** (the table answers "what does quality mean?", this answers "what must I DO?"):

| Action | Enforced by |
|---|---|
| Use existing before building | Stage 1 Research, Codebase Review |
| Complete scope fully (no partial) | Verification Loop (fully working) |
| Self-clean and housekeep | Cleanup Requirements, pre-commit hooks |
| Leave codebase better than found | Stage 5 Post-Implementation Review |
| Realign when scope drifts | Triple-Check Gate (Stage 3) |
| Regular self-check vs original plan | Phase checkpoints |

**JBGE** (Just Barely Good Enough): Document only what prevents problems.

**Discoverability Requirement** (Issue #119): All SST3 files MUST be discoverable from CLAUDE.md in EVERY repo.
- **Chain**: CLAUDE.md → workflow/WORKFLOW.md → stage-X → feature (<=4 steps)
- **Validation**: `python scripts/check-discoverability.py` during Verification Loop
- **Exception**: CLAUDE_TEMPLATE.md (template), .sst3-local/ (project-specific)
- **Enforcement**: Verification Loop BLOCKS merge if any repo fails discoverability check

**Don't Explain Claude to Claude** (Issue #119): Document YOUR rules/decisions/patterns. Not model capabilities or standard practices. ✓ "Ralph Tier 1 uses haiku for surface checks" ✗ "Haiku is fast"

**LMCE** (Lean, Mean, Clean, Effective): JBGE defines *what* to keep; LMCE defines *how* to deliver it.
- **Lean**: Remove if removable without breaking. Keep only if ROI > 1x.
- **Mean**: Actionable commands. Strip "consider", "might", "it's important".
- **Clean**: Findable in <30 seconds. No >10-line blocks without headers/bullets.
- **Effective**: Root cause, not symptoms. Simplest permanent solution.

**Pruning rule**: Keep examples that prevent real problems and decision thresholds. Remove AI-known explanations and motivational language. If pruned content caused problems, restore it.

See: `ANTI-PATTERNS.md` for top 5 recurring problems (Issue #79)

**AI-First Documentation** (Issue #153): Internal docs optimize for AI consumption.

**Three-Category Framework**:

| Category | Examples | Rule |
|----------|----------|------|
| Internal AI-to-AI | WORKFLOW.md, checklists | Remove tutorials/motivation. Keep commands/criteria/guardrails. |
| User Touchpoints | PR diffs, Issue comments | Keep human-readable, 30-second scan. |
| Hybrid | STANDARDS.md, WORKFLOW.md overview | Tables+bullets for AI, context for user. |

**Decision Rule**: User ever reads it → keep human-readable. AI-only → optimize for AI.

**Remove from AI-to-AI**: tutorials, "Purpose" sections, motivational language, teaching examples.

**Always Keep**: checklists `[ ]`, commands, decision thresholds, MANDATORY/CRITICAL/NEVER tags, file paths, issue refs, tables, DO/DON'T, pattern→fix pairs, If X→do Y recovery steps.

**Compression, not deletion** (Issue #124): preserve all functional content.

## Engineering Practices

### Use Existing Before Building
- Research existing libraries/packages FIRST
- Evaluate: popularity, maintenance, license, security
- Build custom only when existing solutions don't fit
- Document why existing solutions rejected

See: `../workflow/WORKFLOW.md` (Stage 1 — Research) for detailed library research process.

### Critical Thinking & Honest Analysis

**Critical Thinking**: AI must challenge ideas with evidence, not validate blindly.

**DO**: Disagree with evidence when flawed. Find holes/edge cases/trade-offs. Surface risks early.
**DON'T**: Validate blindly or cherry-pick positives.

**BAD**: "Good idea! I will proceed." **GOOD**: "Method X is O(n^2); Method Y is O(n). Recommend Y unless constraint requires X."

See: ../workflow/WORKFLOW.md (Stage 1 — Research) for research-specific critical thinking

### Never Assume — Always Check

**Principle**: Read the actual source before drawing conclusions. Assumptions cause silent errors.

**DO**: Read before editing. Check actual values. Verify function/pattern exists before referencing.
**DON'T**: State file contents without reading. Assume variable names or API shapes from memory. Skip verification.

**Pattern**: When in doubt → Read first, conclude after.

### Factual Claims Must Have Provenance

**Principle**: No number without a source. Every quantified claim in documentation, issue bodies, commit messages, or review comments must be backed by a verifiable source.

**Rules**:
- Every number must have a **verification method**: a command that produces it, a document that cites it, or a calculation that derives it
- Estimates must be labelled as estimates ("~6 months", "up to $1.25M") — never presented as precise facts
- "Seems reasonable" is NOT a source. If you cannot reproduce the number, do not write it
- When researching facts, use **multiple independent sources** (code, git history, external documentation) — never trust a single unverified claim
- AI agents must use subagents to **research and verify** before stating facts — read the actual code, run the actual command, check the actual data

**Verification Methods** (in order of preference):
1. **Reproducible command**: `git log --oneline | wc -l` → "10,385 commits"
2. **API query**: `gh issue list --state all --json number` → "1,309 issues"
3. **Code reference**: `grep -c "def test_" tests/` → "N test functions"
4. **Document citation**: "per Joel Sing Feb 2022 award citation in MASTER_PROFILE.md"
5. **Calculation**: "(total - open) / total = 99.4% close rate"

**Anti-patterns**:
- ❌ "3-5 concurrent agents" with no measurement or architectural derivation
- ❌ "catches 85% of bugs" with no data source
- ❌ "average of $1.25M" when source says "up to $1.25M"
- ❌ Repeating a number from another document without verifying it is still accurate

**Enforcement**: Ralph Review Tier 2 (Sonnet) — Evidence Quality section. User Review Checklist — Gap Analysis section.

### User Assertion = Immediate Source Verification

**Principle**: User assertion = verify source IMMEDIATELY. Do not debate; do not validate without checking. Source file is ground truth.

**Rules**:
1. **User asserts → grep source immediately**, with multiple synonyms and partial-figure variants. Don't grep just `676K`; grep `676|redhill|3fp|digital realty`.
1b. **Handover claim → grep source immediately** (Theme 1, #477): same discipline applies to claims sourced from prior-research handovers, post-compact recovery summaries, or memory entries — not just user assertions. When entering a session with a handover that names file:lines / counts / table sizes / function-existence assertions, the main agent extracts 3-5 headline claims and verifies each via raw-grep / direct read BEFORE dispatching the Stage 1 swarm. Document drift in the research file as "handover claim X corrected from Y to Z before swarm dispatch". Memory ≠ source of truth; a handover is a starting hypothesis, not a frozen contract. Cross-reference: Leader.md Stage 1 step 1a.5 (PRE-SWARM SOURCE-VERIFICATION GATE for handover claims); ANTI-PATTERNS.md AP #14d (Scope-gap blindness — Stage 1 research specific).
2. **Never say "you're right" before checking**. Verification is the response, not validation.
3. **Never debate or push back** based on a subagent's earlier finding. The subagent could have missed it.
4. **Trust structured data** (tables, PO lists, project enumerations) over narrative paraphrases or subagent summaries.
5. **Report verbatim with line numbers**. No editorial. If the source genuinely contradicts the user, quote the source verbatim and let them decide.
6. **Cross-check swarm subagent claims against source before applying ANY removal or change**. Two swarm subagents disagreeing → read MASTER directly. Don't pick the "safer" recommendation.

**Anti-patterns**:
- ❌ "You're right!" followed by an edit you made without checking
- ❌ Removing a claim because a subagent said "not in MASTER" without grepping yourself
- ❌ Trusting v2 swarm output over v1 swarm output without reading source
- ❌ Grepping a single narrow term and concluding "not found"
- ❌ Debating with the user from memory ("I'm sure I checked that")

**Enforcement**: Every fact-removal, every dollar-figure change, every date change, every claim deletion must be preceded by a direct source read. The swarm recommends; you verify; the source decides.

### Research Must Be Applied Collectively, Never Singularly

**Principle**: Every change must integrate ALL relevant sources in the same pass. Single-source edits silently override constraints from every other source. (Applies to: code, CV, config, any multi-source artefact.)

**Rules**:
1. Before any edit to a multi-source artefact, load ALL referenced research/profile/memory files. Not the relevant one. All of them.
2. Check every proposed change against every loaded source in the SAME pass, not sequentially. Any failed check = invalid edit.
3. Conflicts between sources must be resolved EXPLICITLY via documented conflict-resolution rules. Never silently pick one.
4. New audit/subagent output is ADDITIVE to the collective, never replacement.
5. The mandatory-reading list at the top of any skill / CLAUDE.md is non-negotiable. Reading 1 of N = reading 0.
6. Commit messages must name every source consulted. Shorter than the mandatory-reading list = invalid edit.
7. **SST3 self-reference**: never edit a STANDARDS / ANTI-PATTERNS / workflow / template / ralph / hook file without cross-checking the rest of the SST3 corpus first. The corpus governs itself.

**See ANTI-PATTERNS.md #9** for evidence, root cause, worked examples, and self-healing.

### Subagent Orchestration Discipline

**Principle**: Use MANY subagents in LAYERS, cross-checking from different angles. Verify every finding against source. Document proof method inline.

**Rules**:
1. **Subagent count is dynamic**: cover every directory, file, and claim category line-by-line. NEVER 2-3 as default. Size to work (e.g. 12 categories → ≥12 subagents, 20 files → 4-5 subagents). Stinginess produces shallow skims.
2. **Layered cross-checking**: dispatch a second wave of subagents from a DIFFERENT angle to verify the first wave. Layer 1 = "find the violations". Layer 2 = "verify each violation isn't a false positive". Layer 3 (if applying changes) = "verify the proposed fix doesn't break anything else".
3. **Different angles per layer**: layer 2 must NOT use the same prompt or framing as layer 1. Different lens = different blind spots = real cross-check.
4. **Main agent verifies, never assumes**: every subagent finding is read against source by the main agent before being acted on. The swarm recommends; the main agent verifies; the source decides.
5. **Factually provable AND documented**: every claim/figure/decision must be provable AND the proof method (file:line, command, query, source-doc reference) must be documented inline so future audits can re-verify it without re-deriving from scratch.
6. **Prevent false-positive flagging by design**: when a section is intentional architectural design (defence-in-depth, intentional duplication, specialised verbosity), document it inline so future audits skip it.
7. **No stingy exceptions**: "to save time" / "to save tokens" / "the task is small" are NOT valid reasons to dispatch fewer subagents. Cost is not a constraint; quality is.
8. **Orchestrator MUST embed wrapper-lane caveats in subagent prompts, not just in the RESULT schema**. When dispatching a subagent that may invoke wrapper-lane queries, the orchestrator's prompt MUST explicitly name the known caveats: (a) `mcp_graph_available: yes|no` as first RESULT line (AP #19; under wrapper-lane this is always `no` per Issue #445); (b) `search` is keyword-only — there are no embeddings; verify with synonym sweep before any "no match" conclusion; (c) current `last_updated` (repo HEAD time, not query freshness — wrapper-lane is stateless); (d) inner-engine availability (exit 127 = ast-grep / ripgrep / jq missing). The RESULT schema is a receipt check — the prompt-embedded reminders are the primary trigger. Author-time drift (orchestrator writes the rule but forgets to embed it in dispatched prompts) is the documented failure mode (round-5 S1 + N45 — 2× corroboration).

**Procedural minimum** for any audit-driven change to a multi-source artefact:
1. Layer 1 swarm (sized to cover every angle of the audit): identify violations
2. Layer 2 swarm (sized to verify every layer-1 finding): false-positive sweep — verify each violation isn't documented architectural design
3. Main agent: read source for every confirmed violation before applying any edit
4. Apply edits with inline proof-method comments where helpful
5. Layer 3 swarm (3-5 subagents): verify applied edits didn't break cross-references or surface new violations

**See ANTI-PATTERNS.md #14** for the no-discipline failure modes.

#### Stage 1 Layer-2 Adversarial Gap-Finder Discipline (Theme 8, #477)

**Principle**: Layer-1 swarm finds what's in scope; Layer-2 adversarial swarm finds what Layer-1 missed. Different lens = different blind spots = real gap coverage. Mandatory for infrastructure / governance / cross-cutting Stage 1 research.

**The Layer-2 prompt** (verbatim template): "Layer-1 found X, Y, Z. Find 3 things they missed — either (a) false-positive claims already covered by modern equivalents, or (b) genuine gaps not yet surfaced." Layer-2 prompt MUST differ from Layer-1 (per AP #14c).

**Two failure modes Layer-2 catches**:

1. **False-positive legacy claims**: Layer-1 cites an obsolete API / registry key / convention that has a modern equivalent already in use. Examples (worked examples, surfaced in #477 research):
   - Layer-1 cited Win10 `SetUserFTA` legacy API → Layer-2 surfaces Win11 24H2 modern path: `UserChoice ProgId` registry under `HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts`. Apply: replace SetUserFTA invocation with UserChoice ProgId write.
   - Layer-1 cited deprecated registry key for default-app association → Layer-2 surfaces `dism.exe /Set-DefaultAppAssociation` modern equivalent shipped in Win10+. Apply: prefer dism.exe over registry direct-write.

2. **Scope-adjacent genuine gaps**: Layer-1's angles cover the named scope but miss adjacent surfaces. Examples:
   - Layer-1 swarm covers Stage 1 hooks → Layer-2 surfaces Stage 4 sample-invocation gate also needs the same angle (#477 Themes 1+8 cross-cutting).
   - Layer-1 covers `feedback_parser.py` schema → Layer-2 surfaces `check-closure-loop-applied.py` pre-commit hook also reads the schema (closure-loop integrity gap).

**Main-agent verification gate**: when Layer-2 surfaces a false-positive correction (e.g. "Layer-1 cited X but modern equivalent Y exists"), the main agent MUST verify the equivalence against source before accepting the correction. Document the verification method inline (command run, file:line, URL). Drift between Layer-1, Layer-2, and source = block scope-acceptance until reconciled. Pattern: dispatch a verification subagent with the prompt "Run `grep / ls / Query` against <file>:<line> to confirm whether <Layer-1 legacy claim> or <Layer-2 modern equivalent> is present in the actual codebase. Report file:line + verbatim quote." Both Layer-1 and Layer-2 outputs are recommendations; the source decides (per AP #14c).

**Enforcement**: Leader.md Stage 1 step 2a (Layer-2 adversarial gap-finder MANDATORY). ANTI-PATTERNS.md AP #14d (Scope-gap blindness — Stage 1 research specific).

#### Acceptance Criteria Measurability Gate (Theme 10, #477)

**Principle**: Every Acceptance Criteria checkbox MUST have an explicit verification command/method that is **falsifiable** (binary pass/fail). Unfalsifiable ACs leak through Stage 2 audit because subagents can rubber-stamp ambiguity ("looks reasonable") — the gate MUST fire BEFORE swarm dispatch, not after.

**Failure mode**: subjective ACs ("cleaner architecture", "better performance", "improved coverage") get marked `[x]` at Stage 4 with vibes-based evidence. Stage 5 audit can't reject them because there's no falsifiable test to fail. The contract becomes infinitely flexible.

**Reject (unfalsifiable)** — examples observed in #477 prior-feedback aggregation:
- "subsystem length ≤500 lines" — line counts not bound to a specific file/path
- "improved coverage" — no metric, no threshold, no source of truth
- "cleaner architecture" — subjective, no test
- "better performance" — no baseline, no measurement, no pass/fail
- "more maintainable" — no proxy metric (cyclomatic complexity, file count, dep count)
- "reduce duplication" — no count of duplicates eliminated

**Accept (falsifiable)**:
- ``wc -l <specific-file>`` returns N where N ≤ 500 (file path explicit)
- ``pytest tests/<specific>.py`` exit 0 (or specific test count)
- ``grep <pattern> <specific-file>`` returns ≥N matches (pattern + file explicit)
- ``coverage report --include=<file>`` returns ≥N% (N stated)
- ``radon cc <file> -a`` returns avg ≤B (or per-function rank ≤C)
- File at `<specific-path>:<line-range>` contains the named text/structure (verbatim)
- Command + expected output recorded inline in the AC

**Enforcement**:
- Leader.md Stage 2 step 4e (AC verifiability sweep — author runs before subagent dispatch).
- issue-template.md "AC Verifiability Gate" subsection (template-time gate).
- Stage 3 sanity-check subagent angle: any AC without falsifiable verification = block issue creation until rewritten.

**Apply rule**: ACs without falsifiable verification get rewritten in-place OR moved to Cleanup Requirements with rationale BEFORE subagent dispatch. Do NOT pass unfalsifiable ACs into the Stage 3 swarm — subagents anchor on whatever scope they receive.

**Verify**: ``grep -cE '^- \[ \] \*?\*?\(?[0-9]+\.[0-9]+' <issue-draft>`` returns count of ACs; spot-check 3-5 random ACs and confirm each carries either a verification command (`grep`/`wc`/`pytest`/`exit 0`) OR a verbatim file:line target. Document any reject→rewrite in the per-stage feedback file Stage 2 `worked` field.

#### Scope Snippet Rule (#406 F5.1)

When dispatching ≥10 subagents on an issue, the main agent writes a **frozen scope snippet** (≤2K tokens, scope + acceptance criteria only) to `${SST3_TMP:-/tmp}/sst3-issue-<N>-scope.md` and passes the path to subagents instead of the full issue body. ONE "scout" subagent reads the full issue and validates that the snippet covers the relevant scope. Saves O(N × full-issue-tokens) of subagent context bloat.

#### RESULT Block Schema (#406 F5.2)

Every swarm subagent ends its return with a fenced block:

```
## RESULT
- verdict: pass|fail|unknown
- files_touched: [...]
- findings: [{path, line, claim, evidence}]
- tee_log: <path or none>
- scope_gaps: [...]
```

Main agent parses the RESULT block; subagent prose body is informational. Reduces typical 4-8K-token return per subagent to ~500 tokens with zero signal loss because every claim already has provenance per Rule 5 above. **When a subagent discusses graph queries, prepend `mcp_graph_available: yes|no` as the FIRST line** — AP #19 L443 (Ralph Tier 1 uses this to discriminate "no access" from "lazy fallback"). **Wrapper-lane disposition (Issue #445)**: under the wrapper-lane, this field is always `no` — wrappers are bash-tool calls, not MCP-protocol calls, and subagents do not inherit the bash-tool set from the main agent in the same way. Documented fallback (grep + manual file reads) is the expected path under wrapper-lane, not a degradation. **Historical semantics (G-3 fix, #444; retained for reference)**: in the MCP-native phase the field reflected the LAST graph call's result. A subagent that probed `yes` then hit a mid-stream stdio EOF / 401 / `MCP error -32000: Connection closed` MUST set this to `no` so Ralph Tier 1 reads grep-fallback evidence as DOCUMENTED fallback, not "lazy". Ralph Tier 1 sees `no` + valid fallback evidence → PASS, not FAIL.

### Bash Output Budgets (#406 F4.7)

Default flags for the 10 commands SST3 runs hot. Provenance: each row backed by file:line in the audit findings of #406. The `tee-run.sh` wrapper (`../scripts/tee-run.sh <label> -- <cmd>`) provides recovery for any compressed output: full log saved to `~/.cache/sst3/tee/`, last 200 lines printed.

| Command | Default | Why |
|---|---|---|
| `git status` | `--short --untracked-files=no` | Avoid 200-line untracked dump (per `MEMORY.md` "never use -uall flag") |
| `git log` | `--oneline -20` | Full pager output is ~600 lines; agent needs 10-20 subjects |
| `git diff` | `--stat` first, then targeted `git diff -- <file>` | 20K-line diffs collapse to file list + hunk count |
| `pytest` | `-x --tb=line -q --no-header` (use `tee-run.sh pytest -- pytest …`) | Fail-fast, one-line tracebacks. tee-run preserves full log on disk. |
| `grep` (content search) | Use the **Grep tool** with `head_limit`, NOT bash `grep` | Tool is dedicated and observable |
| `find` (file discovery) | Use the **Glob tool**, NOT bash `find` | Tool is dedicated and observable |
| `Read` on file > 1500 lines | Grep first, then `Read` with `offset` + `limit` | Eager full reads burn 10K+ tokens for one function |
| `gh issue view` | `--json title,body,state --jq '...'` always; comments via separate `--json comments --jq '.comments[-5:]'` | Avoid 50-comment dumps |
| `curl` | `--fail --max-time 30` (any JSON consumer pipes through `jq -e .`) | Fail loud on HTTP errors; no invalid-JSON consumers |
| Logs | `tail -n 100` or `tee-run.sh logs -- cat <log>` | Never `cat` a log of unknown size |

Rule of thumb: any single Bash invocation that produces > 200 lines should be wrapped with `../scripts/tee-run.sh <label> -- <cmd>` so the agent gets the tail and the full log is recoverable.

### Structural Code Queries — Wrapper-Lane First, Subagent Fallback

For structural code questions (callers, callees, imports, inheritance, blast radius, dead code, large functions, test coverage) in a language the wrapper-lane parses (Python, TypeScript, TSX, JavaScript, Rust — the five languages ast-grep is wired for in the wrappers), prefer **wrapper-lane** bash queries (`bash dotfiles/scripts/sst3-code-*.sh`) over subagent exploration — when the pre-query gate passes:

1. **Wrapper invocable**: `bash dotfiles/scripts/sst3-code-status.sh` exits 0 and emits valid JSON `{last_updated, file_count, source_languages}`. The lane is stateless — there is no graph to build. `file_count` reports the count of supported source files in the target repo (audit-trail aid, not a precondition).
2. **No staleness — every call re-parses from disk**. The wrapper-lane has no persistent cache; `sst3-code-update.sh` is a no-op contract-preservation shim. `last_updated` reflects the repo HEAD commit time, not query freshness.
3. **Target file / project language is in the supported list**. If not (Markdown, YAML, JSON, SQL, TOML, shell, HTML, Jinja, Dockerfile, etc.), skip the wrapper-lane; use subagent exploration.
4. **`search` is keyword-only**. The wrapper invokes ripgrep (`--literal` mode) or ast-grep structural patterns — there are no embeddings, no semantic similarity. Any "no match" must be cross-checked with a synonym sweep before drawing a negative conclusion.
5. **Spot-check one result** by reading source before drawing conclusions. "Never Assume — Always Check" applies to wrapper output the same as to memory or subagent summaries.
6. **Data-layer boundary** (round-5 N54): if the structural question spans a data-layer boundary (ORM ↔ SQL, HTTP ↔ service, JSONB ↔ Python type, serialisation round-trip, enum ↔ DB literal), wrapper-lane alone is INSUFFICIENT — it is AST-only; does NOT verify DB column existence, SQL literal values, JSONB schema, or runtime types. Verify per STANDARDS.md "Contract Verification" + AP #18 real-DB sample invocation. Field evidence: JSONB schema mismatch between planned-state and realized-state tables caught only by real-DB invocation (round-5).

The wrapper-lane is **NOT a replacement** for subagents. See ANTI-PATTERNS.md AP #19 for the full list of 12 subagent-only moments (voice, intent, cross-document, non-code audits, etc.) that MUST NOT be demoted by a "wrapper-first" rule.

**Naming-honesty note (Issue #445 Stage 5)**: the lane is called "wrapper-lane", not "graph". There is no graph database, no SQLite, no Tree-sitter store, no embeddings. Every query re-parses on disk via ast-grep + ripgrep + git. Field names in the wrapper JSON output reflect what is actually computed (`file_count`, not `total_nodes`); historical names from the displaced upstream MCP appear only inside HISTORICAL-MCP-REFERENCES blocks.

**Non-interactive shell PATH bootstrap (Issue #456)**: wrappers self-augment PATH via `../scripts/sst3-bash-utils.sh` (sourced by 31 of 38 end-user wrappers) so engines under `~/.cargo/bin`, `~/.local/bin`, `~/.npm-global/bin` resolve from `bash --noprofile --norc -c '...'` (the shape Claude Code's Bash tool spawns). Without this bootstrap, `.bashrc` early-returns on non-interactive shells and engines on disk are invisible. The 8 exempt wrappers (system-PATH-only + the meta-validator that self-bootstraps inline) are listed in `../scripts/.bash-utils-exempt-list`; the `check-wrapper-bash-utils-source` pre-commit hook (declared BEFORE `sst3-self-test`) catches future drift at commit time.

See also `../reference/tool-selection-guide.md` "Decision Tree: Code-Understanding Queries" and `../dotfiles/docs/guides/code-query-playbook.md`.

**Three-signal contract policy (#447 Phase 5)**: every wrapper emits a quorum of (exit code, stdout NDJSON, stderr sentinel) — consumers MUST check ≥2 of 3 to declare clean. Single-signal trust is a known wrapper failure mode (silent-zero, silent-clean, sentinel-missing classes). The full 33-shape failure-mode taxonomy lives in `../dotfiles/docs/research/wrapper-lane-vs-raw/03_comparison.md` — out-of-line to keep this section actionable.

**Raw-tool cross-validation REQUIRED moments (#447 Phase 5)**: dispatch a raw-only subagent counter-query in these 4 cases — (a) any change to wrapper-lane scripts (`../scripts/sst3-*.sh`); (b) any structural query producing zero results (silent-zero is the failure mode this catches); (c) any post-implementation review of changes >100 LOC; (d) any time a subagent's RESULT block contains `wrapper_invokable: yes` AND `wrapper_invoked: no` without documented reason. The raw-only counter-query is the audit-time failsafe for wrapper recall drift; without it, wrapper bugs cascade through Stage 4 + Stage 5 invisibly.

**AI-agent fallback heuristic (#447 Phase 5; semantics clarified by Issue #456)**: when a wrapper exits 127 / 1 / 2, the agent MUST — (1) look up the failed query type in `../dotfiles/docs/guides/code-query-playbook.md` "Raw Fallback Recipes" table, run the listed raw command, and record the substitution + raw command + result count in the RESULT block; (2) if no table row matches the query, escape to subagent-only mode per AP #19 12-moments carve-out, citing "no fallback recipe" as the escape reason; (3) NEVER silently substitute raw output for wrapper output without recording the substitution — silent fallback hides recall delta which is the exact signal Phase 5 cross-validation depends on. **Exit 127 semantics post-#456**: means the engine is genuinely missing on disk (npm/cargo/pipx install never ran). Pre-#456 the same code ALSO fired when the engine was on disk but PATH was not propagated to non-interactive shells; that case is now closed by `sst3-bash-utils.sh` self-bootstrap. Run `scripts/install.sh` to install missing engines — do NOT add custom PATH workarounds in the calling agent.

### Double-Guardrail Principle (N32 — user-authoritative)

**Principle**: every `/Leader` invocation verifies work against BOTH guardrails — the cross-cutting SST3 canonical (STANDARDS.md + ANTI-PATTERNS.md + WORKFLOW.md + project CLAUDE.md) AND the invoked-skill's domain canonical. Skill-specific rules are NOT suggestions; they are load-bearing canonical, equal in authority to SST3 standards within the skill's domain. Single-guardrail `/Leader` runs on non-SST3-infrastructure work operate with half their guardrails missing.

**Failure mode**: `/Leader 1-6` on a blog / CV / eBay / claude-api task passes every SST3 check but silently violates the skill's domain canonical — banned voice words slip through, Seagate series HARD CONTRACT breached, prompt-caching not wired, claude-api model ID stale. Deliverable looks clean against SST3; fails against skill.

**Invoked-skill canonical by domain** (load-bearing references — see skill definitions for the full rules; this table is a pointer, not a restate):

| Skill | Canonical rules |
|---|---|
| `blog` / `job-hunter` / CV / LinkedIn | `voice_rules.py` banned words + KEEP_LIST; `iamhoi` / `iamhoiend` marker wrapping (carve-outs: `iamhoi-skip` / `iamhoi-skipend`); `check-ai-writing-tells.py` exit 0 |
| `ebay-seller-tool` | Seagate series HARD CONTRACT; 21-field listing contract; SMART gate; dual-path BOTH directions; never-dispute-customer |
| `claude-api` | Prompt caching wired on every cacheable prompt; model IDs current (no retired models); SDK idioms |
| `SST3-solo` / `Leader` | Cross-cutting SST3 canonical + AP #19 12-moments carve-out + stage-order discipline |
| Project-specific (`auto_pb`, `tradebook_GAS`, etc.) | Paper/live parity; never-touch-production-positions; RTH-only E2E; per-project CLAUDE.md rules |

**Stage-by-stage integration**:

- **Stage 1 step 0a**: identify invoked skill + record `invoked_skill` + `skill_canonical_files` in the research file. First link of the chain; downstream stages read from this.
- **Stage 2**: main-agent author-time compliance — draft MUST NOT violate skill canonical.
- **Stage 3**: subagent angle verifies draft against skill canonical (main agent verifies against source).
- **Stage 4**: main-agent implementation-time compliance at every edit + Ralph Tier 2/3 verify + Gate 1 Verification Loop runs the skill's own verification hooks (e.g. `check-ai-writing-tells.py`, pre-commit hooks) with evidence in issue comment.
- **Stage 5**: Post-Implementation Review subagent angle audits delivered work against skill canonical; same verify-against-source discipline as the graph-backed audit.

**Enforcement**: Leader.md Guardrails block (all stages) + Stage 3 subagent angle list + Stage 4 Gate 1 checkbox + Stage 5 Post-Implementation Review appendix. Absence of skill-canonical checking on a non-SST3-infrastructure task = violation.

**Evidence**: round-5 user observation N32 (2026-04-20) — "Leader 1-6 should incorporate checking against the workflow of the skills that been invoked too, otherwise it just checks SST3 workflow and standard and anti-patterns ... The SST3 should also have this integrated, so it's like a double guardrail." Pre-existing research: `docs/research/LEADER_SKILL_ENGINEERING_2026_04_12.md` (AI-to-AI prompt engineering + Stage-4 conflation fix + Ralph tier design).

#### Skill-Canonical Audit Template (Comprehensive Walk)

**Use for AUDIT prompts** (Stage 2 author / Stage 3 subagent / Stage 5 subagent): walk every section of the invoked-skill canonical, return per-section pass/fail. **NOT for INVARIANT GATES** (Ralph checklists, Stage 4 Gate 1, AC checkboxes, Mirror-lane triggers, file:line/exit-code checks) — gates verify named conditions; audits verify a draft against a multi-section canonical.

**Scaffolding** (subagent receives verbatim):

> Read EVERY file in `skill_canonical_files` (Stage 1 metadata). For each: walk every `## ` and `### ` heading; for non-markdown structure (numbered `### 1.`, `**bold**` headers, prose-only) walk every numbered/bold/prose section as a logical unit. Per section, identify rules + verify [draft|delivered work] does not violate any. Do NOT pre-filter. Return per-section [PASS|FAIL|N/A] with file:line evidence for any FAIL, tagged by `source_file`.

**Fallbacks**: (a) empty `skill_canonical_files` → walk "Double-Guardrail Principle" pointer-table row + URLs; document in RESULT. (b) missing on disk → `verdict: fail` + `error: missing_canonical_file: <path>`. (c) multi-canonical → aggregate `section_failures`, tag by `source_file`.

**RESULT extension**:
```
section_failures: [{source_file, section_heading, canonical_file_line, draft_violation, evidence}]
canonicals_walked: [list of files actually walked]
fallback_applied: <none|inline_pointer_table|multi_canonical_aggregation>
```
Coverage = `canonicals_walked` matches `skill_canonical_files` (no separate counts).

**Failure diagnosis**: (a) subagent failure (in walked file, RESULT omitted → re-dispatch); (b) template failure (heading regex didn't match → widen); (c) canonical incompleteness (absent everywhere → add to canonical / pointer table).

**Prevents**: AP #23 (curator-bounded audit recall). **Stage refs**: Leader.md Stage 2 author + Stage 3 subagent + Stage 5 subagent. Multi-skill dispatch (split >5K tokens) lives in Leader.md Stage 3.

### Contract Verification — Three Contracts (Issue #1407 post-mortem)

Every change that crosses a boundary must verify all three contracts:

**1. Type Contract**
- Every function parameter with a non-Optional type annotation: grep all call sites and confirm no `None` can flow in
- If any caller can pass `None`, the annotation MUST be `T | None` and the function MUST have a null guard
- Pattern that causes silent bugs: annotated `float` but caller passes `float | None` → TypeError at runtime

**2. Schema Contract**
- Every SQL query that references a column: verify the column exists in the target table (run `\d tablename` or check migration file)
- Every SQL literal value in WHERE clauses: verify it matches the actual data stored (e.g., DB normalizes `'SLD'` → `'SELL'` on insert)
- Never infer column names from application-level variable names — the DB schema is ground truth

**3. Config Contract**
- Every key added to a config YAML: grep the source code for a matching read (`config.get('key')` or `config['key']`)
- Every config read in code: grep the YAML for the matching key definition
- Dead config (key in YAML, never read) = incomplete implementation, must be wired or removed
- Dead read (code reads key that doesn't exist in YAML) = runtime KeyError, must be added or removed

**Enforcement**: All three contracts are checked in the Verification Loop (Stage 4) and Ralph Review (all 3 tiers).

### Fail Fast, No Silent Fallbacks

**Principle**: Fail loudly at startup. Silent fallbacks hide bugs. Fix root cause. Error indicators must be unmistakable (cannot be confused with valid data).

| FORBIDDEN | Why | USE INSTEAD |
|-----------|-----|-------------|
| `0.0`, `0` | Valid metric values | `None` (internal) → `ER` (display) |
| `N/A` | Looks like "not applicable" | `ER` (clearly an error) |
| `""`, `-`, `--` | Invisible/soft placeholders | `ER` or explicit error message |

**See ANTI-PATTERNS.md #7** for full DO/DON'T list, code examples, detection patterns, and the Issue #269 post-mortem.

### Observability — No Code Without Logs, Metrics, and Audit Trails

**Principle**: Logs, metrics, and audit trails are mandatory at write time. If a system can run silently, it will — and you'll have no signal when it produces the wrong answer.

**Rules** (apply to every component you write):
1. **Log every decision boundary**, state transition, and external call (DB/API/file/subprocess/IPC) with structured fields (key=value or JSON), inputs, duration, and outcome.
2. **Metrics on anything quantifiable**: counters, durations, queue depths, success/failure ratios. Surface them where a human can see.
3. **Audit trail for any state change** affecting production data, money, or user-visible behaviour. Append-only, with actor + timestamp + reason.
4. **Logs must be searchable**: structured fields, consistent naming, no `print()`, no free-text prose.

(Loud failures at boundaries are covered by Fail Fast above. Don't restate them here.)

**See ANTI-PATTERNS.md #12** for the no-observability failure mode and self-healing.

### Monitor, Don't Fire-and-Forget

**Principle**: When you launch a script / command / subprocess / deployment / test run / commit / push / background process, you own it from launch to completion. "Started" is not "done". Tail the logs, check the exit code, verify the expected output, confirm the side effects landed. The user repeatedly asking "did it work?" is the failure signal.

**Rules**:
1. Every script launch verified end-to-end: tail logs, check exit code, verify output, confirm side effects.
2. Every `run_in_background` command polled via BashOutput at sensible intervals OR notification hook configured. Never fire and walk away.
3. Every test run reported with pass/fail counts, not just "tests ran".
4. Every commit/push/merge verified: commit landed, push succeeded, CI started, CI finished.
5. Every deployment includes post-deploy health checks before declaring done.
6. Every subagent dispatch followed by reading the output and verifying it did what was asked.
7. Every observability surface (logs, metrics, audit trails) READ when relevant — not just written.

**Test**: if you cannot answer "what happened?" with specifics, you fired and forgot. Go check NOW.

AP #12 builds the observability surfaces; AP #16 enforces reading them.

**See ANTI-PATTERNS.md #16** for the failure mode.

### Not Done Until Working

**Principle**: NOT complete until ALL scope requirements verified WORKING.

| State | Status |
|-------|--------|
| "Mostly works" / "works except X" / "I think it works" / "tests pass but feature broken" | NOT DONE |
| All acceptance criteria verified / scope tested / user can perform expected actions | DONE |

**Self-Healing**: Return to appropriate stage → fix → re-verify → then mark complete.

**Enforcement**: Verification Loop requires explicit "fully working" before proceeding.

### No Hardcoded Settings

**Principle**: All configurable values must be in external config files. Hardcoded values cause inconsistency and block reuse.

**Must Externalize**: numeric thresholds, URLs/paths/credentials, colors, timeouts/retry/limits, feature flags.

**Where Settings Go** (per project's CONFIG_SYSTEM.md):

| Setting Type | Location | Discovery |
|--------------|----------|-----------|
| Environment (dev/prod) | `.env` or env vars | Fail if missing |
| Strategy parameters | Config YAML (Layer 2) | config_loader.py |
| Component metadata | Co-located YAML (Layer 3) | config_loader.py |
| UI theming | CSS variables (Layer 4) | stylesheet |
| Indicator colors | Component YAML | Part of component |

**Allowed Hardcoding** (exceptions):
- \ constants with descriptive names (explicit intent)
- Array indices and loop counters
- Line numbers in error messages
- Test fixtures in \ directory

**Enforcement**:
1. **SST3 workflow**: Pre-commit hook `check-hardcoded-params.py` (BLOCKING)
2. **Pre-commit hook**: \ blocks commit with guidance
3. **Discovery**: Project's \ documents where each type goes

**Error Format** (from pre-commit hook):
**Impact**: Issue #383 identified 309 hardcoded values in frontend code. Pre-commit hook prevents future violations.

### Voice Content Protection (Marker-Driven)

**Principle**: Any prose written in Hoi's voice in any repo (CV, LinkedIn, cover letters, blog posts, profile docs) MUST be wrapped in `<!-- iamhoi -->` ... `<!-- iamhoiend -->` markers so the marker-driven voice guard can scan it. Default = SKIP. Untagged prose is silently unprotected.

**Canonical source of truth**: `../scripts/voice_rules.py` (~80 banned words, banned phrases, KEEP_LIST, cutoff date 2026-04-07). Human companion: `~/DevProjects/job-hunter/cv-linkedin/VOICE_PROFILE.md` Sections 8 + 19. NEVER duplicate the rules — both `check-ai-writing-tells.py` (canonical) and any vendored copy (e.g. `hoiboy-uk/scripts/check-ai-writing-tells.py`) import from `voice_rules.py` only.

**MUST**:
- Wrap every new voice-prose paragraph in `<!-- iamhoi --> ... <!-- iamhoiend -->` before commit.
- For quoted JD content, banned-word examples, or proper-noun usage inside a tagged block, carve out with `<!-- iamhoi-skip --> ... <!-- iamhoi-skipend -->`.
- For whole-file exemption, put `<!-- iamhoi-exempt -->` as the FIRST non-blank line.
- For new banned words: edit `voice_rules.py` AND `VOICE_PROFILE.md` Section 8 in the SAME pass (single-source-edits, AP #9).

**MUST NOT**:
- Sanitise authentic Hoi vocabulary out (passion, journey, deeply, truly, navigate, back to basics, attention to detail — see KEEP_LIST).
- Add banned words anywhere inside iamhoi markers.
- Duplicate rule data outside `voice_rules.py`.
- Mix HTML `<!-- iamhoi -->` and `# iamhoi` syntax in the same file (hard fail).

**Enforcement**: pre-commit hook + CI in dotfiles (`validate.yml` voice-tells job) and hoiboy-uk (`ci.yml` voice-tells step). Drift between canonical and vendored copies enforced via `cmp -s` bash hook.

**Reference**: dotfiles#404, hoiboy-uk#3.

---

### Public Repo Secret Detection

**Principle**: Public repos (`ebay-seller-tool`, `SST3-AI-Harness`, `hoiboy-uk`) must never contain secrets, business identifiers, or private filesystem paths. Repos opt in via `.public-repo` marker file at root.

**What is blocked**: Platform tokens (GitHub PATs, AWS keys, GCP, Stripe, JWT), private key headers (PEM, PGP), generic secret assignments (password/token/credential with non-placeholder values), private paths (`/mnt/c/Users/`, `My Drive/`, `Google Drive/`, `OneDrive/`), per-repo business terms (from `.secret-blocklist`).

**Per-repo config**: `.secret-blocklist` (business terms, one per line) and `.secret-allowlist` (false positive suppressions, `path/file` or `path/file:line` format). Script handles missing files as empty sets.

**Enforcement**: Pre-commit hook `check-public-repo-secrets.py` (BLOCKING, `--staged-only` mode) + CI step (full repo scan, no `continue-on-error`). Vendored to consumer repos with drift-check hooks.

**Evidence**: Issue #410. eBay store username, Google Drive paths, and business strategies leaked in ebay-seller-tool (2026-04-11), required manual scrub + force-push.

---

### No Backwards-Compatibility Hacks

**Principle**: When code is removed or refactored, delete it completely.

**FORBIDDEN**: `_oldVar` aliases, re-exported removed types, `// deprecated` comments, dead code paths, shim layers, feature flags for removed features.

**DO**: Delete unused code completely. Update all call sites. Use git history to recover. Trust tests.

**Enforcement**: Verification Loop catches compatibility hacks.

---

### Fix Everything — No Scope/Language Excuses

**Principle**: Fix ALL problems found. No deferrals, no scope/language excuses.

**DO**: Fix every real bug — Python, Rust, JS, SQL, YAML, shell. Only valid skip: confirmed false positive (document why).
**DON'T**: "not in scope", "pre-existing", priority tiers — if it's real, fix it.

---

### Investigate Before Coding

**Principle**: Investigate → root cause → plan → alignment → THEN code. Use subagents to research; main agent collates and plans.

---

### Before Fixing Any Function — Verify the Live Code Path

**Principle**: A fix applied to a function nobody calls is not a fix. Prove the function is on the live code path before editing it.

**Rules**:
1. `grep -rn 'foo' src/ scripts/ tests/ rust/` (excluding the definition itself). Zero non-test callers → dead. **Delete instead of fix.** Record in commit.
2. If callers exist, confirm at least one is reachable from a production entry point (CLI, route, scheduled task, queue consumer, systemd service).
3. Commit message: `Verified live: <caller path>` or `Verified dead: deleted`.

**Python ↔ Rust parallel implementations**: any change to a Python file under `src/data/adapters/` (or a parallel Rust port in `rust/pb-data-service/src/`) MUST also check the Rust file. Apply equivalent change OR: `Rust equivalent: N/A — <reason>` or `Rust equivalent: <file:line> — <commit hash>`.

**Evidence**: Issue #1416 — three manifestations in one session (silent 23-day crash, bug fixed in dead copy, live Rust path broken 45+ days). All three skipped the grep.

---

### Fix Big Problems First

**Principle**: Fix PRODUCTION/architecture problems before infrastructure issues. A stuck repair loop beats a pytest timeout.

---

### Never Replace — ADD Alongside

**Principle**: When adding config values, NEVER replace existing user-set values. Add new ones alongside. ASK if an existing value seems wrong. (Evidence: scheduler incident — refresh ran 2 hrs late.)

---

### Solo Branch Merge Safety

**Principle**: Before merging any solo branch to main: pull main, diff for concurrent edits, resolve preserving BOTH sets of changes. (Evidence: Issue #1347 — concurrent work overwritten.)

---

### Test Live Operations

**Principle**: After fixing operational infrastructure (services, restarts, systemd), trigger a live end-to-end smoke test. Don't just verify imports. (Evidence: crash-loop undetected because restart never triggered.)

---

### Wiring Verification

**Principle**: After ANY fix/enhance/refactor, verify changed code is wired into existing functions and processes.

**Enforcement**: Verification Loop mandatory check.

---

### E2E Tests Must Reuse Production Code

**Principle**: E2E tests must reuse production code paths (calculators, order gateways, price validation), not build parallel logic. Search production code before writing any test helper.

---

### Exhaustive Line-by-Line Audit

**Principle**: Audits are line-by-line per directory using separate subagents, NOT grep pattern skims. Each subagent gets a focused area. Covers: scope review, wiring check, inefficiency scan, memory leaks, STANDARDS.md compliance.

**Evidence**: OHLCV audit first pass (grep skim) missed 40-60% of issues. Line-by-line with separate subagents per directory catches everything.

---

### SST3 is Enforcement, Not Honor System

**Principle**: 5-stage workflow and verification checkpoints are mandatory, not suggestions. Follow in order.

**Enforcement Mechanisms**:
- **Stage 1 Research Gate**: Must complete before writing Issue body
- **Stage 3 Triple-Check Gate**: Must complete before Solo Assignment
- **Verification Loop**: Repeat until ALL pass (overengineering, reuse, duplication, fallbacks, wiring, regression, quality)
- **Ralph Review**: Haiku → Sonnet → Opus — all 3 must pass before merge
- **user-review-checklist.md**: ALL sections mandatory
- **Pre-commit hooks**: Block on size limits, propagation, hardcoded params, debug code

**DON'T**: Skip stages for "simple" changes. Mark checkboxes without evidence. Use honor system.

**Flow**: Research Gate ✓ → Issue written → Triple-Check Gate ✓ → Implement → Verification Loop ✓ → Ralph Review ✓ → Merge → user-review-checklist ✓ → Close

### Minimal Comments

**Write AI-readable code**:
- Use clear, descriptive names (functions, variables, classes)
- Keep functions small and focused
- Self-documenting code saves tokens in context window
- **WHAT comments are forbidden** - use descriptive names instead
- Comment WHY (business logic, gotchas), not WHAT (code already shows this)
- Only comment non-obvious decisions

Comment WHY for non-obvious business logic (e.g., `time.sleep(2)` for IBKR rate-limit). Never comment WHAT.

### Plan Mode by Default

**Principle**: Default state is plan-only. No file ops, no subagents, no commands until execution trigger.

**Execution triggers**: "work on #X", "implement", "autonomously".

**Immediate execution** (ALL must be true): <5 min, <10 lines, zero external deps, reversible, user explicitly requested.

**Enforcement**: Ambiguous requests → stay in Plan Mode, ask for clarification.

## Tool Standardization

| Category | Python | JavaScript/TypeScript |
|----------|--------|----------------------|
| Package manager | `uv` | `npm` or `pnpm` |
| Linter/formatter | `ruff` | `eslint` + `prettier` |
| Testing | `pytest` | `jest` or `vitest` |

Document tool choices in CLAUDE.md.

See: `../workflow/WORKFLOW.md` (Stage 1 — Research) for library research process.

## MCP Tool Schema Loading (Deferred Tools + ToolSearch)

**What it is**: The Claude Code harness may defer MCP tool schemas — tools appear as NAMES ONLY in the agent's active tools (no parameter schema). Calling a deferred tool directly returns `InputValidationError`. Detection: the `ToolSearch` tool is listed in the agent's available tools, and MCP tool names appear in a `<system-reminder>` block labelled "deferred tools".

**Rule (generic — applies to ANY deferred MCP tool, not just github-checkbox)**: Before invoking any MCP tool whose schema is not present in the session-start tool list, call `ToolSearch` with `select:<tool_name>[,<tool_name>...]` to load the schema. Only after the schema is loaded may the tool be invoked. This applies to `mcp__github-checkbox__*`, project-local MCPs registered in `.sst3-local/.claude.json`, and any future MCP servers added to `~/.claude.json`.

**Pattern — github-checkbox** (canonical six-tool load):

```
ToolSearch(query="select:mcp__github-checkbox__update_issue_checkbox,mcp__github-checkbox__get_issue_checkboxes,mcp__github-checkbox__health_check,mcp__github-checkbox__get_issue_events,mcp__github-checkbox__list_issue_comments,mcp__github-checkbox__update_issue_comment")

# then:
mcp__github-checkbox__update_issue_checkbox(
    issue_number=N,
    checkbox_text="...",
    evidence="..."
)
```

**Pattern — generic** (any deferred MCP tool):

```
ToolSearch(query="select:mcp__<server>__<tool>")
# then call the tool as documented by the MCP server
```

**Fail modes**:
- **InputValidationError on direct call** (schema not loaded) → invoke `ToolSearch` first, then retry the call. This is the canonical path; not a failure, just an unloaded schema.
- **ToolSearch returns no match** → retry ONCE with short backoff (transient harness issue). On second no-match, STOP and surface the error. Do NOT fall back to comment-only progress — that is AP #20.
- **ToolSearch succeeds but tool still errors** → normal tool-error handling; fix the call, do not silently skip.

**Canonical scope boundary**: this section is THE canonical source for the ToolSearch / deferred-tool rule. `../reference/tool-selection-guide.md` "Example 2: Stage 4 Checkbox Update" is THE canonical source for per-deliverable evidence-quality patterns. The two are separate concerns — do not duplicate content between them; cross-link by section header only.

**Canonical invocation points**: `../dotfiles/.claude/commands/Leader.md` Guardrails block + `../dotfiles/.claude/commands/SST3-solo.md` Governance Enforcement section reference this rule. `../ralph/{haiku,sonnet,opus}-review.md` enforce it at review time.

## Governance Evidence Signal (Canonical)

Canonical audit signal for verifying that `mcp__github-checkbox__update_issue_checkbox` was actually invoked (AP #20 compliance) is the **`## Proof of Work` section in the issue body** — NOT the GitHub timeline `edited` event log.

**Why the body section, not the timeline**: GitHub's timeline API (`mcp__github-checkbox__get_issue_events`) does not emit `edited` events for an issue author's own body edits on their own issue — a documented API behavior. Since solo-workflow agents ARE the issue author in ~99% of cases, PATCH-event-based audit false-negatives every honored invocation. The body content itself, however, is always externally readable via `mcp__github__get_issue` or `mcp__github-checkbox__get_issue_checkboxes`, regardless of who authored the edit.

**Structure of the signal**: `../dotfiles/mcp-servers/github-checkbox/server.py` function `append_to_proof_of_work` (lines 214-261, invoked at :322) appends a structured entry per invocation to the body's `## Proof of Work` section. Each entry contains the checkbox text + evidence string supplied at call time. The body PATCH that toggles `[ ]` → `[x]` is the SAME PATCH that appends the entry, so presence in Proof of Work strictly implies the tool was called.

**Verification procedure** (for Ralph tiers and any external auditor):
1. Fetch issue body via `mcp__github__get_issue` (or `mcp__github-checkbox__get_issue_checkboxes` for live-state cross-check).
2. Parse the `## Proof of Work` section. Each entry starts with `- **<checkbox text>**: <evidence>`.
3. For every `[x]` box in the body, there MUST be a matching entry in Proof of Work. Missing entry = AP #20 violation (comment-only / narrative-only progress).
4. For each entry, verify the cited evidence:
   - `file:line` claims → `mcp__github__get_file_contents` or local Read on the solo branch
   - commit hashes → `mcp__github__list_commits` / `git show <hash>` / GitHub `/commits/<sha>` endpoint
   - subagent RESULT blocks → comment-id referenced in entry, fetched via `list_issue_comments`
   - command output → reproducible via the same command, or cited via tee log path

**Tier-A cadence verification (opus-review.md Governance Drift Audit)**: ordering of Proof of Work entries is authoritative — the section appends in invocation order. Cross-reference the entry order against the branch's `git log --oneline` to confirm Tier A items closed within the same phase's commit window. Do NOT use `get_issue_events` timestamps for this — self-edit suppression breaks it.

**What this signal does NOT provide**:
- Authenticity of evidence text (a dishonest agent could write false file:line claims). Secondary verification via `get_file_contents` / `list_commits` is required for that — see verification procedure step 4.
- Tamper-detection (issue authors can edit the body to remove Proof of Work entries — use `git log` commit trail as immutable secondary audit).

**Canonical scope boundary**: this section is THE canonical source for which signal Ralph / external audits use. `../ralph/{haiku,sonnet,opus}-review.md` reference this section and do NOT duplicate the procedure. `../reference/tool-selection-guide.md` Example 2 remains canonical for per-deliverable evidence-quality patterns (what to write INTO the Proof of Work entry). This section is canonical for what to DO WITH Proof of Work entries at audit time.

## Per-Stage Feedback Capture (Canonical)

Canonical telemetry mechanism for the SST3 5-stage `/Leader` workflow. Each `/Leader` stage close writes a 10-field feedback record so we accumulate observed patterns across runs (which stage routinely catches what bug class, which subagent angles are wasted, which corrections came from the user vs the agent self-caught).

**Storage convention** (literal path lives in unmirrored CLAUDE.md only): one `feedback-<repo>-<issue>.md` per issue under the `SST3-metrics/leader-feedback/` runtime telemetry directory. Filename encodes repo to prevent cross-repo collision (e.g. `dotfiles#449` vs `auto_pb_swing_trader#449`). Pre-commit hook `sst3-metrics-feedback-present` validates filename regex `^feedback-([a-z][a-z0-9_]*(?:-[a-z0-9_]+)*)-([1-9]\d*)\.md$` AND filename↔frontmatter parity. The repo-segment grammar disallows trailing hyphens, double hyphens, and digit-prefix names; the issue segment is a positive int with no leading zeros (rejects `0`, `007`, `00` collisions). All 5 stages append `## Stage <N>` blocks to the same file. Index NDJSON co-located in the same directory.

**Stage discovery**: parser reads `### Stage <N> — <name>` headings from `../workflow/WORKFLOW.md` at runtime. NEVER hardcode the stage list. This is the lesson from the archived `archive/retrospective-template.md` (coupled to a stage that got deleted in #428 and silently broke).

**Frontmatter schema** (8 fields):
- `issue` — GitHub issue number (integer)
- `repo` — repository name (encoded in filename via `feedback-<repo>-<issue>.md`; parity-validated against frontmatter at commit time)
- `created` — ISO date of first stage close
- `last_updated` — ISO date of most recent stage close
- `stages_logged` — list of stage numbers logged (e.g. `[1, 2, 3, 4, 5]`)
- `verdict_summary` — one-paragraph headline observation across all logged stages
- `topic_keywords` — list of normalized keywords for `--shape-match` lookup (e.g. `[feedback, telemetry, sst3-metrics]`)
- `reconstructed_stages` — list of stage numbers whose body fields were filled with `[reconstructed-post-compact: ...]` markers (lower-weighted in DRIFT ALERT counts)

**Per-stage body schema (10 fields, hard-cap)**:
- `model` — agent model id used for the stage (e.g. `opus-4-7-1m`)
- `worked` — observations of what the workflow caught / surfaced correctly
- `didnt` — observations of what the workflow missed (FP correctly identified does NOT belong here — see FP-handling rule below)
- `why` — root-cause analysis of the `didnt` items
- `improvement` — concrete next-run change suggestion
- `improvement_status` — enum (see below)
- `evidence` — file:line / commit hash / command output / subagent RESULT comment-id
- `friction` — token cost, wall-clock, restart count, per-Ralph-tier outcomes (Stage 4 sub-structure)
- `rule_self_caught` — agent-self-caught violations of an existing canonical rule
- `rule_user_caught` — user-caught corrections (attribution wording is FINE — see channel-separation rule)

**`caught_by:` enum** (sub-attribute on findings inside `worked` / `didnt`): `wrapper / raw / haiku / sonnet / opus / user / agent-self`. Lets the aggregator answer queries like "how often did raw-only Layer 2 catch what wrapper missed".

**`improvement_status` enum**: `pending / applied / partial / superseded / rejected`. When status moves to `applied` or `partial`, set `applied_in: <issue#>`. Closure loop: future Stage 1 Step 0 picks up `pending` improvements from prior issues + marks them `applied` (or `partial` for multi-bullet improvements) when the next run satisfies them.

**Closure-loop content-match format (#460 Phase 5)**: Stage 1 closure-loop entries MUST quote the first 80 chars of the source improvement field verbatim so Stage 5 can byte-match without ambiguity:

```
<repo>#<issue> stage=<N> [bullet=<i>]: "<first 80 chars verbatim>" → <applied-where>
```

The `[bullet=<i>]` qualifier is REQUIRED for multi-bullet improvement fields (1-indexed), OPTIONAL when the entire improvement is a single bullet. The byte-match rule is: take the first 80 chars of the improvement bullet (after `**improvement**:` or `- ` bullet prefix), strip leading/trailing whitespace, that's the canonical key.

**Multi-bullet partial-application schema**: when only a subset of bullets in a multi-bullet improvement field is applied this run, mark per-bullet rather than per-improvement:

```
**improvement_status**: partial
**applied_in_bullets**: [1, 3]
**carry_forward_bullets**: [2]
**applied_in**: <issue-number>
```

Inline per-bullet markers go AFTER the bullet text using HTML comments — e.g. ``- **template-vs-mirror lane mapping** ...<!-- applied_in: 459 -->``. The aggregator and `check-closure-loop-applied.py` (Phase 6) parse these markers via `feedback_parser.py`; the parser emits `applied_in_bullets` + `carry_forward_bullets` into the NDJSON index for cross-issue reporting.

**Soft-cap guidance**: tiny issues 10-20 lines per stage block / medium 30-60 / large 60-120 / >150 revisit. **Hard cap**: 10 fields exactly. Parser emits stderr WARNING (advisory, exit 0) if a per-stage block exceeds 80 lines. Tiny-issue terminal one-liners permitted (`rule_user_caught: none` / `friction: trivial`).

**FP-handling rule**: a false positive correctly identified counts as `worked`, NOT `didnt`. Filter the FP, document why, that's a successful audit. (Avoids inflating DRIFT ALERT counts with the audit's own correctly-rejected hypotheses.)

**Channel-separation rule** (forward-preference-blocklist, NOT attribution-blocklist): feedback files MUST NOT contain forward-looking memory-channel signals: `prefers / always / from now on / default ON / going forward`. Those phrases belong to auto-memory (the user-voice channel). Attribution words that describe what happened in this run (`Hoi flagged`, `user pointed out`, `Hoi caught`) are FINE — they're the natural vocabulary of `rule_user_caught`. Pre-commit hook enforces.

**DRIFT ALERT spec**: count-based on `(stage, verdict=didnt) >= threshold`. Default threshold 5 (placeholder; calibrate after 10 issues). Configurable via env var `SST3_FEEDBACK_DRIFT_THRESHOLD`. Fires from `leader-feedback-aggregate.sh --summarize` to stderr; AP #21 forbids autonomous Issue creation, so DRIFT ALERTs are advisory signals not actions.

**Single-CONCURRENT-session-per-issue rule** (NOT "single-session"): two parallel `/Leader` runs on the same issue from different chat sessions is OUT OF SCOPE. Sequential sessions (compact + resume) FINE — sentinel auto-releases after 24h staleness so a resumed session can re-acquire.

**Cross-repo support**: every repo's `/Leader` runs write to `dotfiles/SST3-metrics/leader-feedback/`. Repo is encoded in both the filename (`feedback-<repo>-<issue>.md`) and the frontmatter `repo:` field; the filename↔frontmatter parity check enforces consistency. Repo source for new files: `/Leader` workflow fills frontmatter `repo:` at file-creation time (per existing manual-fill convention). The dotfiles pre-commit hook validates parity; it does NOT auto-detect repo because it always runs in dotfiles context regardless of which sister repo's `/Leader` triggered the work.

**Post-compact reconstruction protocol**: if an agent compacted mid-stage and cannot recover original observations, fields use the literal marker `[reconstructed-post-compact: <evidence-source>]` (e.g. `[reconstructed-post-compact: chat-handover.md]`, `[reconstructed-post-compact: phase-3-checkpoint-comment]`). Frontmatter `reconstructed_stages: [N]` flag set. Aggregator weights these lower in DRIFT ALERT counts so reconstructed observations don't dominate signal.

**Stage 4 sub-structure**: Stage 4 `worked` / `didnt` MAY contain per-Ralph-tier sub-bullets (Tier 1 Haiku / Tier 2 Sonnet / Tier 3 Opus). The `friction` field captures `ralph_restarts: <N>` + per-tier outcomes (PASS / FAIL → restart → PASS).

**Activation-sha gate**: `SST3-metrics/leader-feedback/.activation-sha` holds the canonical merge SHA when this mechanism lands on master. The `sst3-metrics-feedback-present` pre-commit hook fires only on solo branches whose first commit descends from `.activation-sha`. Pre-existing branches grandfathered (hook exits 0 with stderr note `pre-activation branch: hook skipped, hand-write feedback retroactively if desired`).

**Stage detection**: pre-commit hook detects which stage a commit belongs to via the `Phase: N` git-trailer in the commit message OR an explicit `--stage N` CLI flag. NO fragile heuristic. NO silent skip. Fail loud if a solo-branch commit on an activated branch has neither.

**Auto-archive**: after 90 days of inactivity, records auto-archive to a `_archive/` subfolder.

**Index**: `feedback-index.ndjson` regenerated post-commit (incremental — mtime-vs-files check; full rebuild via `--rebuild`). Queryable via `../scripts/leader-feedback-aggregate.sh --summarize | --report | --shape-match | --staleness`.

**Enforcement (3 layers)**:
- **Layer A**: pre-commit hook `sst3-metrics-feedback-present` (compact-resilient — survives context loss). Bypass for genuine emergencies: `SKIP=sst3-metrics-feedback-present git commit ...`.
- **Layer B**: persistent sentinel files in the gitignored `.sentinels/` subfolder catch Stages 1+2 (which don't produce commits). Auto-release after 24h staleness so compact-resume cycles can re-acquire.
- **Layer C**: skill-body sign-off line in `../dotfiles/.claude/commands/Leader.md` for each of the 5 stages — the redundant-by-design third layer (AP #20 case proved skill-body alone leaks).

**Hook-failure protocol**: `feedback_parser.py` exits 1 with single-line stderr `feedback_parser: <human-readable error> at <file>:<line>`. NEVER raises stack trace. NEVER prints debug noise. The error must be diagnosable from the single line.

**No retrofill**: pre-existing closed issues are NOT seeded with fabricated feedback records. The first live record under this canonical IS the implementation Issue's own dogfood (#448). Avoids the fabrication-vs-criterion contradiction that killed the original retrofill scope.

**Canonical scope boundary**: this section is THE canonical source for what / how / why feedback records exist. `../dotfiles/.claude/commands/Leader.md` SIGN-OFF lines reference this section for the per-stage write step. `../dotfiles/.claude/commands/SST3-solo.md` references this section at Per-Session Initialization and Verification Loop. `../workflow/WORKFLOW.md` references this section in each stage trailer. `../dotfiles/CLAUDE.md` is the single place where the literal `SST3-metrics/leader-feedback/...` storage path lives — the workflow files are mirrored to public repos and use this section reference only.

### Cross-Repo Cohabitation Protocol (#469 Phase 4 — closes dotfiles#449 stage=5)

When a sister repo's `/Leader` run writes feedback that references both the sister repo's work AND a dotfiles-side artefact change, both repos may end up needing entries in their own canonical paths but only ONE can be merged at a time (due to branch-safety rule "NEVER switch branches"). The 4-step cohabitation protocol:

1. **Active-branch minimal marker**: while on the sister repo's solo branch, write a minimal one-line marker file at `dotfiles/SST3-metrics/leader-feedback/feedback-<sister-repo>-<issue>.md` containing only the FM block + a placeholder `[parked: full block at /tmp/feedback-<sister-repo>-<issue>-stage-N.md awaiting cross-repo apply post-merge]` body. Stages 1-2 placeholders rather than full blocks because the active sister branch can't switch to dotfiles to commit fully.
2. **Sister parked full block**: stage the FULL stage block to `/tmp/feedback-<sister-repo>-<issue>-stage-N.md`. This is the data-of-record until applied.
3. **Sign-off comment with apply commands**: at /Leader 5 sign-off, post the apply commands as a comment on the sister-repo Issue: `cp /tmp/feedback-<sister-repo>-<issue>-stage-N.md $DOTFILES_ROOT/SST3-metrics/leader-feedback/feedback-<sister-repo>-<issue>.md && cd $DOTFILES_ROOT && git add SST3-metrics/leader-feedback/feedback-<sister-repo>-<issue>.md && git commit -m "metrics(feedback): apply parked block from <sister-repo>#<issue> (Phase: 5)"`.
4. **Post-merge sweep enforcement**: `bash dotfiles/scripts/sweep-parked-feedback.sh <issue> [--repo <sister-repo>]` invoked at Stage 5 step 7a.0 (per Leader.md) BLOCKs sign-off if any `/tmp/feedback-<sister-repo>-<issue>*.md` file remains. Operator MUST apply the full block before sign-off proceeds. The completeness-check C15 enforces server-side via the Layer B GitHub Actions workflow.

**TBD-issue staging via `_drafts/` subdir**: pre-issue feedback (work where the GitHub Issue hasn't been assigned yet) goes to `dotfiles/SST3-metrics/leader-feedback/_drafts/feedback-<repo>-<topic>-pre-issue.md`. Aggregator's non-recursive glob `feedback-*.md` excludes `_drafts/` automatically — no parser regex change needed. When the Issue is assigned, `git mv _drafts/feedback-<repo>-<topic>-pre-issue.md feedback-<repo>-<issue>.md` + update FM `issue:` field. Pattern matches Jekyll/Hugo `_drafts/` precedent.

**Aggregator self-validates per-file** (#469 Phase 1 hook-order fix): `leader-feedback-aggregate.sh` calls `validate_record()` per-file BEFORE `--emit-ndjson` parse — single point of enforcement at the aggregator boundary, eliminating the pre-commit hook-order timing window without touching `.pre-commit-config.yaml`. Belt-and-braces with the parser's strict-mode emit-ndjson which validates at the CLI layer too.

### Canonical field-line format vs Banned legacy formats

The parser strictly requires `**field**:` bare bold form. Banned legacy formats (parser rejects since #469 Phase 3 strict mode):

| Form | Status | Example |
|------|--------|---------|
| `**field**: value` | Canonical | `**model**: opus-4-7-1m` |
| `- **field**: value` | Banned (bullet-prefix-bold) | `- **model**: ...` |
| `- field: value` | Banned (bullet-prefix-no-bold) | `- model: ...` |
| `- field: \|<br>    indented value` | Banned (YAML literal block) | (multi-line legacy) |
| `## Field` (H2 section) | Banned (header-as-field) | `## Model` |

Continuation lines for multi-line values: bare bullets at column 0, no leading `- ` prefix on the field line itself. Migration scripts for the banned forms live transient in `/tmp/` for one-shot use; canonical pattern is to enforce via parser strict mode + per-file validate at aggregator boundary, not retroactive correction.

**Codepath-split note** (#469 Phase 3): pre-Phase-3 the parser had two effective code paths — `parse_record()` (lax, used by `--emit-ndjson`) and `validate_record()` (strict, used by default + by aggregator pre-Phase-1). Files with missing FM fields / wrong heading levels / forward-pref trips silently emitted 0 NDJSON lines via the lax path. Post-Phase-3: both paths run validate first; CLI consumers and Python module consumers see identical strictness. This single-validate-then-emit codepath is the cure for the silent-skip class. Coining a new Anti-Pattern from one instance is premature per Pass-1 hostile FP sweep — if the codepath-split pattern recurs in another tool, operator can authorise the AP separately per AP #21 (no autonomous Issue creation).

## Path Portability

**Environment Variables**:
- `DOTFILES_ROOT`: Path to dotfiles repository (default: `$HOME/My Drive/DevProjects/dotfiles`)
- `SST3_TEMP`: Path to temp folder (default: `C:/temp`)

**Usage in scripts**:
```bash
# Use environment variable with fallback
cd "${DOTFILES_ROOT:-"$HOME/My Drive/DevProjects/dotfiles"}"

# OR use relative paths from known location
cd ../dotfiles  # from DevProjects/[repo]
```

**Usage in documentation**:
- Use `$DOTFILES_ROOT` in examples requiring absolute paths
- Use relative paths (e.g., `../dotfiles/SST3/...`) for cross-repo references
- Never hardcode `C:\Users\username` in documentation

## DevProjects Directory Structure

```
DevProjects/              ← Local parent (not a git repo, not on GitHub)
├── dotfiles/             ← SST3 source of truth (git repo)
│   ├── SST3/            ← Workflow documentation
│   └── CLAUDE.md        ← Entry point
├── auto_pb_swing_trader/ ← Git repo (uses SST3)
│   └── CLAUDE.md        → ../dotfiles/SST3/...
├── tradebook_GAS/        ← Git repo (uses SST3)
│   └── CLAUDE.md        → ../dotfiles/SST3/...

C:/temp/                  ← Shared temp folder (outside Google Drive, avoids sync conflicts)
```

**Key Implications**: DevProjects/ is local only. Each repo is independent. SST3 lives in dotfiles/, referenced via `../dotfiles/SST3/`. Temp: `C:/temp/{repo}-{issue}-{description}.ext`.

### Architecture Validation

**CRITICAL: DevProjects/ MUST NOT be a git repository.**

**Validation**: `cd .. && git status` → expected: `fatal: not a git repository`.

**If fails**: `cd .. && mv .git .git.DISABLED.{issue-number}` → remove duplicate files from DevProjects/ root → document → add to pre-commit hooks. See Issue #172.

### DevProjects Cleanliness Enforcement

**Pre-commit hook** `check-devprojects-clean` validates DevProjects/ before every commit:

**Allowed:**
- Known repos: `dotfiles/`, `auto_pb_swing_trader/`, `tradebook_GAS/`
- Shared temp: `temp/`
- New git repos: Any directory containing `.git/`
- Disabled git: `.git.DISABLED.*` pattern

**Blocked:**
- Files at DevProjects/ root
- Folders not matching allowed criteria

**Script:** `../scripts/check-devprojects-clean.py`

**Reference:** Issue #249

## Documentation Requirements

| Document | When Required | Max Size |
|----------|--------------|----------|
| README.md | Always | 80 lines |
| Inline comments | Complex logic only | Minimal |
| GitHub Issues | All decisions | N/A |

### README Standards

**Philosophy**: READMEs follow both [Core Philosophy](#foundational-philosophy) principles:
- **JBGE**: Document only what's essential (4 key questions)
- **LMCE**: Deliver it effectively (80-line limit, clear structure)

**The 4 Questions Every README Must Answer**:
1. **What?** - What does this do? (1-2 sentences)
2. **Get?** - How do I get/install it? (Quick start commands)
3. **Install?** - How do I set it up? (Dependencies and config)
4. **Learn?** - Where can I learn more? (Links to docs)

**Structure**: Use the What/Get/Install/Learn format from `../templates/CLAUDE_TEMPLATE.md` (Project-Specific Configuration section).
```

**Enforcement**: Pre-commit hook rejects README.md files > 80 lines

**Per-Stage Feedback / Telemetry**: see canonical section "Per-Stage Feedback Capture (Canonical)" earlier in this file. The previous `SST3-metrics/retrospectives/` lifecycle (per-Issue retrospective files, quarterly review trigger) was superseded in #448 — `archive/retrospective-template.md` produced zero retrospectives across its lifetime; the new per-stage capture mechanism replaces it with 3-layer enforcement, dynamic stage discovery, and a closure-loop on improvements.

### File Housekeeping

**Delete vs Archive**:
- **Delete**: Temp files, build artifacts, failed experiments with no learnings
- **Archive**: Superseded configs, old docs with context value, deprecated code worth reviewing later

**temp/ Folder**:
- **Location**: `C:/temp/` (cross-repo, shared by all projects)
- **Purpose**: Short-lived working files during active development
- **Naming**: `{repo}-{issue#}-{description}.{ext}` (e.g., `dotfiles-121-api-design.md`)
- **NOT for**: Handovers (use GitHub Issue comments)
- **Cleanup**: Script-based deletion when issue closed OR file age >30 days
- **Script**: `python ../scripts/cleanup-temp.py` (dry-run by default)
- **Script Documentation**: See [scripts/README.md](../scripts/README.md)
- **Enforcement**: Pre-commit hook `no-temp-folder` blocks commits with temp/ paths (see Issue #241)

**Archive**:
- **Location**: `/archive` at repo root
- **Naming**: `filename_ARCHIVED_YYYYMMDD_reason.ext`
- **Example**: `old-config.json` → `/archive/old-config_ARCHIVED_20250108_superseded-by-new-config.json`

**Branch Cleanup** (MANDATORY after merge):
- **When**: Immediately after merge to main
- **Local**: `git branch -d {branch-name}`
- **Remote**: `git push origin --delete {branch-name}`
- **Verify**: `git branch -a` shows no orphaned branches for completed issues
- **Monthly**: `git branch --merged main | grep -v "main" | xargs git branch -d`

**Rollback Cleanup**: See `../reference/self-healing-guide.md` for full rollback procedures. Key: one logical change per commit (enables surgical `git revert`), separate debug commits, document rollback in Issue before restarting.
- **Implementation guidance**: Commit incrementally (per-file) supports this strategy

**Removal Reporting** (Issue #119): When removing content, post a brief summary (`File: section (-X tokens/lines) — Removed: X, Kept: Y`) so user can approve deletions quickly.

## "READ IN FULL" Warning Criteria

Add if: sequential checklists, interdependent instructions, skipping causes failures, order matters.
Skip if: pure reference/lookup, independent sections, spot-check only.

**Format**: `**⚠️ READ IN FULL - DO NOT SKIP SECTIONS ⚠️**` + `**This document contains [type] that must be [action]. Selective [action] causes [consequence].**`

**Cleanup Empty Folders**: After archiving/deleting files, remove empty directories

### Issue #108 Lesson: Why Housekeeping Repetition is Intentional

Housekeeping in 3 places (during work, after merge, STANDARDS.md) is intentional — each is a different execution context. Compressing them caused file sprawl (Issue #108). Prevention > Cure.

## Code Quality

### DO
- [ ] Set up pre-commit hooks (scripts/check-propagation.py, scripts/auto-stage-tracked-folders.py)
- [ ] Write tests for critical paths (85% bug catch rate at Verification Loop)
- [ ] Isolate components with clear interfaces
- [ ] Require PR review before merging
- [ ] Run automated tests in CI/CD

### DON'T
- [ ] Skip tests for "simple" changes
- [ ] Bypass pre-commit hooks (scripts/check-propagation.py, scripts/auto-stage-tracked-folders.py)
- [ ] Mix concerns in single modules
- [ ] Merge without passing tests
- [ ] Ignore linter warnings

## Testing Priority

Test in this order:

1. **Critical Paths** (MUST work)
   - Authentication
   - Payment processing
   - Data persistence

2. **Integration Points**
   - API boundaries
   - External services
   - Component interfaces

3. **Edge Cases**
   - Error handling
   - Boundary conditions

4. **Everything Else**
   - UI polish
   - Nice-to-haves

**Minimum coverage**: 85% for Stage 5 verification

### Workflow Validation Gate (AP #18 — MANDATORY)

Unit + smoke tests are necessary but NOT sufficient for pipeline / backtest / CLI-wiring / cross-module propagation changes. Every such change MUST pass a **real-CLI sample invocation** against real DB before the issue closes.

**Per-shape recipes**: see ANTI-PATTERNS.md AP #18 per-shape sample-invocation table (#447 Phase 7) for the 6 repo shapes (Service, Docs-only, Static-blog, Config-heavy, Infra-as-code, GAS) and their respective sample-invocation patterns. The wrapper-script trigger (#447 Phase 5) is also enumerated there. For non-auto_pb repos, use the per-shape recipe in AP #18 rather than the auto_pb-shaped 8-item-liquid-basket pattern.

Cross-link: the **three-signal contract policy** + **Raw-tool cross-validation REQUIRED moments** + **AI-agent fallback heuristic** above ("Structural Code Queries" section L249+) bound when raw-tool counter-queries become MANDATORY at the wrapper-lane boundary. AP #18 sample invocation and raw-tool cross-validation are complementary gates: AP #18 covers downstream-consumer verification, the raw-tool counter-query covers recall verification. Both fire on wrapper-script changes per Phase 5.

**Applies to (ANY match → gate active):**
- New/modified CLI flags threaded into downstream function signatures
- SL1 / SL2 / backtest / queue-orchestrator / pipeline wiring
- Coverage pre-flights, auto-bootstrap paths, snapshot-suffix / experiment-path logic
- Multi-module function-arg propagation chains (>1 hop from CLI to DB write)
- Any change where a `**kwargs`-accepting mock could silently hide the regression
- **Idempotency re-run paths** (#477 Phase 5 AC 5.2 — Theme 4): for changes claiming idempotency or feature-detect logic (install-path scripts, bootstrap guards, "if X already configured: skip" branches), the sample MUST cover BOTH first-install AND re-run-with-feature-already-present paths. (dotfiles#474 evidence — single-direction sample hides re-run-corruption bug class.)
- **Documentation cross-reference resolution** (#477 Phase 5 AC 5.2 — Theme 4): for infrastructure-shape work (homelab bootstrap, runbook scripts, multi-node setup), Stage 5 swarm MUST include an angle that walks every script-path / URL / file-reference / cross-link in the Issue's docs and confirms each resolves (`ls <path>` / `curl -fsI <url>` / `grep -F <ref> <target>`). (dotfiles#474 evidence — dangling references pass Stage 4 but break next runner.)
- **Every-return-path wiring** (#477 Phase 5 AC 5.2 — Theme 4): for cache-read or guard-helper additions (functions whose job is "check state and return early"), Stage 4 must enumerate every `return` statement in the guarded function via `grep -n "return" <file>` and confirm each return path either emits the new instrumentation/cache-write OR is documented as exempt. (apbst#1451 evidence — missed return-path silently skips the new behaviour on the missed branch.)

**Gate (verification loop item — NOT optional)**:
1. Small liquid basket (8 tickers typical), real CLI, real DB.
2. Verify rows land; downstream consumers (contamination audit, snapshot copy, dashboard display) succeed.
3. Mocks MUST assert explicit kwargs (`call_args.kwargs["window_start"] == expected`). No `**kwargs`-swallowing proof.
4. Stage 5 integration test added for every new cross-module signature or CLI flag.

**Enforcement**: AP #18, Stage 4 Verification Loop, `issue-template.md` PREREQUISITE CHECKPOINT.

### Test-Prod Call Coverage Discipline (Theme 9, #477)

**Distinct from**: AP #18 Workflow Validation Gate (end-to-end pipeline sample) AND the regression-test gate (broader). This discipline targets the specific failure mode where a function compiles, lints, and ships but is never actually exercised by any test — the **call-site seam** between new prod code and tests is missing.

**Three-bullet doctrine** (each bullet is a falsifiable check):

1. **Function call seams**: For every new public function/method added in a phase, name the test file that imports + invokes it. Verification: `grep -rnE 'from <new-module> import|<new-module>\\.<callable>' tests/`. Empty grep on a new public callable = FAIL.
2. **Response-payload field assertions**: For every new field added to an API response / JSON payload / dict structure, name the test that asserts the field's presence + value. Verification: `grep -rnE '<field-name>' tests/`. Field with no assertion = FAIL.
3. **Config-key read coverage**: For every new config key read by code (YAML/env/dict), name the test that exercises the read path. Verification: `grep -rnE '<config-key>' tests/`. Config read with no test = FAIL.

**Why it's distinct from AP #18**: AP #18 verifies the end-to-end pipeline lands rows (downstream-consumer verification). Test-Prod Call Coverage verifies the function-level seam exists at all (a function with no test caller can pass AP #18 if the pipeline never invokes it during the sample run, and pass Workflow Validation Gate if it ships untouched).

**Why it's distinct from regression tests**: regression tests cover existing behavior; this discipline targets NEW prod code added in the current phase. The grep pattern is scoped to the diff, not the full codebase.

**Enforcement**:
- `ralph/sonnet-review.md` Test-Prod Call Coverage section (Tier 2 logic-depth gate).
- `.claude/commands/Leader.md` Stage 4 step 3.5 (per-phase-boundary author sweep before MCP close-out).
- Phase-boundary AP #20 close-out: every Tier A box claiming a new public callable MUST cite the test file in evidence.

**Apply rule**: when phase work introduces a new public callable / response field / config key, the implementer runs the matching grep BEFORE closing the phase via MCP. Empty grep = test seam missing = FAIL the phase boundary; either add the test seam OR document explicit no-test-needed rationale (rare; usually only valid for trivial dataclasses or pure-data exports).

### Marker-Substring Discipline (Theme 2, #477)

**Cross-reference**: full rule lives in `ANTI-PATTERNS.md` AP #24 ("Marker-Substring Changes Without Full Emit-Site Enumeration"). This subsection is the STANDARDS.md anchor — short paragraph + two-stage contract. (Sample-run anchor for #477 Phase 6 AC 6.7 — `STANDARDS.md` edited to exercise the post-commit `sst3-tier-a-auto-tick` hook end-to-end against the live #477 Issue body.)

**Two-stage contract** (all marker substring changes — error-message partition string, counter name, diagnostic flag, feature-gate literal, status-enum value, log-line prefix):

1. **Stage 1 baseline grep enumeration** — before any implementation, run `grep -rn -F '<exact_literal>' src/ tests/ scripts/ --include='*.py'` (or per-language equivalent) over the entire codebase. Record count + per-site triage (emission / fixture / mock / stale) in the Issue body as "Known Emit Sites: (N)".
2. **Stage 4 count-drift verification gate** — at Verification Loop, re-run the same grep. Confirm count matches the Stage 1 baseline. Mismatch = either implementation added emission sites that should have been in scope (expand scope) or removed sites that shouldn't have changed (revert removal). Either way FAIL until reconciled.

**Why it's distinct from AP #18**: AP #18 verifies the end-to-end pipeline lands rows under sample invocation. Marker-Substring Discipline verifies the SCOPE of marker references is enumerated and updated together. The two gates are complementary; both fire when the marker change affects pipeline / CLI args / cross-module propagation.

**Why it's distinct from AP #10**: AP #10 prevents creating a duplicate of something that already exists (search before adding). AP #24 prevents incomplete change of something that already exists (enumerate every reference before modifying).

**Enforcement**: ANTI-PATTERNS.md AP #24 (canonical rule), `.claude/commands/Leader.md` Stage 1 step 2.1 (subagent dispatch), `WORKFLOW.md` Verification Loop (Stage 4 Gate 1 checkbox).

## Modularity Standards

### Single Responsibility
Each file/function does ONE thing well.

### Clear Interfaces
Each function/class: single responsibility, typed parameters, descriptive name. `calculate_price(item: Item, discount: float) -> Decimal` not `process_stuff(data)`.
```

### Component Isolation
- Separate concerns into distinct modules
- Use dependency injection
- Avoid tight coupling
- Follow DRY principle

### Checklist
- [ ] One responsibility per function
- [ ] Clear input/output contracts
- [ ] No circular dependencies
- [ ] Testable in isolation
- [ ] Reusable components

### Finding Reusable Modules

Before creating new code: search with Glob/Grep/Agent(Explore), check `docs/INDEX.md`, `docs/components/`. Extend existing — don't duplicate. If new: add documentation. See WORKFLOW.md Stage 1.

## Git Workflow

### Branch Naming
`solo/issue-{number}-{description}` (Solo workflow — primary)
`type/issue-number-description` (legacy format)

Examples: `solo/issue-399-sst3-deep-cleanup`, `fix/80-auth-bug`, `docs/81-update-readme`

### Commit Format
```
Brief description of change

Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>
```

### PR Checklist
- [ ] Links to issue
- [ ] Clear description
- [ ] Tests pass
- [ ] Code reviewed

### Issue & PR Naming Standards

**Principle**: Titles must be self-contained and discoverable without context. Embedding issue/PR numbers causes confusion (documented in Issues #225, #294).

**DO**:
- Use `[Phase X]` for hierarchical work (e.g., `[Phase 1a] Database Schema`)
- Use `[Stage X]` ONLY for SST3 workflow documentation
- Create self-contained titles (no issue/PR number references)
- Track relationships in body: Issues use "Implements #X", PRs use "Related to #X"
- PRs: Use TYPE prefix (feat, fix, refactor, docs, test, chore)

**DON'T**:
- Embed issue/PR numbers in title (e.g., "[#179]", "(Issue #42)")
- Mix [Stage X] and [Phase X] (they serve different purposes)

### Marker Distinction (CRITICAL)

| Marker | Scope | Example |
|--------|-------|---------|
| `[Stage Xa-z]` | SST3 workflow ONLY | `[Stage 1] Issue Enforcement Validation` |
| `[Phase Xa-z]` | Project hierarchical work | `[Phase 1a] Database Schema Design` |

When you see `[Stage X]`, it's SST3 process work. `[Phase X]` is project feature work. NEVER mix.

**When to Use**: Sequential phases (`[Phase 1a]`, `[Phase 1b]`), sub-phases with letters/numbers. Skip markers for standalone features, simple bugs, single-issue implementations.

**Good**: `[Phase 1a] Database Schema Design`, `feat: Add email validation`, `Fix auth timeout`
**Bad**: ❌ `Sub-issue [#179] Database Schema #180`, ❌ `feat: Add validation (#42)`

**Enforcement**: Triple-Check Gate (Issues) and Verification Loop (PRs) validate naming. New items only; legacy exempt.


### PR Linking Convention

**ALWAYS use**: `Related to #X`
**NEVER use**: `Closes #X`, `Fixes #X`

**Reason**: Issues closed manually after user review, not auto-closed on merge. Prevents premature closure.

**Enforcement**: PR template pre-fills "Related to #". Verification Loop verifies format.

**NEVER force push to main/master**

## Checklist Enhancement Process

**Principle**: Enforcement gaps → add checkboxes to workflow checklists, not explanatory paragraphs. Checkboxes force execution; explanations get skipped.

**Process**: Identify gap → add direct actionable checkbox to appropriate stage → reference STANDARDS.md for detail.
- ✓ `[ ] Verify: Components follow single responsibility (Modularity - STANDARDS.md)`
- ✗ Adding 5 paragraphs explaining modularity to stage file

**Impact**: Issue #248 found 40+ enforcement gaps fixed this way.

## Template Accuracy Principle

**Principle**: Templates must match workflow instructions exactly. Instruction conflicts with template → template is wrong.

**Prevention**: When updating workflow, update templates in the same commit. Triple-Check Gate + Verification Loop verify against templates. Post-Implementation Review flags mismatches.

**Evidence**: Issue #248 — PR template had "Closes #X" in parentheses; workflow requires separate line.

## Enforcement

1. **Automated Tools**: Pre-commit hooks, CI/CD pipeline, code analysis
2. **PR Review**: Checklist verification, test coverage, standards compliance
3. **Templates**: Issue templates, PR templates, project scaffolding

## Quick Reference

**Before Committing**: Run tests, check linting/formatting, update docs
**Before PR**: Link issue, describe changes, confirm tests pass, request review
**Before Merging**: Address feedback, CI/CD green, update issue, no force push to main

## Keep Going Until Done

Do not stop mid-work to ask permission, wait for confirmation, or "check in" when there is no real blocker. With a 1M context window, the run-length is the work, not the session. Stop only when one of these is actually true:

1. **Context at 80%+** of the model window (800K of 1M, 160K of 200K). Warn at 70%, stop at 80%.
2. **Irreversible destructive action** needs explicit user consent (force-push, `rm -rf`, `DROP TABLE`, branch deletion, overwrites of uncommitted work).
3. **Genuinely stuck** after investigation — not as a first-response-to-friction reflex.
4. **Task is complete.**

Phase checkpoints post a comment to the Issue. They do NOT pause work. Post the comment, then immediately start the next phase. Warnings at 70% are informational; keep working until 80%.

The 200K-era pattern of "stop at phase boundary to compact" no longer applies. The 1M window exists to be used. Stopping at 50%, 70%, or 80% REMAINING (i.e. only 20-50% used) is premature stopping — see ANTI-PATTERNS.md AP #17.

**Threshold update (2026-04-15):** previously "80% warn / 90% stop" from the 200K era. Now **70% warn / 80% stop**. 80%+ of 1M (>800K) is where degradation becomes severe; the 10-point earlier warning gives enough runway to wrap up cleanly. User rationale: *"shit gets bad after that, it should warn at 70%"*.

## Related Documentation

- [Workflow Overview](../workflow/WORKFLOW.md) - 5-stage Solo workflow (Research → Issue → Triple-Check → Implement → Review)
- [Self-Healing Guide](../reference/self-healing-guide.md) - Recovery mechanisms and self-healing protocols
- [Anti-Patterns](ANTI-PATTERNS.md) - Common mistakes and how to avoid them

## External Research References

Capture quality research once in `docs/research/` (project root, NOT SST3/). Create when 3+ external resources found.

**Anti-regression clarifier (added 2026-04-24 after drift detected):** research docs — public or private — go in `docs/research/<topic>/` with topic sub-folders. They do NOT go in domain-adjacent paths like `business/<domain>/research/`, `src/<module>/docs/`, or any other out-of-tree location. If a domain has ≥3 research docs, create `docs/research/<domain>/`; if <3, keep at `docs/research/` root with the date-prefix filename. Single source of truth per project, scannable by `ls docs/research/`. Prior 14-doc accumulation in dotfiles was consolidated to a `docs/research/ebay/` topic folder on 2026-04-24, then migrated out of dotfiles entirely into a private sibling repo on 2026-04-27 (dotfiles#449) — eBay business operations no longer share the SST3 harness repo.

See: `../reference/research-reference-guide.md` for complete guide, file structure, naming conventions, and template.
