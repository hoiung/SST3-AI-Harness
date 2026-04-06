# GitHub Tool Selection Guide

---
domain: github_tooling
type: guide
topics: [mcp-tools, github-mcp, checkbox-mcp, gh-cli, tool-selection]
use_when: "Choosing between GitHub MCP, Checkbox MCP, and gh CLI for GitHub operations"
last_updated: 2025-01-16
sources:
  - Internal SST3 workflow patterns
  - GitHub MCP server documentation
  - Checkbox MCP server implementation
coverage: comprehensive
---

## Overview

SST3 workflow provides THREE methods for GitHub interactions:

1. **Checkbox MCP**: Progressive checkbox updates with evidence (local Python server)
2. **GitHub MCP**: Issue body editing, sub-issues, comments (configured in `~/.claude.json`)
3. **gh CLI**: Complex queries, dependencies, fallback operations (always available)

This guide provides decision trees for selecting the correct tool.

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

## References

- [Checkbox MCP Server](../../mcp-servers/github-checkbox/README.md)
- [GitHub MCP Documentation](https://github.com/modelcontextprotocol/servers/tree/main/src/github)
- [GitHub Relationships Guide](../reference/github-relationships-guide.md)
- [WORKFLOW.md](../workflow/WORKFLOW.md)
- [WORKFLOW.md Stage 4](../workflow/WORKFLOW.md) (Implementation)
