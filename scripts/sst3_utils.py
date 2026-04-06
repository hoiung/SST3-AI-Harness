"""SST3 shared utilities. Extracted from duplicate implementations across scripts (#399, #405)."""
import json
import os
import subprocess
import sys
import io
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, List


# Constants (would live in sst3_limits.py for the larger config; kept here
# because they describe internal IO defaults of helpers in this file).
DEFAULT_METRICS_PATH = Path(
    os.environ.get("SST3_METRICS_PATH", str(Path.home() / ".cache" / "sst3" / "sst3-events.jsonl"))
)


def log_event(script: str, event: str, level: str = "info", **fields: Any) -> None:
    """Append a structured event to the SST3 metrics log (#406 F7.1).

    Schema: {ts, script, event, level, fields}.

    Best-effort: failures here are intentionally swallowed because the caller
    is usually a hook running on every commit and a metrics-write failure
    must NOT block the operation. The on-disk JSONL is the audit surface;
    if it cannot be written, the only fallback would be stderr, which would
    pollute pre-commit output. Per AP #12, the helper exists so that adding
    structured logging to a hook is a one-liner.
    """
    try:
        DEFAULT_METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps({
            "ts": datetime.now(timezone.utc).isoformat(),
            "script": script,
            "event": event,
            "level": level,
            "fields": fields,
        }, ensure_ascii=True)
        with DEFAULT_METRICS_PATH.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        # Best-effort writer; never crash the caller. AP #12 cap is the
        # JSONL write itself; absence of an entry is the failure signal.
        pass


# Static list of repositories that consume the SST3 harness.
# Source of truth, imported by:
#   - check-propagation.py
#   - check-devprojects-clean.py
#   - backup-issue-bodies.py
#   - check-issue-assignment-change.py
# Note: propagate-template.py uses dynamic auto-discovery (iterdir on
# DevProjects/) — KNOWN_REPOS is the static fallback for scripts that need
# the canonical list without scanning the filesystem.
KNOWN_REPOS: List[str] = [
    'dotfiles',
    'auto_pb_swing_trader',
    'tradebook_GAS',
    'hoiboy-uk',
]


# Boundary marker between SST3 standard content (above) and project-specific
# content (below) in CLAUDE.md / CLAUDE_TEMPLATE.md.
# Single source of truth (#406 F2.13). Used by:
#   - check-propagation.py
#   - propagate-template.py
BOUNDARY_MARKER = "<!-- ⚠️ DO NOT MODIFY OR DELETE ANYTHING ABOVE THIS LINE ⚠️ -->"


def collect_source_files(
    base_path: Path,
    extensions: Iterable[str],
    ignore_patterns: Iterable[str] = (),
    allowed_files: Iterable[str] = (),
) -> List[Path]:
    """Collect source files matching extensions, applying ignore filters.

    Consolidates the duplicate `for ext in [...]: rglob(f'*{ext}')` + filter
    pattern from check-debug-code.py, check-fallbacks.py, check-hardcoded-params.py,
    check-ai-writing-tells.py, and check-discoverability.py (Phase 7 dedup).

    Args:
        base_path: directory to scan recursively
        extensions: file extensions to match (e.g. ['.py', '.js', '.ts'])
        ignore_patterns: glob/substring patterns passed to should_ignore_path
        allowed_files: explicit allow-list passed to should_ignore_path

    Returns:
        List of Path objects, deduplicated and sorted, matching extensions
        and not filtered out by should_ignore_path.
    """
    base = Path(base_path)
    if not base.exists():
        return []

    files: List[Path] = []
    for ext in extensions:
        files.extend(base.rglob(f'*{ext}'))

    if ignore_patterns or allowed_files:
        files = [
            f for f in files
            if not should_ignore_path(f, ignore_patterns, allowed_files)
        ]

    return sorted(set(files))


def should_ignore_path(
    file_path: Path,
    ignore_patterns: Iterable[str],
    allowed_files: Iterable[str] = (),
) -> bool:
    """Check whether a file path should be skipped by code-scanning hooks.

    Consolidates the duplicated should_ignore() logic from check-debug-code.py,
    check-fallbacks.py, check-hardcoded-params.py, and check-ai-writing-tells.py
    (Phase 7 dedup, dotfiles#405). Each consumer used the same 4-step matching
    pattern: glob-match, path-component match, substring match, then explicit
    allow-list short-circuit.

    Args:
        file_path: file to test
        ignore_patterns: glob/substring patterns to skip
        allowed_files: explicit allow-list (matched first, returns True)

    Returns:
        True if path should be ignored, False otherwise.
    """
    file_str = str(file_path).replace('\\', '/')
    file_parts = file_path.parts

    # Allow-list short-circuit (file is explicitly permitted)
    for pattern in allowed_files:
        if Path(file_str).match(pattern):
            return True

    for pattern in ignore_patterns:
        pattern_norm = pattern.replace('\\', '/')
        if Path(file_str).match(pattern_norm):
            return True
        pattern_clean = pattern_norm.strip('*/').strip('/')
        if pattern_clean and pattern_clean in file_parts:
            return True
        if pattern_clean and '/' + pattern_clean + '/' in '/' + file_str + '/':
            return True

    return False


class SST3UtilError(RuntimeError):
    """Raised by sst3_utils helpers on unrecoverable errors.

    Replaces sys.exit() inside library functions (dotfiles#406 F1.19) so
    callers — including tests — can catch and handle without the process
    dying inside an import or helper call.
    """


def get_staged_files() -> list[str]:
    """Get list of staged files from git. Used by pre-commit hooks.

    Raises SST3UtilError on git failure (dotfiles#406 F1.19).
    CLI callers should catch and translate to sys.exit themselves.
    """
    try:
        result = subprocess.run(
            ['git', 'diff', '--cached', '--name-only'],
            capture_output=True, text=True, check=True
        )
        files = result.stdout.strip().split('\n')
        return [f for f in files if f]
    except subprocess.CalledProcessError as exc:
        raise SST3UtilError(f"git diff --cached failed: {exc}") from exc


def get_repo_root() -> Path:
    """Get the git repository root path.

    Raises SST3UtilError if not in a git repo (dotfiles#406 F1.19).
    """
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--show-toplevel'],
            capture_output=True, text=True, check=True
        )
        return Path(result.stdout.strip())
    except subprocess.CalledProcessError as exc:
        raise SST3UtilError(f"Not in a git repository: {exc}") from exc


def fix_windows_console() -> None:
    """Fix Windows console encoding for UTF-8 output."""
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def fetch_issue_data(issue_number: int, fields: list[str], repo: str | None = None) -> dict | None:
    """Fetch GitHub issue data via gh CLI.

    AP #12 + #406 Phase 9 F1.18: errors logged to stderr AND structured event
    written to sst3-events.jsonl. Returns None on failure (sentinel) — callers
    MUST check for None per the documented contract. Returning None here is
    NOT a silent fallback because the failure is loud (stderr + JSONL event).
    """
    cmd = ['gh', 'issue', 'view', str(issue_number), '--json', ','.join(fields)]
    if repo:
        cmd.extend(['--repo', repo])
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)
        return json.loads(result.stdout)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        log_event(
            "sst3_utils.py",
            "fetch_issue_data_error",
            level="error",
            issue_number=issue_number,
            error_class=type(exc).__name__,
            error_msg=str(exc),
        )
        print(
            f"[ERROR] fetch_issue_data(#{issue_number}) failed: "
            f"{type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return None
    except FileNotFoundError:
        log_event(
            "sst3_utils.py",
            "fetch_issue_data_no_gh",
            level="error",
            issue_number=issue_number,
        )
        print(
            "[ERROR] gh CLI not found. Install GitHub CLI: https://cli.github.com",
            file=sys.stderr,
        )
        return None
