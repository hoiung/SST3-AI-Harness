# GitHub Issue Relationships Guide

---
domain: github_api
type: api
topics: [issue-relationships, dependencies, sub-issues, rest-api, graphql]
use_when: "Creating blocked_by dependencies or parent/child sub-issue relationships in GitHub Issues"
scope: "Dependencies (gh CLI only) vs Sub-issues (GitHub MCP or gh CLI)"
last_updated: 2025-01-16
sources:
  - https://docs.github.com/en/rest/issues/dependencies
  - https://docs.github.com/en/graphql/reference/mutations#addsubissue
coverage: comprehensive
---

## Tool Selection Context

**Dependencies (blocked_by)**: GitHub MCP does NOT support dependencies. Use `gh CLI` with REST API.

**Sub-issues (parent/child)**: GitHub MCP provides `sub_issue_write` tool (preferred). Fallback to `gh CLI` with GraphQL API if MCP unavailable.

**Tool Selection Guide**: See [tool-selection-guide.md](../dotfiles/SST3/reference/tool-selection-guide.md) for complete decision tree.

---

## Overview

GitHub supports two types of issue relationships:

1. **Dependencies** (blocked_by) - REST API with issue ID (integer)
2. **Sub-issues** (parent/child) - GraphQL API with node ID (string)

**Critical Distinction**: Dependencies use numeric issue IDs, sub-issues use string node IDs. Using the wrong ID type causes API failures.

## Section 1: Dependencies API (REST)

### 1.1. Get Issue ID (Integer)

Dependencies require the **numeric issue ID** (NOT the issue number):

```bash
# Get issue ID for issue NUMBER
ISSUE_ID=$(gh api repos/OWNER/REPO/issues/NUMBER --jq '.id')

# Example
gh api repos/hoiung/dotfiles/issues/328 --jq '.id'
# Output: 2876543210 (this is the issue ID)
```

**Why**: GitHub's REST API uses internal issue IDs, not the visible issue numbers.

### 1.2. Add blocked_by Dependency

Create dependency: "Issue A is blocked by Issue B"

```bash
# Pattern
gh api repos/OWNER/REPO/issues/BLOCKED_ISSUE/dependencies/blocked_by \
  -X POST \
  -F issue_id=BLOCKING_ISSUE_ID

# Example: Issue #330 blocked by Issue #328
BLOCKING_ID=$(gh api repos/hoiung/dotfiles/issues/328 --jq '.id')
gh api repos/hoiung/dotfiles/issues/330/dependencies/blocked_by \
  -X POST \
  -F issue_id=$BLOCKING_ID
```

**Result**: Issue #330 sidebar shows "Blocked by #328"

### 1.3. List Dependencies

View all dependencies for an issue:

```bash
# Pattern
gh api repos/OWNER/REPO/issues/NUMBER/dependencies/blocked_by

# Example
gh api repos/hoiung/dotfiles/issues/330/dependencies/blocked_by
```

**Output**: JSON array of blocking issues

### 1.4. Remove Dependency

Delete specific dependency relationship:

```bash
# Pattern
gh api repos/OWNER/REPO/issues/NUMBER/dependencies/blocked_by/DEPENDENCY_ID \
  -X DELETE

# Example
gh api repos/hoiung/dotfiles/issues/330/dependencies/blocked_by/2876543210 \
  -X DELETE
```

**Note**: DEPENDENCY_ID is the issue ID of the blocking issue (from step 1.1)

## Section 2: Sub-issues API (GraphQL)

### 2.1. Get Node ID (String)

Sub-issues require the **GraphQL node ID** (NOT the issue number):

```bash
# Get node ID for issue NUMBER
gh api graphql -f query='
  query {
    repository(owner: "OWNER", name: "REPO") {
      issue(number: NUMBER) {
        id
        title
      }
    }
  }'

# Example
gh api graphql -f query='
  query {
    repository(owner: "hoiung", name: "dotfiles") {
      issue(number: 328) {
        id
        title
      }
    }
  }'
# Output: { "id": "I_kwDOABC123...", "title": "..." }
```

**Why**: GraphQL uses global node IDs (string format starting with "I_kw")

### 2.2. Add Sub-issue

Create parent/child relationship:

```bash
# Pattern
gh api graphql -f query='
  mutation {
    addSubIssue(input: {
      issueId: "PARENT_NODE_ID"
      subIssueId: "CHILD_NODE_ID"
    }) {
      issue {
        number
        title
      }
      subIssue {
        number
        title
      }
    }
  }'

# Example: Make #330 a sub-issue of #328
PARENT_ID=$(gh api graphql -f query='query { repository(owner: "hoiung", name: "dotfiles") { issue(number: 328) { id } } }' --jq '.data.repository.issue.id')
CHILD_ID=$(gh api graphql -f query='query { repository(owner: "hoiung", name: "dotfiles") { issue(number: 330) { id } } }' --jq '.data.repository.issue.id')

gh api graphql -f query="
  mutation {
    addSubIssue(input: {
      issueId: \"$PARENT_ID\"
      subIssueId: \"$CHILD_ID\"
    }) {
      issue { number title }
      subIssue { number title }
    }
  }"
```

**Result**: Issue #330 sidebar shows "Parent: #328"

### 2.3. Check Parent Issue

Query sub-issue's parent:

```bash
# Pattern
gh api graphql -f query='
  query {
    repository(owner: "OWNER", name: "REPO") {
      issue(number: NUMBER) {
        parentIssue {
          number
          title
        }
      }
    }
  }'

# Example
gh api graphql -f query='
  query {
    repository(owner: "hoiung", name: "dotfiles") {
      issue(number: 330) {
        parentIssue {
          number
          title
        }
      }
    }
  }'
```

### 2.3. List Sub-issues of a Parent

```bash
gh api graphql -f query='
  query {
    repository(owner: "OWNER", name: "REPO") {
      issue(number: PARENT_NUMBER) {
        subIssues(first: 50) {
          nodes { number title }
        }
      }
    }
  }'
```

### 2.4. Remove Sub-issue Relationship

```bash
gh api graphql -f query="
  mutation {
    removeSubIssue(input: {
      issueId: \"$PARENT_NODE_ID\"
      subIssueId: \"$CHILD_NODE_ID\"
    }) {
      issue { number }
      subIssue { number }
    }
  }"
```

## Section 3: Common Errors and Troubleshooting

### Error: "404 Not Found" (Dependencies)

**Cause**: Using issue number instead of issue ID

**Fix**: Use `gh api repos/OWNER/REPO/issues/NUMBER --jq '.id'` to get numeric ID

```bash
# Wrong
gh api repos/hoiung/dotfiles/issues/330/dependencies/blocked_by -X POST -F issue_id=328

# Right
BLOCKING_ID=$(gh api repos/hoiung/dotfiles/issues/328 --jq '.id')
gh api repos/hoiung/dotfiles/issues/330/dependencies/blocked_by -X POST -F issue_id=$BLOCKING_ID
```

### Error: "Invalid node ID" (Sub-issues)

**Cause**: Using issue number or numeric ID instead of GraphQL node ID

**Fix**: Use GraphQL query to get node ID (string starting with "I_kw")

```bash
# Wrong
gh api graphql -f query='mutation { addSubIssue(input: { issueId: "328" ... }) }'

# Right
PARENT_ID=$(gh api graphql -f query='query { repository(owner: "hoiung", name: "dotfiles") { issue(number: 328) { id } } }' --jq '.data.repository.issue.id')
gh api graphql -f query="mutation { addSubIssue(input: { issueId: \"$PARENT_ID\" ... }) }"
```

### Error: "Permission denied"

**Cause**: Insufficient repository permissions

**Fix**: Ensure `gh auth login` with repo scope, or use PAT with `repo` permissions

### Verification (Programmatic — preferred over UI)

```bash
# Verify dependency
gh api repos/OWNER/REPO/issues/NUMBER/dependencies/blocked_by

# Verify sub-issue parent
gh api graphql -f query='query { repository(owner: "OWNER", name: "REPO") { issue(number: NUMBER) { parentIssue { number } } } }'
```

Agent-executable. Replaces UI sidebar inspection.

## Quick Reference Table

| Relationship | API Type | ID Type | Get ID Command | Create Command |
|--------------|----------|---------|----------------|----------------|
| Dependencies (blocked_by) | REST | Integer | `gh api repos/OWNER/REPO/issues/NUMBER --jq '.id'` | `gh api repos/OWNER/REPO/issues/BLOCKED/dependencies/blocked_by -X POST -F issue_id=BLOCKING_ID` |
| Sub-issues (parent/child) | GraphQL | String (node ID) | `gh api graphql -f query='query { repository(owner: "OWNER", name: "REPO") { issue(number: NUMBER) { id } } }' --jq '.data.repository.issue.id'` | `gh api graphql -f query='mutation { addSubIssue(input: { issueId: "PARENT_ID" subIssueId: "CHILD_ID" }) { ... } }'` |

## Stage 4 Usage Pattern

When implementing relationships in Stage 3:

1. Check Issue body for "Blocked by: #X" or "Parent: #X" references
2. Determine relationship type (dependency vs sub-issue)
3. Get appropriate ID type (integer for dependencies, node ID for sub-issues)
4. Create relationship using correct API
5. Verify in GitHub UI sidebar

**Example Workflow**:

```bash
# Issue body says: "Blocked by: #328"
# Step 1: Get blocking issue ID
BLOCKING_ID=$(gh api repos/hoiung/dotfiles/issues/328 --jq '.id')

# Step 2: Add dependency to current issue (e.g., #330)
gh api repos/hoiung/dotfiles/issues/330/dependencies/blocked_by \
  -X POST \
  -F issue_id=$BLOCKING_ID

# Step 3: Verify programmatically
gh api repos/hoiung/dotfiles/issues/330/dependencies/blocked_by
```
