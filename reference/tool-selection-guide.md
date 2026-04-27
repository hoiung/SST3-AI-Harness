# Tool Selection Guide

---
domain: tool_selection
type: guide
topics: [mcp-tools, github-mcp, checkbox-mcp, gh-cli, wrapper-lane, tool-selection]
use_when: "Choosing between MCP tools, subagents, and CLI tools for GitHub operations OR code-understanding queries"
last_updated: 2026-04-25
sources:
  - Internal SST3 workflow patterns
  - GitHub MCP server documentation
  - Checkbox MCP server implementation
  - SST3 wrapper-lane (Issue #445 — request-scoped bash wrappers, ast-grep + ripgrep + git)
coverage: comprehensive
---

This guide provides decision trees for selecting the correct tool across two domains:

1. **GitHub Operations** (Checkbox MCP / GitHub MCP / `gh` CLI) — edit issues, update checkboxes, query repos.
2. **Code-Understanding Queries** (wrapper-lane bash scripts / subagent exploration / Bash) — callers/callees, blast radius, dead-code, impact.

## Overview

SST3 workflow provides THREE methods for GitHub interactions:

1. **Checkbox MCP**: Progressive checkbox updates with evidence (local Python server)
2. **GitHub MCP**: Issue body editing, sub-issues, comments (configured in `~/.claude.json`)
3. **gh CLI**: Complex queries, dependencies, fallback operations (always available)

---

## Deferred Tools & ToolSearch

MCP tool schemas may be **deferred** by the Claude Code harness — tools appear as names only at session start and must be loaded via `ToolSearch` with `select:<tool_name>` before invocation. See `../dotfiles/SST3/standards/STANDARDS.md` section "**MCP Tool Schema Loading (Deferred Tools + ToolSearch)**" for the canonical rule, generic + github-checkbox load patterns, and fail-mode handling. This is cross-linked, not duplicated — STANDARDS.md is the single source of truth for the rule.

---

## Decision Tree: GitHub Operations

```
OPERATION: What GitHub operation do you need?

├─ UPDATE CHECKBOX (progressive evidence-based updates)
│  └─ USE: Checkbox MCP
│     └─ Tool: mcp__github-checkbox__update_issue_checkbox(issue_number, checkbox_text, evidence)
│     └─ Rationale: Atomic updates, evidence tracking, no race conditions
│     └─ Fallback: Manual checkbox editing (not recommended)
│
├─ EDIT ISSUE BODY (replace full body content)
│  └─ USE: GitHub MCP (preferred) OR gh CLI (fallback)
│     └─ MCP Tool: mcp__github__issue_write(issue_number, body)
│     └─ CLI Fallback: gh issue edit [number] --body "..."
│     └─ Rationale: GitHub MCP simplifies body replacement
│     └─ WARNING: DO NOT use for checkbox updates (use Checkbox MCP instead)
│
├─ CREATE SUB-ISSUE (parent/child relationship)
│  └─ USE: GitHub MCP (preferred) OR gh CLI (fallback)
│     └─ MCP Tool: mcp__github__sub_issue_write(parent_number, child_number, owner, repo)
│     └─ CLI Fallback: gh api graphql (see github-relationships-guide.md Section 2)
│     └─ Rationale: GitHub MCP handles node ID conversion automatically
│
├─ ADD ISSUE COMMENT (post progress updates, checkpoints)
│  └─ USE: GitHub MCP (preferred) OR gh CLI (fallback)
│     └─ MCP Tool: mcp__github__add_issue_comment(issue_number, body)
│     └─ CLI Fallback: gh issue comment [number] --body "..."
│     └─ Rationale: GitHub MCP cleaner syntax, automatic auth
│
├─ SEARCH ISSUES (find related issues, check duplicates)
│  └─ USE: GitHub MCP (preferred) OR gh CLI (fallback)
│     └─ MCP Tool: mcp__github__search_issues(query, owner, repo)
│     └─ CLI Fallback: gh issue list --search "query"
│     └─ Rationale: GitHub MCP provides structured results
│
├─ GET FILE CONTENTS (remote file access without cloning)
│  └─ USE: GitHub MCP (preferred) OR gh CLI (fallback)
│     └─ MCP Tool: mcp__github__get_file_contents(owner, repo, path, ref)
│     └─ CLI Fallback: gh api repos/OWNER/REPO/contents/PATH --jq '.content' | base64 -d
│     └─ Rationale: GitHub MCP decodes base64 automatically
│
├─ CREATE PULL REQUEST (submit changes for review)
│  └─ USE: GitHub MCP (preferred) OR gh CLI (fallback)
│     └─ MCP Tool: mcp__github__create_pull_request(title, body, head, base)
│     └─ CLI Fallback: gh pr create --title "..." --body "..."
│     └─ Rationale: GitHub MCP structured API, better error handling
│
├─ SEARCH CODE (find implementations, patterns)
│  └─ USE: GitHub MCP (preferred) OR gh CLI (fallback)
│     └─ MCP Tool: mcp__github__search_code(query, owner, repo)
│     └─ CLI Fallback: gh search code "query" --repo OWNER/REPO
│     └─ Rationale: GitHub MCP provides structured results with context
│
├─ LIST COMMITS (review change history)
│  └─ USE: GitHub MCP (preferred) OR gh CLI (fallback)
│     └─ MCP Tool: mcp__github__list_commits(owner, repo, sha, path)
│     └─ CLI Fallback: gh api repos/OWNER/REPO/commits
│     └─ Rationale: GitHub MCP provides filtered results
│
└─ CREATE DEPENDENCY (blocked_by relationship)
   └─ USE: gh CLI ONLY (GitHub MCP does NOT support)
      └─ CLI Method: gh api repos/OWNER/REPO/issues/BLOCKED/dependencies/blocked_by -X POST -F issue_id=BLOCKING_ID
      └─ Rationale: GitHub MCP server lacks dependency support
      └─ Reference: github-relationships-guide.md Section 1
```

---

## Tool Comparison Table

| Operation | Checkbox MCP | GitHub MCP | gh CLI | Preferred |
|-----------|--------------|------------|--------|-----------|
| **Update Checkbox** | ✅ Native (evidence-based) | ❌ Not supported | ⚠️ Manual edit | Checkbox MCP |
| **List Checkboxes** | ✅ `get_issue_checkboxes` | ❌ Not supported | ⚠️ Manual parse | Checkbox MCP |
| **List Comments** | ✅ `list_issue_comments` | ❌ Not supported | ✅ `gh api` | Checkbox MCP |
| **Update Comment** | ✅ `update_issue_comment` | ❌ Not supported | ✅ `gh api` | Checkbox MCP |
| **Get Issue Events** | ✅ `get_issue_events` | ❌ Not supported | ✅ `gh api` | Checkbox MCP |
| **Edit Issue Body** | ❌ Not supported | ✅ `issue_write` | ✅ `gh issue edit` | GitHub MCP |
| **Create Sub-Issue** | ❌ Not supported | ✅ `sub_issue_write` | ✅ GraphQL API | GitHub MCP |
| **Add Comment** | ❌ Not supported | ✅ `add_issue_comment` | ✅ `gh issue comment` | GitHub MCP |
| **Search Issues** | ❌ Not supported | ✅ `search_issues` | ✅ `gh issue list --search` | GitHub MCP |
| **Get File Contents** | ❌ Not supported | ✅ `get_file_contents` | ✅ `gh api` + base64 | GitHub MCP |
| **Create PR** | ❌ Not supported | ✅ `create_pull_request` | ✅ `gh pr create` | GitHub MCP |
| **Search Code** | ❌ Not supported | ✅ `search_code` | ✅ `gh search code` | GitHub MCP |
| **List Commits** | ❌ Not supported | ✅ `list_commits` | ✅ `gh api` | GitHub MCP |
| **Create Dependency** | ❌ Not supported | ❌ Not supported | ✅ REST API | gh CLI |

---

## Fallback Strategy

- GitHub MCP unavailable → gh CLI equivalent (then document in Issue comment).
- gh CLI unavailable → curl with `$GITHUB_TOKEN` against `api.github.com`.

---

## Common Mistakes

### Mistake 1: Using GitHub MCP for Checkbox Updates

**Wrong**:
```python
# DO NOT use GitHub MCP to update checkboxes
mcp__github__issue_write(issue_number=364, body=modified_body_with_checkbox)
```

**Why Wrong**: Replaces entire Issue body, loses concurrent updates, no evidence tracking

**Correct**:
```python
# Use Checkbox MCP for checkbox updates
mcp__github-checkbox__update_issue_checkbox(
    issue_number=364,
    checkbox_text="Read STANDARDS.md (entire file)",
    evidence="Reviewed 1069 lines, applied LMCE/JBGE principles"
)
```

### Mistake 2: Using gh CLI for Dependencies When GitHub MCP Available

**Wrong**:
```bash
# GitHub MCP available, but using gh CLI unnecessarily
gh api graphql -f query='mutation { addSubIssue(input: {...}) }'
```

**Why Wrong**: Verbose syntax, manual node ID conversion, more error-prone

**Correct**:
```python
# Use GitHub MCP for sub-issues (simpler)
mcp__github__sub_issue_write(parent_number=364, child_number=365, owner="hoiung", repo="dotfiles")
```

### Mistake 3: Assuming GitHub MCP Supports All Operations

**Wrong**:
```python
# GitHub MCP does NOT support dependencies
mcp__github__create_dependency(blocked_issue=365, blocking_issue=364)  # Tool doesn't exist
```

**Why Wrong**: GitHub MCP server does not include dependency management tools

**Correct**:
```bash
# Use gh CLI for dependencies
BLOCKING_ID=$(gh api repos/hoiung/dotfiles/issues/364 --jq '.id')
gh api repos/hoiung/dotfiles/issues/365/dependencies/blocked_by -X POST -F issue_id=$BLOCKING_ID
```

---

## Tool Selection Checklist

Before choosing a tool, verify:

- [ ] **Operation type**: Checkbox update, body edit, comment, sub-issue, dependency?
- [ ] **Tool availability**: Is GitHub MCP configured in `~/.claude.json`?
- [ ] **Fallback readiness**: Do I have gh CLI available as fallback?
- [ ] **Evidence requirement**: Does operation need evidence tracking? (use Checkbox MCP)
- [ ] **Concurrency risk**: Could other sessions modify same Issue? (use Checkbox MCP for updates)

---

## Integration Points

**WORKFLOW.md**: References this guide for progress posting tool selection (Item: CRITICAL REPORTING)

**issue-template.md**: Lists MCP tools availability with link to this guide

---

## Quick Reference Commands

### Checkbox MCP
```python
mcp__github-checkbox__update_issue_checkbox(issue_number, checkbox_text, evidence)
```

### GitHub MCP (8 tools)
```python
mcp__github__issue_write(issue_number, body)
mcp__github__sub_issue_write(parent_number, child_number, owner, repo)
mcp__github__add_issue_comment(issue_number, body)
mcp__github__search_issues(query, owner, repo)
mcp__github__get_file_contents(owner, repo, path, ref)
mcp__github__create_pull_request(title, body, head, base)
mcp__github__search_code(query, owner, repo)
mcp__github__list_commits(owner, repo, sha, path)
```

### gh CLI (dependencies only)
```bash
# Dependencies (blocked_by)
gh api repos/OWNER/REPO/issues/BLOCKED/dependencies/blocked_by -X POST -F issue_id=BLOCKING_ID

# Sub-issues (fallback if MCP unavailable)
gh api graphql -f query='mutation { addSubIssue(input: {...}) }'
```

---

## Examples from SST3 Workflow

### Example 1: Progress Update Comment

**Scenario**: Phase 2 complete on Issue #364. Post checkpoint with files modified + next steps.

**Tool Selection**: GitHub MCP `add_issue_comment` for narrative; Checkbox MCP `update_issue_checkbox` for per-criterion evidence.

**Code**:
```python
# Narrative checkpoint comment
mcp__github__add_issue_comment(
    issue_number=364,
    owner="hoiung",
    repo="dotfiles",
    body="## Checkpoint: Phase 2 complete\n- Files modified: ...\n- Next steps: Phase 3 ..."
)

# Per-criterion evidence for each Phase 2 acceptance item
mcp__github-checkbox__update_issue_checkbox(
    issue_number=364,
    checkbox_text="Add new STANDARDS.md section 'MCP Tool Schema Loading'",
    evidence="Added section STANDARDS.md:552-601 with deferred-tool rule + ToolSearch pattern"
)
```

### Example 2: Stage 4 Checkbox Update (Evidence Patterns — CANONICAL)

**Scenario**: Acceptance Criteria checkbox "Read STANDARDS.md (entire file)" on Issue #364.

**Tool Selection**: Checkbox MCP (native evidence-based, atomic, no race conditions).

**Code**:
```python
mcp__github-checkbox__update_issue_checkbox(
    issue_number=364,
    checkbox_text="Read STANDARDS.md (entire file)",
    evidence="Reviewed 909 lines, applied LMCE/JBGE + Double-Guardrail principles"
)
```

**Evidence patterns by deliverable type** — CANONICAL table (post-#429, replaces archived `../dotfiles/SST3/archive/ORCHESTRATOR.md:738-763`; all other files reference this location by section name):

| Deliverable Type | Evidence Pattern |
|---|---|
| File created   | `Created [path] with [sections/functions]` |
| File modified  | `Modified [path] lines [X-Y]: [change]` |
| Analysis       | `Analyzed [scope]: Found [key findings]` |
| Test           | `Ran [command]: [results]` |
| Validation     | `Verified [criteria]: [outcome]` |
| Posted update  | `Posted to Issue #X: [URL or description]` |

**When to invoke**:
- ✓ After completing each deliverable
- ✓ After verification passes
- ✓ After file creation/modification documented
- ✗ NOT in bulk at stage end
- ✗ NOT before work is complete

**Deferred-tool bootstrap**: if `mcp__github-checkbox__*` tools are deferred, load schemas first via `ToolSearch(select:mcp__github-checkbox__update_issue_checkbox,...)` per `../dotfiles/SST3/standards/STANDARDS.md` "MCP Tool Schema Loading".

### Example 3: Create Sub-Issue Relationship

**Scenario**: Make Issue #365 a sub-issue of Issue #364

**Tool Selection**:
1. Try GitHub MCP `sub_issue_write` (preferred - no node ID conversion)
2. Fall back to gh CLI GraphQL if MCP unavailable

**Code**:
```python
# MCP Method (preferred)
mcp__github__sub_issue_write(
    parent_number=364,
    child_number=365,
    owner="hoiung",
    repo="dotfiles"
)

# CLI Fallback
PARENT_ID=$(gh api graphql -f query='query { repository(owner: "hoiung", name: "dotfiles") { issue(number: 364) { id } } }' --jq '.data.repository.issue.id')
CHILD_ID=$(gh api graphql -f query='query { repository(owner: "hoiung", name: "dotfiles") { issue(number: 365) { id } } }' --jq '.data.repository.issue.id')
gh api graphql -f query="mutation { addSubIssue(input: { issueId: \"$PARENT_ID\" subIssueId: \"$CHILD_ID\" }) { issue { number } subIssue { number } } }"
```

### Example 4: Create Dependency Relationship

**Scenario**: Issue #365 blocked by Issue #364

**Tool Selection**: gh CLI ONLY (GitHub MCP does NOT support dependencies)

**Code**:
```bash
# Get blocking issue ID (numeric ID, not node ID)
BLOCKING_ID=$(gh api repos/hoiung/dotfiles/issues/364 --jq '.id')

# Add dependency to blocked issue
gh api repos/hoiung/dotfiles/issues/365/dependencies/blocked_by \
  -X POST \
  -F issue_id=$BLOCKING_ID
```

---

## Troubleshooting

### Error: "MCP tool not found"

**Cause**: GitHub MCP server not configured in `~/.claude.json`

**Solution**: Add GitHub MCP server entry (see File 1 in Implementation Plan)

### Error: "Checkbox not found"

**Cause**: Checkbox text doesn't match exactly (case-sensitive, whitespace-sensitive)

**Solution**: Copy exact checkbox text from Issue (without `[ ]` prefix)

### Error: "Permission denied"

**Cause**: gh CLI not authenticated OR insufficient repository permissions

**Solution**: Run `gh auth login` with `repo` scope

### Error: "Invalid node ID" (sub-issues)

**Cause**: Using numeric issue ID instead of GraphQL node ID

**Solution**: Use GitHub MCP `sub_issue_write` (handles conversion) OR get node ID via GraphQL query

---

## Decision Tree: Code-Understanding Queries

> **See also**: `../dotfiles/SST3/reference/lane-selection.md` (#447 Phase 5) for the win-condition heuristic — when to default to wrapper-lane vs drop to raw tools, the 4 cross-validation REQUIRED moments, the 20% recall delta gate, and the empirical validation experiment design pattern.

For structural code questions (callers, callees, imports, inheritance, blast radius, dead code, large functions, test coverage) the SST3 workflow provides **three layered tools**:

1. **Wrapper-lane bash scripts** (Issues #445 + #447) — 38 stateless request-scoped wrappers across 4 phase-groups: Phase A code (20 — status, update, search, callers, callers-transitive, callees, subclasses, impact, large, review, untested-py, secrets, cross-lang, shell, recent-changes, at-ref, config, coverage, orphans, entry-points), Phase A-security (4 — sec-{subprocess, deserialize, secret-touchpoints, input-sources}), Phase A-dep (4 — dep-{list, usage, blast-radius, cve}), Phase B doc (5 — lint, links, yaml, frontmatter, toc), Phase C sync (4 — related-code, tool-eviction, doc-to-code, url-liveness), Phase D (1 — check.sh orchestrator). No daemon, no SQLite, no persistent graph, no embeddings. Inner engines: `ast-grep` (structural patterns) + `ripgrep` (literal search) + `git diff` + `coverage.py` + `jq` + `pip-audit` + `cargo audit` + `npm audit`. Every call re-parses on disk. Supported languages (the five ast-grep is wired for in the wrappers): Python, TypeScript, TSX, JavaScript, Rust. Other languages → subagent fallback.
2. **Subagent exploration** — `Agent(Explore)` for semantic / cross-document / intent / voice / non-code / ambiguous questions. Subagents are NEVER replaced by the wrapper-lane; the wrapper-lane narrows scope for them.
3. **Bash tools** (Grep/Glob/Read) — unsupported-language fallback, direct file reads, text searches.

### 4-Quadrant Boundary Matrix

| Quadrant | Topic | Primary tool | Subagent role |
|---|---|---|---|
| Q1 Wrapper-first | Who calls X? / what does X call? / blast radius of Y / dead functions in Z (all in supported languages) | `bash sst3-code-callers.sh` / `bash sst3-code-callees.sh` / `bash sst3-code-impact.sh` / `bash sst3-code-large.sh` | Spot-check one result; NOT primary |
| Q2 Wrapper + Subagent | Change spans multiple concerns (structure + intent / structure + cross-language) | Wrapper narrows + subagent verifies semantics | Layered — wrapper seeds, subagent validates |
| Q3 Subagent-only | Voice-prose / intent / chat-history / scope-vs-audit / cross-document / non-code file content audits | None — subagent is the primary tool | Sole owner (12 documented moments) |
| Q4 Direct-tool | Exact-file-path lookup / specific function read / single-grep for a known string | Read / Grep / Glob | Skip both — tool is fastest |

### Pre-Query Safety Gate (3 items)

Run BEFORE any wrapper-lane call:

1. Wrapper invocable: `bash dotfiles/SST3/scripts/sst3-code-status.sh` exits 0 and emits valid JSON `{last_updated, file_count, source_languages}`. If exit non-zero (typically exit 127 = inner engine missing), see playbook Install section. The wrapper-lane is stateless — no graph to build, no freshness window.
2. Target language is supported by the wrapper-lane: Python, TypeScript, TSX, JavaScript, Rust (the five ast-grep is wired for in the wrappers). If not (Markdown, YAML, JSON, SQL, TOML, shell, HTML, Jinja, Dockerfile, Go, Java, etc.) → skip wrapper-lane, use subagents.
3. Spot-check discipline: read one wrapper result from source before drawing conclusions. "Never Assume — Always Check" applies. `search` is keyword-only — verify with synonym sweep before any "no match" conclusion.

### Edge-Case Resolutions

| Situation | Resolution |
|---|---|
| Change edits `config.yaml`; a value reads from Python | YAML is unsupported by the wrapper-lane → use Grep + subagent for the config-key-read contract. The wrapper-lane will not catch the link. |
| SQL column rename | SQL is unsupported → grep for column name + subagent. Wrapper-lane won't help. |
| Markdown doc cross-references | Subagent + grep. The wrapper-lane does not parse Markdown. |
| Py ↔ Rust parallel adapters | Wrapper-lane runs per-language per-call; cross-language joins must be done by subagent. Run wrappers on each side separately, then subagent verifies parity. |
| Jinja template → rendered-variable contract | Jinja is unsupported → subagent reads both ends. |
| "No dead functions found" from `bash sst3-code-large.sh` / `bash sst3-code-impact.sh` | Spot-check by reading one result. If zero results AND diff includes unsupported-language files, broaden to subagent. |
| Fresh clone — wrapper-lane install | Run install steps from `docs/guides/code-query-playbook.md` "Wrapper-Script Lane > Install" section (ast-grep via cargo or npm; ripgrep via apt; coverage.py via pipx). Wrapper-lane is stateless — there is no graph to build. |

### Wrapper-Lane Limitations (when NOT to reach for the wrapper-lane)

**Does NOT parse**: Markdown, YAML, JSON, SQL, TOML, shell, HTML, Jinja, Dockerfile, CSS, plain text docs, Go, Java, C#, Ruby, C/C++, Kotlin, Swift, PHP, Solidity (the wrapper-lane covers the 5 languages ast-grep is wired for in the wrappers: Python, TypeScript, TSX, JavaScript, Rust).

**Does NOT answer**: docstring / comment content searches, voice / style / tone analysis, scope-vs-audit alignment, chat-history / opposite-scoping checks, intent / motivation / design-rationale questions, cross-language boundary contracts, cross-document reference integrity, false-positive sweep for confirmed violations, acceptance-criteria prose → code evidence mapping, factual-claims provenance validation.

For any of the above → subagents remain the primary tool (see the 12 subagent-only moments enumerated in STANDARDS.md "Structural Code Queries" and ANTI-PATTERNS.md AP #19).

### Invocation Quick Reference

| Question | Wrapper call |
|---|---|
| Who calls `foo`? | `bash dotfiles/SST3/scripts/sst3-code-callers.sh foo <lang>` |
| What does `foo` call? | `bash dotfiles/SST3/scripts/sst3-code-callees.sh foo <lang>` |
| Blast radius of editing `file.py`? | `bash dotfiles/SST3/scripts/sst3-code-impact.sh <base-branch>` |
| Any function over 200 lines? | `bash dotfiles/SST3/scripts/sst3-code-large.sh 200 <lang>` |
| Find tests covering `foo`? | ⊘ Deferred to semantic-subagent fallback — Phase A wrappers do not expose `tests_for` (Issue #445; no canonical call sites) |
| Review for diff vs default branch? | `bash dotfiles/SST3/scripts/sst3-code-review.sh <base-branch>` (use `main` or `master` per repo) |
| Wrapper-lane status? | `bash dotfiles/SST3/scripts/sst3-code-status.sh` |

See `../../docs/guides/code-query-playbook.md` for full operational playbook (freshness recipe, fallback rules, embeddings policy, cadence governance).

---

## References

- [Checkbox MCP Server](../../mcp-servers/github-checkbox/README.md)
- [GitHub MCP Documentation](https://github.com/modelcontextprotocol/servers/tree/main/src/github)
- [GitHub Relationships Guide](../reference/github-relationships-guide.md)
- [WORKFLOW.md](../workflow/WORKFLOW.md)
- [WORKFLOW.md Stage 4](../workflow/WORKFLOW.md) (Implementation)
- [STANDARDS.md "Structural Code Queries"](../standards/STANDARDS.md)
- [ANTI-PATTERNS.md AP #19](../standards/ANTI-PATTERNS.md)
- [Code-query Playbook (wrapper-lane)](../../docs/guides/code-query-playbook.md)
