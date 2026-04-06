#!/usr/bin/env python3
"""Pre-commit hook: Validate DevProjects/ contains only allowed items.

Prevents rogue subagents from creating files/folders directly in DevProjects/.
See Issue #249 for context.
"""

import sys
from pathlib import Path

from sst3_utils import KNOWN_REPOS


# Navigate to DevProjects/ (parent of dotfiles repo)
DEVPROJECTS = Path(__file__).resolve().parents[3]

# Sourced from sst3_utils.KNOWN_REPOS — single source of truth (dotfiles#405).
ALLOWED_REPOS = set(KNOWN_REPOS)

ALLOWED_SPECIAL = {
    "temp",  # Shared temp folder
    "screenshots",  # Chrome DevTools MCP screenshots (see CLAUDE.md)
    ".claude",  # Claude Code project configuration
    "essential_backups",  # User backups folder
}


def is_git_repo(path: Path) -> bool:
    """Check if directory is a git repository."""
    return (path / ".git").exists()


def is_disabled_git(name: str) -> bool:
    """Check if folder is a disabled git artifact."""
    return name.startswith(".git.DISABLED")


def main() -> int:
    """Validate DevProjects/ cleanliness."""
    try:
        if not DEVPROJECTS.exists():
            print(f"ERROR: DevProjects path not found: {DEVPROJECTS}")
            return 1

        violations = []

        for item in DEVPROJECTS.iterdir():
            name = item.name

            # Skip allowed repos
            if name in ALLOWED_REPOS:
                continue

            # Skip allowed special folders
            if name in ALLOWED_SPECIAL:
                continue

            # Skip disabled git folders
            if is_disabled_git(name):
                continue

            # Allow new git repos (must have .git/)
            if item.is_dir() and is_git_repo(item):
                continue

            # Everything else is a violation
            violations.append(item)

        if violations:
            print("=" * 60)
            print("ERROR: Unexpected items in DevProjects/")
            print("=" * 60)
            print()
            print("Violations found:")
            for v in violations:
                item_type = "folder" if v.is_dir() else "file"
                print(f"  - {v.name} ({item_type})")
            print()
            print("=" * 60)
            print("ALLOWED IN DevProjects/:")
            print()
            print(f"   Repos: {', '.join(sorted(ALLOWED_REPOS))}")
            print("   Temp:  temp/")
            print("   New:   Any folder with .git/ inside")
            print("=" * 60)
            print()
            print("To fix:")
            print("  1. Move misplaced folders INTO the correct repo")
            print("  2. Delete stray files (nul, temp files, etc.)")
            print("  3. Re-run: pre-commit run check-devprojects-clean")
            print()
            return 1

        return 0

    except PermissionError as e:
        print(f"ERROR: Permission denied accessing DevProjects/: {e}")
        return 1
    except OSError as e:
        print(f"ERROR: Filesystem error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
