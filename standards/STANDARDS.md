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
- **Chain**: CLAUDE.md → SST3/workflow/WORKFLOW.md → stage-X → feature (<=4 steps)
- **Validation**: `python SST3/scripts/check-discoverability.py` during Verification Loop
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
8. **Orchestrator MUST embed graph-tool caveats in subagent prompts, not just in the RESULT schema**. When dispatching a subagent that may invoke graph queries, the orchestrator's prompt MUST explicitly name the known caveats: (a) `mcp_graph_available: yes|no` as first RESULT line (AP #19 L435); (b) `keyword_fallback: true` when `embeddings_count=0`; (c) current `last_updated` timestamp; (d) freshness status vs HEAD. The RESULT schema is a receipt check — the prompt-embedded reminders are the primary trigger. Author-time drift (orchestrator writes the rule but forgets to embed it in dispatched prompts) is the documented failure mode (field evidence: 2x corroboration). Consumer-time compliance is validated when orchestrator DOES embed.

**Procedural minimum** for any audit-driven change to a multi-source artefact:
1. Layer 1 swarm (sized to cover every angle of the audit): identify violations
2. Layer 2 swarm (sized to verify every layer-1 finding): false-positive sweep — verify each violation isn't documented architectural design
3. Main agent: read source for every confirmed violation before applying any edit
4. Apply edits with inline proof-method comments where helpful
5. Layer 3 swarm (3-5 subagents): verify applied edits didn't break cross-references or surface new violations

**See ANTI-PATTERNS.md #14** for the no-discipline failure modes.

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

Main agent parses the RESULT block; subagent prose body is informational. Reduces typical 4-8K-token return per subagent to ~500 tokens with zero signal loss because every claim already has provenance per Rule 5 above. **When a subagent discusses graph queries, prepend `mcp_graph_available: yes|no` as the FIRST line** — AP #19 L435 (Ralph Tier 1 uses this to discriminate "no MCP access" from "lazy fallback").

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

### Structural Code Queries — Prefer Graph, Never Alone

For structural code questions (callers, callees, imports, inheritance, blast radius, dead code, large functions, test coverage) in a language the graph supports (Python, TypeScript, TSX, JavaScript, Go, Rust, Java, C#, Ruby, C/C++, Kotlin, Swift, PHP, Solidity), prefer **code-review-graph** MCP queries over subagent exploration — when the pre-query safety gate passes:

1. Graph exists for the target repo (`config status` returns non-null `graph_path` and `total_nodes > 0`). If not, `graph build`.
2. Graph is fresh (`last_updated` within 24 h or since last `git fetch`). If stale, `graph update`.
3. Target file / project language is in the supported list above. If not (Markdown, YAML, JSON, SQL, TOML, shell, HTML, Jinja, Dockerfile, etc.), skip graph; use subagent exploration.
4. If using `search`, check `embeddings_count`. If 0, treat results as keyword substring — NOT semantic similarity.
5. Spot-check one graph result by reading source before drawing conclusions. "Never Assume — Always Check" applies to graph output the same as to memory or subagent summaries.
6. **Data-layer boundary**: if the structural question spans a data-layer boundary (ORM ↔ SQL, HTTP ↔ service, JSONB ↔ Python type, serialisation round-trip, enum ↔ DB literal), graph alone is INSUFFICIENT — graph parses AST, not DB state / schema drift / runtime types. Verify per STANDARDS.md "Contract Verification" + AP #18 real-DB sample invocation. Field evidence: persistent-state write hot-fix (JSONB schema drift between planned-state and realized-state tables) caught only by real-DB invocation.

Graph is **NOT a replacement** for subagents. The following workflow moments remain subagent-only: voice content protection and AI-tell detection; intentional-vs-accidental architecture distinction; Research-Applied-Collectively cross-lens checks; chat-history scope-drift / opposite-scoping checks; false-positive sweep for confirmed violations; scope-vs-audit 100 % alignment; overengineering / out-of-scope detection; design rationale explanation; factual-claims provenance validation; YAML/JSON/SQL/shell/TOML semantic content audits; Markdown voice-prose AI-tells; acceptance-criteria prose → code file:line evidence mapping. See ANTI-PATTERNS.md AP #19.

See also `../reference/tool-selection-guide.md` "Decision Tree: Code-Understanding Queries" and `../docs/guides/code-review-graph-playbook.md`.

### Double-Guardrail Principle

**Principle**: every `/Leader` invocation verifies work against BOTH guardrails — the cross-cutting SST3 canonical (STANDARDS.md + ANTI-PATTERNS.md + WORKFLOW.md + project CLAUDE.md) AND the invoked-skill's domain canonical. Skill-specific rules are NOT suggestions; they are load-bearing canonical, equal in authority to SST3 standards within the skill's domain. Single-guardrail `/Leader` runs on non-SST3-infrastructure work operate with half their guardrails missing.

**Failure mode**: `/Leader 1-6` on a blog / CV / eBay / claude-api task passes every SST3 check but silently violates the skill's domain canonical — banned voice words slip through, Seagate series HARD CONTRACT breached, prompt-caching not wired, claude-api model ID stale. Deliverable looks clean against SST3; fails against skill.

**Invoked-skill canonical by domain** (load-bearing references — see skill definitions for the full rules; this table is a pointer, not a restate):

| Skill | Canonical rules |
|---|---|
| `blog` / `job-hunter` / CV / LinkedIn | `voice_rules.py` banned words + KEEP_LIST; `iamhoi` / `iamhoi-skipend` marker wrapping; `check_voice_tells.py` exit 0 |
| `ebay-seller-tool` | Seagate series HARD CONTRACT; 21-field listing contract; SMART gate; dual-path BOTH directions; never-dispute-customer |
| `claude-api` | Prompt caching wired on every cacheable prompt; model IDs current (no retired models); SDK idioms |
| `SST3-solo` / `Leader` | Cross-cutting SST3 canonical + AP #19 12-moments carve-out + stage-order discipline |
| Project-specific | Paper/live parity; never-touch-production-positions; RTH-only E2E; per-project CLAUDE.md rules |

**Stage-by-stage integration**:

- **Stage 1**: step 0a — identify invoked skill + record `invoked_skill` + `skill_canonical_files` in the research file (alongside graph freshness / CHECK metadata). This is the FIRST LINK of the chain; every downstream stage reads from this.
- **Stage 2**: draft-write time — the issue draft itself MUST NOT violate skill canonical (no voice-banned words in an acceptance criterion for a blog task; no Seagate series mislabel in eBay scope; no retired model IDs in a claude-api task). Main agent is responsible at Stage 2; Stage 3 then verifies via subagent.
- **Stage 3**: one subagent angle verifies the issue draft against invoked-skill canonical (layer 1 scope-compliance; main agent verifies against source).
- **Stage 4**: implementation-write time — every edit must be skill-canonical compliant AT the edit, not only at the verification pass. Same responsibility as Stage 2 for the main agent; Ralph Tier 2/3 verify.
- **Stage 5 Gate 1**: run the skill's own verification hooks (voice guard, eBay 21-field grep + SMART test, prompt-caching verify, project pre-commit hooks). Evidence: pass/fail + output in issue comment.
- **Stage 6**: one subagent angle audits skill-canonical compliance in the delivered work, reading `invoked_skill` + `skill_canonical_files` from Stage 1 research file; same verify-against-source discipline as graph-backed audit.

**Enforcement**: Leader.md Guardrails block (all stages) + Stage 3 subagent angle list + Stage 5 Gate 1 checkbox + Stage 6 appendix. Absence of skill-canonical checking on a non-SST3-infrastructure task = violation.

**Evidence**: field-tested observation (latest round absorption issue) — "Leader 1-6 should incorporate checking against the workflow of the skills that been invoked too, otherwise it just checks SST3 workflow and standard and anti-patterns ... The SST3 should also have this integrated, so it's like a double guardrail." Pre-existing research: `docs/research/LEADER_SKILL_ENGINEERING.md` (AI-to-AI prompt engineering + Stage-4 conflation fix + Ralph tier design).

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

**Canonical source of truth**: `../scripts/voice_rules.py` (~80 banned words, banned phrases, KEEP_LIST, cutoff date 2026-04-07). Human companion: `cv-linkedin/VOICE_PROFILE.md` Sections 8 + 19. NEVER duplicate the rules — both `check-ai-writing-tells.py` (canonical) and any vendored copy (e.g. `hoiboy-uk/scripts/check_voice_tells.py`) import from `voice_rules.py` only.

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

### Public Harness Vendoring Rules

**Principle**: Public repos (`ebay-seller-tool`, `SST3-AI-Harness`, `hoiboy-uk`) must never contain secrets, business identifiers, or private filesystem paths. Repos opt in via `.public-repo` marker file at root.

#### Secret Detection

**What is blocked**: Platform tokens (GitHub PATs, AWS keys, GCP, Stripe, JWT), private key headers (PEM, PGP), generic secret assignments (password/token/credential with non-placeholder values), private paths (`/mnt/c/Users/`, `My Drive/`, `Google Drive/`, `OneDrive/`), per-repo business terms (from `.secret-blocklist`).

**Per-repo config**: `.secret-blocklist` (business terms, one per line) and `.secret-allowlist` (false positive suppressions, `path/file` or `path/file:line` format). Script handles missing files as empty sets.

**Enforcement**: Pre-commit hook `check-public-repo-secrets.py` (BLOCKING, `--staged-only` mode) + CI step (full repo scan, no `continue-on-error`). Vendored to consumer repos with drift-check hooks.

**Evidence**: eBay store username, Google Drive paths, and business strategies leaked in ebay-seller-tool (2026-04-11), required manual scrub + force-push.

#### Command File Path Rewrites (Vendored from private `dotfiles/.claude/commands/`)

Canonical command files live in the private `dotfiles` repo at `.claude/commands/<name>.md` and reference private-SST3 paths (`../dotfiles/SST3/<subdir>/`). When vendored to `SST3-AI-Harness/claude/commands/<name>.md`, rewrite to in-repo paths:

- `../dotfiles/SST3/standards/` → `standards/`
- `../dotfiles/SST3/workflow/` → `workflow/`
- `../dotfiles/SST3/templates/` → `templates/`
- `../dotfiles/SST3/ralph/` → `ralph/`
- `../dotfiles/SST3/scripts/` → `scripts/`
- `../dotfiles/SST3/reference/` → `reference/`

**Verify after each scrub**: grep the vendored file for `../dotfiles/` — must return zero matches. Grep for `hoiung`, `hoi_u`, `auto_pb_swing_trader`, `tradebook_GAS`, `hoiboy`, `ebay-seller` — must return zero matches.

**Drift enforcement** (`cmp -s` with transform applied): deferred until 3+ vendored command files exist. Track as follow-up issue when threshold is crossed.

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
- Use relative paths (e.g., `../...`) for cross-repo references
- Never hardcode `C:\Users\username` in documentation

## DevProjects Directory Structure

```
DevProjects/              ← Local parent (not a git repo, not on GitHub)
├── dotfiles/             ← SST3 source of truth (git repo)
│   ├── SST3/            ← Workflow documentation
│   └── CLAUDE.md        ← Entry point
├── project-a/              ← Git repo (uses SST3)
│   └── CLAUDE.md        → ../...
├── project-b/              ← Git repo (uses SST3)
│   └── CLAUDE.md        → ../...

C:/temp/                  ← Shared temp folder (outside Google Drive, avoids sync conflicts)
```

**Key Implications**: DevProjects/ is local only. Each repo is independent. SST3 lives in dotfiles/, referenced via `../`. Temp: `C:/temp/{repo}-{issue}-{description}.ext`.

### Architecture Validation

**CRITICAL: DevProjects/ MUST NOT be a git repository.**

**Validation**: `cd .. && git status` → expected: `fatal: not a git repository`.

**If fails**: `cd .. && mv .git .git.DISABLED.{issue-number}` → remove duplicate files from DevProjects/ root → document → add to pre-commit hooks. See Issue #172.

### DevProjects Cleanliness Enforcement

**Pre-commit hook** `check-devprojects-clean` validates DevProjects/ before every commit:

**Allowed:**
- Known repos: `dotfiles/`, `<your-project-a>/`, `<your-project-b>/`
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

**Retrospective Lifecycle**:
- **Location**: `SST3-metrics/retrospectives/` (outside SST3 token budget)
- **Retention**: Keep until learnings actioned (30-90 days)
- **Quarterly Review**: 3+ occurrences = create consolidated GitHub issue
- **Archive When**: GitHub Issue closed AND "Ready to Archive: Yes"

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
- **Script**: `python scripts/cleanup-temp.py` (dry-run by default)
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
- [ ] Set up pre-commit hooks (SST3/scripts/check-propagation.py, SST3/scripts/auto-stage-tracked-folders.py)
- [ ] Write tests for critical paths (85% bug catch rate at Verification Loop)
- [ ] Isolate components with clear interfaces
- [ ] Require PR review before merging
- [ ] Run automated tests in CI/CD

### DON'T
- [ ] Skip tests for "simple" changes
- [ ] Bypass pre-commit hooks (SST3/scripts/check-propagation.py, SST3/scripts/auto-stage-tracked-folders.py)
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

Unit + smoke tests are necessary but NOT sufficient for pipeline / data-processing / CLI-wiring / cross-module propagation changes. Every such change MUST pass a **real-CLI sample invocation** against real DB before the issue closes.

**Applies to (ANY match → gate active):**
- New/modified CLI flags threaded into downstream function signatures
- Pipeline / orchestration wiring changes
- Coverage pre-flights, auto-bootstrap paths, window-scoped / experiment-path logic
- Multi-module function-arg propagation chains (>1 hop from CLI to DB write)
- Any change where a `**kwargs`-accepting mock could silently hide the regression

**Gate (verification loop item — NOT optional)**:
1. Small liquid basket (8 items typical), real CLI, real DB.
2. Verify rows land; downstream consumers (audit queries, consumers of the output) succeed.
3. Mocks MUST assert explicit kwargs (`call_args.kwargs["window_start"] == expected`). No `**kwargs`-swallowing proof.
4. Stage 5 integration test added for every new cross-module signature or CLI flag.

**Enforcement**: AP #18, Stage 4 Verification Loop, `issue-template.md` PREREQUISITE CHECKPOINT.

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

**Threshold update (2026-04-15):** previously "80% warn / 90% stop" from the 200K era. Now **70% warn / 80% stop**. 80%+ of 1M (>800K) is where degradation becomes severe; the 10-point earlier warning gives enough runway to wrap up cleanly.

## Related Documentation

- [Workflow Overview](../workflow/WORKFLOW.md) - 5-stage Solo workflow (Research → Issue → Triple-Check → Implement → Review)
- [Self-Healing Guide](../reference/self-healing-guide.md) - Recovery mechanisms and self-healing protocols
- [Anti-Patterns](ANTI-PATTERNS.md) - Common mistakes and how to avoid them

## External Research References

Capture quality research once in `docs/research/` (project root, NOT SST3/). Create when 3+ external resources found.

See: `../reference/research-reference-guide.md` for complete guide, file structure, naming conventions, and template.
