#!/usr/bin/env python3
"""Pre-commit hook to detect Solo Assignment changes in issue-template.md.

This hook detects when the '## Solo Assignment' section in issue-template.md
has been modified and alerts the main agent to run the rollout process.

BEHAVIOR:
    - Detects changes to Solo Assignment section
    - Outputs clear warning with next steps (does NOT block commit)
    - Always exits 0 (warning only, main agent decides timing)

USAGE:
    Called automatically by pre-commit when issue-template.md is staged.
    Can also be run manually: python SST3/scripts/check-issue-assignment-change.py

Exit codes:
    0: Always (warning only, never blocks)
"""

import subprocess
import sys
from pathlib import Path

from sst3_utils import get_staged_files, fix_windows_console, KNOWN_REPOS, SST3UtilError

fix_windows_console()


TEMPLATE_PATH = 'SST3/templates/issue-template.md'
SOLO_MARKER = '## Solo Assignment (SST3 Automated)'


def extract_assignment_section(content: str) -> str | None:
    """Extract Solo Assignment section from content.

    Args:
        content: File content

    Returns:
        Solo section text, or None if not found
    """
    if SOLO_MARKER not in content:
        return None

    solo_pos = content.find(SOLO_MARKER)
    return content[solo_pos:]


def get_file_content_from_git(file_path: str, ref: str) -> str | None:
    """Get file content from git at specific ref.

    dotfiles#406 F1.17: 'staged' now ALWAYS reads from the index via
    `git show :<path>` rather than falling back to working-tree filesystem
    read. The previous fallback compared HEAD to working tree (not to staged)
    when an unstaged modification existed on top of a staged change, silently
    returning the wrong answer.

    Args:
        file_path: Path to file
        ref: Git ref ('HEAD', 'staged')

    Returns:
        File content, or None if file doesn't exist at ref
    """
    try:
        target = f':{file_path}' if ref == 'staged' else f'{ref}:{file_path}'
        result = subprocess.run(
            ['git', 'show', target],
            capture_output=True,
            text=True,
            encoding='utf-8',
            check=False,
        )
        if result.returncode != 0:
            return None
        return result.stdout
    except subprocess.CalledProcessError:
        return None


def check_assignment_changed() -> bool:
    """Check if Solo Assignment section changed in staged issue-template.md.

    Returns:
        True if Solo Assignment section changed
    """
    try:
        staged_files = get_staged_files()
    except SST3UtilError as exc:
        print(f"[ERROR] check-issue-assignment-change: {exc}", file=sys.stderr)
        sys.exit(1)

    # Check if issue-template.md is staged
    if TEMPLATE_PATH not in staged_files:
        return False

    # F1.17 (#406 Phase 9): read STAGED content from the index, not from the
    # working tree. The previous fallback compared HEAD vs working tree when an
    # unstaged modification existed on top of a staged change, silently
    # returning the wrong answer. The helper get_file_content_from_git was
    # added by the original F1.17 commit but was never wired in — Stage 5 audit
    # caught the unwiring.
    staged_content = get_file_content_from_git(TEMPLATE_PATH, 'staged')
    if staged_content is None:
        return False

    # Get HEAD content
    head_content = get_file_content_from_git(TEMPLATE_PATH, 'HEAD')

    # If file is new (no HEAD version), consider changed
    if head_content is None:
        return True

    # Extract Solo sections from both versions
    staged_solo = extract_assignment_section(staged_content)
    head_solo = extract_assignment_section(head_content)

    return staged_solo != head_solo


def print_warning():
    """Print warning message with next steps."""
    print("\n" + "="*70)
    print("⚠️  ISSUE ASSIGNMENT CHANGED")
    print("="*70)
    print()
    print("The Solo Assignment section in issue-template.md has been modified.")
    print()
    print("NEXT STEPS (MANDATORY):")
    print("1. READ: SST3/templates/issue-assignment-rollout.md")
    print("2. EXECUTE: Follow all checkboxes in the rollout template")
    print("3. VERIFY: All open issues updated before merging related PR")
    print()
    print(f"This rollout affects: {', '.join(KNOWN_REPOS)}")
    print()
    print("="*70)
    print()


def main():
    """Main entry point."""
    if check_assignment_changed():
        print_warning()

    # Always exit 0 (warning only, never blocks)
    sys.exit(0)


if __name__ == '__main__':
    main()
