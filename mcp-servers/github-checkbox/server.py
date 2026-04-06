#!/usr/bin/env python3
"""
GitHub Checkbox MCP Server

Provides MCP tools for updating GitHub Issue checkboxes with evidence enforcement.
Enforces one-checkbox-at-a-time updates with mandatory evidence appended to Proof of Work.
"""

import json
import os
import re
import subprocess
import sys
import time
import traceback
from functools import wraps
from typing import Optional

from mcp.server.fastmcp import FastMCP
from mcp import types

# Default repo - can be overridden by environment variable
DEFAULT_REPO = os.environ.get("GITHUB_CHECKBOX_REPO", "OWNER/REPO")

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2

mcp = FastMCP("github-checkbox")


def log_debug(message: str) -> None:
    """Log to stderr (MCP uses stdout for protocol)."""
    print(f"[github-checkbox] {message}", file=sys.stderr, flush=True)


def with_error_handling(func):
    """Decorator to catch and report all exceptions in tool functions."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            error_details = traceback.format_exc()
            log_debug(f"ERROR in {func.__name__}: {error_details}")
            return f"ERROR: Unexpected error in {func.__name__}: {str(e)}\n\nDetails: {error_details}"
    return wrapper


def run_gh_command(args: list[str], repo: str = None, skip_repo_flag: bool = False, retries: int = MAX_RETRIES) -> tuple[bool, str, str]:
    """
    Run gh CLI command and return success status, stdout, and stderr.

    Args:
        args: Command arguments to pass to gh CLI
        repo: Repository in owner/repo format (None = use default)
        skip_repo_flag: If True, don't add --repo flag (for gh api commands)
        retries: Number of retry attempts for transient failures

    Returns:
        Tuple of (success, stdout, stderr)
    """
    # Add --repo flag unless explicitly skipped (gh api commands don't support it)
    cmd_args = list(args)  # Copy to avoid mutation
    if not skip_repo_flag:
        effective_repo = repo or DEFAULT_REPO
        if effective_repo:
            cmd_args = cmd_args + ["--repo", effective_repo]

    last_error = ""
    for attempt in range(retries):
        try:
            log_debug(f"Running: gh {' '.join(cmd_args[:3])}... (attempt {attempt + 1}/{retries})")
            result = subprocess.run(
                ["gh"] + cmd_args,
                capture_output=True,
                text=True,
                timeout=60,  # Increased from 30s for large issues
                encoding='utf-8',
                errors='replace'
            )

            # Check for rate limiting or transient errors
            if result.returncode != 0:
                stderr_lower = result.stderr.lower()
                # Retry on rate limit or server errors
                if any(err in stderr_lower for err in ["rate limit", "502", "503", "504", "timeout"]):
                    last_error = result.stderr
                    if attempt < retries - 1:
                        log_debug(f"Transient error, retrying in {RETRY_DELAY_SECONDS}s: {result.stderr[:100]}")
                        time.sleep(RETRY_DELAY_SECONDS * (attempt + 1))  # Exponential backoff
                        continue

            return result.returncode == 0, result.stdout, result.stderr

        except FileNotFoundError:
            return False, "", "gh CLI not found. Install from: https://cli.github.com/"
        except subprocess.TimeoutExpired:
            last_error = f"Command timed out after 60 seconds (attempt {attempt + 1})"
            log_debug(last_error)
            if attempt < retries - 1:
                time.sleep(RETRY_DELAY_SECONDS)
                continue
            return False, "", last_error
        except Exception as e:
            last_error = f"Command failed: {str(e)}"
            log_debug(f"Exception: {last_error}")
            if attempt < retries - 1:
                time.sleep(RETRY_DELAY_SECONDS)
                continue
            return False, "", last_error

    return False, "", f"All {retries} attempts failed. Last error: {last_error}"


def get_issue_body(issue_number: int, repo: str = None) -> tuple[bool, str, str]:
    """
    Fetch Issue body from GitHub.

    Args:
        issue_number: GitHub Issue number

    Returns:
        Tuple of (success, body_text, error_message)
    """
    success, stdout, stderr = run_gh_command([
        "issue", "view", str(issue_number), "--json", "body", "--jq", ".body"
    ], repo)

    if not success:
        if "no open issues" in stderr.lower() or "not found" in stderr.lower():
            return False, "", f"Issue #{issue_number} not found"
        return False, "", f"Failed to fetch Issue: {stderr}"

    return True, stdout.strip(), ""


def update_issue_body(issue_number: int, new_body: str, repo: str = None) -> tuple[bool, str]:
    """
    Update Issue body on GitHub.

    Args:
        issue_number: GitHub Issue number
        new_body: New body content

    Returns:
        Tuple of (success, error_message)
    """
    success, stdout, stderr = run_gh_command([
        "issue", "edit", str(issue_number), "--body", new_body
    ], repo)

    if not success:
        return False, f"Failed to update Issue: {stderr}"

    return True, ""


def parse_checkboxes(body: str) -> list[dict]:
    """
    Parse all checkboxes from Issue body.

    Args:
        body: Issue body text

    Returns:
        List of dicts with 'checked' (bool) and 'text' (str) keys
    """
    checkboxes = []

    # Match both checked [x] and unchecked [ ] checkboxes
    pattern = r'^- \[([ x])\] (.+)$'

    for line in body.split('\n'):
        match = re.match(pattern, line.strip())
        if match:
            checked = match.group(1).lower() == 'x'
            text = match.group(2).strip()
            checkboxes.append({
                'checked': checked,
                'text': text
            })

    return checkboxes


def find_checkbox_line(body: str, checkbox_text: str) -> Optional[tuple[str, bool]]:
    """
    Find the exact checkbox line matching the given text.

    Args:
        body: Issue body text
        checkbox_text: Text to match (without [ ] prefix)

    Returns:
        Tuple of (full_line, is_checked) or None if not found
    """
    for line in body.split('\n'):
        line_stripped = line.strip()

        # Check for unchecked checkbox
        unchecked_pattern = r'^- \[ \] ' + re.escape(checkbox_text) + r'$'
        if re.match(unchecked_pattern, line_stripped):
            return line, False

        # Check for checked checkbox
        checked_pattern = r'^- \[x\] ' + re.escape(checkbox_text) + r'$'
        if re.match(checked_pattern, line_stripped, re.IGNORECASE):
            return line, True

    return None


def append_to_proof_of_work(body: str, checkbox_text: str, evidence: str) -> str:
    """
    Append evidence to Proof of Work section, creating it if needed.

    Args:
        body: Current Issue body
        checkbox_text: Checkbox text
        evidence: Evidence text

    Returns:
        Updated body with evidence appended
    """
    proof_header = "## Proof of Work"
    evidence_entry = f"- **{checkbox_text}**: {evidence}"

    # Check if Proof of Work section exists
    if proof_header in body:
        # Find the section and append to it
        lines = body.split('\n')
        proof_index = -1

        for i, line in enumerate(lines):
            if line.strip() == proof_header:
                proof_index = i
                break

        if proof_index >= 0:
            # Find where to insert (after header, but before next ## section)
            insert_index = proof_index + 1

            # Skip empty lines after header
            while insert_index < len(lines) and not lines[insert_index].strip():
                insert_index += 1

            # Find next section header or end of document
            while insert_index < len(lines) and not lines[insert_index].strip().startswith('##'):
                insert_index += 1

            # Insert before next section or at end
            lines.insert(insert_index, evidence_entry)
            return '\n'.join(lines)

    # Proof of Work section doesn't exist, create it at the end
    if not body.endswith('\n'):
        body += '\n'

    body += f"\n{proof_header}\n\n{evidence_entry}\n"
    return body


@mcp.tool()
@with_error_handling
async def update_issue_checkbox(
    issue_number: int,
    checkbox_text: str,
    evidence: str,
    repo: str = None
) -> str:
    """
    Update a single unchecked checkbox to checked and append evidence.

    Enforces one-checkbox-at-a-time updates with mandatory evidence.
    Validates checkbox exists and is unchecked before updating.

    Args:
        issue_number: GitHub Issue number
        checkbox_text: Exact text of the checkbox (without [ ] prefix)
        evidence: Evidence/proof for completing this checkbox (required, non-empty)
        repo: Repository in owner/repo format (optional, defaults to hoiung/dotfiles)

    Returns:
        Success or error message
    """
    log_debug(f"update_issue_checkbox: issue={issue_number}, checkbox='{checkbox_text[:50]}...'")
    # Validate evidence is non-empty
    if not evidence or not evidence.strip():
        return "ERROR: Evidence is required and cannot be empty."

    # Fetch current Issue body
    success, body, error = get_issue_body(issue_number, repo)
    if not success:
        return f"ERROR: {error}"

    # Find the checkbox
    result = find_checkbox_line(body, checkbox_text)

    if result is None:
        # Checkbox not found, list available checkboxes
        checkboxes = parse_checkboxes(body)
        if not checkboxes:
            return f"ERROR: No checkboxes found in Issue #{issue_number}"

        available = "\n".join([
            f"  {'[x]' if cb['checked'] else '[ ]'} {cb['text']}"
            for cb in checkboxes
        ])
        return f"ERROR: Checkbox not found: '{checkbox_text}'\n\nAvailable checkboxes:\n{available}"

    checkbox_line, is_checked = result

    if is_checked:
        return f"ERROR: Checkbox already checked: '{checkbox_text}'"

    # Update checkbox from [ ] to [x]
    new_line = checkbox_line.replace('- [ ]', '- [x]', 1)
    new_body = body.replace(checkbox_line, new_line, 1)

    # Append evidence to Proof of Work section
    new_body = append_to_proof_of_work(new_body, checkbox_text, evidence.strip())

    # Update Issue on GitHub
    success, error = update_issue_body(issue_number, new_body, repo)
    if not success:
        return f"ERROR: {error}"

    return f"SUCCESS: Checkbox '{checkbox_text}' marked as complete in Issue #{issue_number}\nEvidence appended to Proof of Work section."


@mcp.tool()
@with_error_handling
async def get_issue_checkboxes(issue_number: int, repo: str = None) -> str:
    """
    List all checkboxes in an Issue with their state.

    Useful for discovering which checkboxes exist before updating.

    Args:
        issue_number: GitHub Issue number
        repo: Repository in owner/repo format (optional, defaults to hoiung/dotfiles)

    Returns:
        Formatted list of checkboxes with [x] or [ ] state
    """
    log_debug(f"get_issue_checkboxes: issue={issue_number}")
    # Fetch current Issue body
    success, body, error = get_issue_body(issue_number, repo)
    if not success:
        return f"ERROR: {error}"

    # Parse checkboxes
    checkboxes = parse_checkboxes(body)

    if not checkboxes:
        return f"No checkboxes found in Issue #{issue_number}"

    # Format output
    lines = [f"Checkboxes in Issue #{issue_number}:"]
    lines.append("")

    checked_count = sum(1 for cb in checkboxes if cb['checked'])
    unchecked_count = len(checkboxes) - checked_count

    for cb in checkboxes:
        status = "[x]" if cb['checked'] else "[ ]"
        lines.append(f"  {status} {cb['text']}")

    lines.append("")
    lines.append(f"Summary: {checked_count} checked, {unchecked_count} unchecked, {len(checkboxes)} total")

    return "\n".join(lines)


@mcp.tool()
@with_error_handling
async def list_issue_comments(issue_number: int, repo: str = None) -> str:
    """
    List all comments on a GitHub Issue with their IDs.

    Returns comment IDs needed for update_issue_comment.

    Args:
        issue_number: GitHub Issue number
        repo: Repository in owner/repo format (optional, defaults to hoiung/dotfiles)

    Returns:
        JSON list of comments with id, author, created_at, and body preview
    """
    log_debug(f"list_issue_comments: issue={issue_number}")
    effective_repo = repo or DEFAULT_REPO
    success, stdout, stderr = run_gh_command([
        "api", f"repos/{effective_repo}/issues/{issue_number}/comments",
        "--jq", '[.[] | {id: .id, author: .user.login, created_at: .created_at, body: (.body | split("\n")[0] | .[0:100])}]'
    ], skip_repo_flag=True)  # gh api doesn't support --repo flag

    if not success:
        return f"ERROR: Failed to list comments: {stderr}"

    if not stdout.strip() or stdout.strip() == "[]":
        return f"No comments found on Issue #{issue_number}"

    try:
        comments = json.loads(stdout)
        lines = [f"Comments on Issue #{issue_number}:", ""]
        for c in comments:
            preview = c['body'][:80] + "..." if len(c['body']) > 80 else c['body']
            lines.append(f"  ID: {c['id']} | @{c['author']} | {c['created_at']}")
            lines.append(f"      {preview}")
            lines.append("")
        lines.append(f"Total: {len(comments)} comment(s)")
        return "\n".join(lines)
    except json.JSONDecodeError:
        return f"ERROR: Failed to parse response: {stdout}"


@mcp.tool()
@with_error_handling
async def update_issue_comment(comment_id: int, body: str, repo: str = None) -> str:
    """
    Update an existing issue comment by its ID.

    Use list_issue_comments to get comment IDs first.

    Args:
        comment_id: The comment ID (from list_issue_comments)
        body: New body content for the comment
        repo: Repository in owner/repo format (optional, defaults to hoiung/dotfiles)

    Returns:
        Success or error message
    """
    log_debug(f"update_issue_comment: comment_id={comment_id}")
    if not body or not body.strip():
        return "ERROR: Comment body cannot be empty"

    effective_repo = repo or DEFAULT_REPO
    success, stdout, stderr = run_gh_command([
        "api", "-X", "PATCH",
        f"repos/{effective_repo}/issues/comments/{comment_id}",
        "-f", f"body={body}"
    ], skip_repo_flag=True)  # gh api doesn't support --repo flag

    if not success:
        if "404" in stderr or "Not Found" in stderr:
            return f"ERROR: Comment {comment_id} not found in {effective_repo}"
        return f"ERROR: Failed to update comment: {stderr}"

    return f"SUCCESS: Comment {comment_id} updated in {effective_repo}"


@mcp.tool()
@with_error_handling
async def get_issue_events(issue_number: int, repo: str = None) -> str:
    """
    Get events/timeline for a GitHub Issue including edit history.

    Shows edits, label changes, assignments, and other events.

    Args:
        issue_number: GitHub Issue number
        repo: Repository in owner/repo format (optional, defaults to hoiung/dotfiles)

    Returns:
        List of events with type, actor, and timestamp
    """
    log_debug(f"get_issue_events: issue={issue_number}")
    effective_repo = repo or DEFAULT_REPO
    success, stdout, stderr = run_gh_command([
        "api", f"repos/{effective_repo}/issues/{issue_number}/timeline",
        "--jq", '[.[] | select(.event != null) | {event: .event, actor: .actor.login, created_at: .created_at}] | .[0:20]'
    ], skip_repo_flag=True)  # gh api doesn't support --repo flag

    if not success:
        return f"ERROR: Failed to get events: {stderr}"

    if not stdout.strip() or stdout.strip() == "[]":
        return f"No events found for Issue #{issue_number}"

    try:
        events = json.loads(stdout)
        lines = [f"Events for Issue #{issue_number} (latest 20):", ""]
        for e in events:
            actor = e.get('actor') or 'system'
            lines.append(f"  {e['event']} | @{actor} | {e['created_at']}")
        lines.append("")
        lines.append(f"Total shown: {len(events)} event(s)")
        return "\n".join(lines)
    except json.JSONDecodeError:
        return f"ERROR: Failed to parse response: {stdout}"


@mcp.tool()
@with_error_handling
async def health_check() -> str:
    """
    Check if the MCP server and gh CLI are working correctly.

    Returns:
        Status message with gh CLI version and auth status
    """
    log_debug("health_check: running")

    # Check gh CLI exists and version
    success, stdout, stderr = run_gh_command(["--version"], skip_repo_flag=True, retries=1)
    if not success:
        return f"ERROR: gh CLI not available: {stderr}"

    version = stdout.strip().split('\n')[0] if stdout else "unknown"

    # Check auth status
    success, stdout, stderr = run_gh_command(["auth", "status"], skip_repo_flag=True, retries=1)
    if not success:
        return f"ERROR: gh CLI not authenticated: {stderr}"

    auth_info = stdout.strip().split('\n')[0] if stdout else "authenticated"

    return f"OK: {version}\nAuth: {auth_info}\nDefault repo: {DEFAULT_REPO}"


if __name__ == "__main__":
    log_debug("Starting github-checkbox MCP server")
    mcp.run()
