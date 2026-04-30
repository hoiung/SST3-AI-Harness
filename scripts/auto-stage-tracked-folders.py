#!/usr/bin/env python3
"""
Auto-stage files in SST3-metrics, archive, and docs folders.
Ensures these files are always tracked and never left as untracked.
"""

import subprocess
import sys
from pathlib import Path

from sst3_limits import TRACKED_AUTOSTAGE_FOLDERS  # F1.14 single source of truth


def get_untracked_and_modified_files(folders):
    """Get list of untracked and modified files in specified folders.

    Single git invocation per folder (was 2 — untracked + modified).
    """
    all_files = []

    for folder in folders:
        if not Path(folder).exists():
            continue

        try:
            # --others (untracked) + --modified in one call
            result = subprocess.run(
                ["git", "ls-files", "--others", "--modified",
                 "--exclude-standard", folder],
                capture_output=True,
                text=True,
                check=True
            )
            if result.stdout.strip():
                all_files.extend(result.stdout.strip().split('\n'))

        except subprocess.CalledProcessError as e:
            print(
                f"WARNING: git ls-files failed for {folder}: {e}",
                file=sys.stderr,
            )
            continue

    return list(set(all_files))  # Remove duplicates


def auto_stage_folders(folders):
    """Auto-stage files in the specified folders.

    AP #7 (dotfiles#406 F1.13): atomic-or-rollback. If any folder's
    `git add` fails partway through, reset all already-staged folders
    to avoid leaving the index in an inconsistent half-staged state.
    """
    files = get_untracked_and_modified_files(folders)

    if not files:
        return 0

    print("[pre-commit] Auto-staging files:")
    for file in sorted(files):
        print(f"  {file}")

    staged: list[str] = []
    for folder in folders:
        if not Path(folder).exists():
            continue
        try:
            subprocess.run(
                ["git", "add", folder],
                check=True,
                capture_output=True,
            )
            staged.append(folder)
        except subprocess.CalledProcessError as exc:
            print(
                f"[ERROR] auto-stage: failed to stage {folder}: {exc}. "
                f"Rolling back {len(staged)} previously staged folder(s).",
                file=sys.stderr,
            )
            for done in staged:
                subprocess.run(
                    ["git", "reset", "HEAD", "--", done],
                    capture_output=True,
                )
            return 1

    return 0


def main():
    """Main entry point."""
    return auto_stage_folders(TRACKED_AUTOSTAGE_FOLDERS)


if __name__ == "__main__":
    sys.exit(main())
