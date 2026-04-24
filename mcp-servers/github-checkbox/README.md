# GitHub Checkbox MCP Server

MCP server that enforces one-checkbox-at-a-time GitHub Issue updates with mandatory evidence.

## What

This MCP server provides tools for updating GitHub Issue checkboxes with built-in enforcement of evidence requirements. It prevents batch checkbox updates and ensures every checkbox completion is documented with proof of work.

**Key Features**:
- Single checkbox updates only (no batch operations)
- Mandatory evidence for every checkbox
- Automatic Proof of Work section management
- Fail-fast error handling with clear messages

## Get

```bash
cd mcp-servers/github-checkbox
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
```

## Install

**Prerequisites**:
- Python >=3.10
- [GitHub CLI (`gh`)](https://cli.github.com/) installed and authenticated
- `uv` package manager

**Configuration**:

Add to your `.mcp.json`:

```json
{
  "mcpServers": {
    "github-checkbox": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/sst3-ai-harness/mcp-servers/github-checkbox",
        "run",
        "python",
        "server.py"
      ]
    }
  }
}
```

**Verify Installation**:

```bash
cd mcp-servers/github-checkbox
uv run python server.py
```

Server should start without errors (press Ctrl+C to stop).

## Learn

### Tools

#### `update_issue_checkbox`

Update a single unchecked checkbox to checked and append evidence.

**Parameters**:
- `issue_number` (int): GitHub Issue number
- `checkbox_text` (string): Exact text of checkbox (without `[ ]` prefix)
- `evidence` (string): Evidence/proof for completion (required, non-empty)

**Returns**: Success or error message

**Example**:
```python
update_issue_checkbox(
    issue_number=335,
    checkbox_text="Create server.py with both tools",
    evidence="Created server.py with 250 lines implementing update_issue_checkbox and get_issue_checkboxes"
)
```

#### `get_issue_checkboxes`

List all checkboxes in an Issue with their state.

**Parameters**:
- `issue_number` (int): GitHub Issue number

**Returns**: Formatted list of checkboxes with state indicators

**Example**:
```python
get_issue_checkboxes(issue_number=335)
```

#### `list_issue_comments`

List all comments on an Issue with their IDs (needed for `update_issue_comment`).

**Parameters**:
- `issue_number` (int): GitHub Issue number
- `repo` (string, optional): Repository in owner/repo format

**Returns**: Formatted list of comments with ID, author, timestamp, and body preview

**Example**:
```python
list_issue_comments(issue_number=366)
```

#### `update_issue_comment`

Update an existing issue comment by its ID.

**Parameters**:
- `comment_id` (int): Comment ID (from `list_issue_comments`)
- `body` (string): New comment body content
- `repo` (string, optional): Repository in owner/repo format

**Returns**: Success or error message

**Example**:
```python
update_issue_comment(comment_id=3663546103, body="Updated comment text")
```

#### `get_issue_events`

Get events/timeline for an Issue (labels, assignments, state changes, etc.).

**Parameters**:
- `issue_number` (int): GitHub Issue number
- `repo` (string, optional): Repository in owner/repo format

**Returns**: List of events with type, actor, and timestamp

**Note**: Shows that edits occurred but not the edit content (GitHub API limitation).

**Example**:
```python
get_issue_events(issue_number=366)
```

### Error Handling

The server fails fast with clear error messages:
- `gh` CLI not found → Install instructions
- Issue not found → Issue number validation
- Checkbox not found → List of available checkboxes
- Checkbox already checked → State explanation
- Empty evidence → Evidence requirement
- `gh` CLI failure → stderr output

### Architecture

Uses `gh` CLI via subprocess for all GitHub operations. Checkbox parsing reuses patterns from existing SST2 validation scripts for consistency.
