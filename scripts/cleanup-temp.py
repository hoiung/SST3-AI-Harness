#!/usr/bin/env python3
"""
Cleanup script for SST3/temp/ folder.
Deletes files when: (1) linked issue is closed OR (2) file age > 30 days.

Usage:
    python cleanup-temp.py              # Dry run (preview only)
    python cleanup-temp.py --execute    # Actually delete files
    python cleanup-temp.py --age 45     # Custom age threshold (days)
"""

import sys
import re
import subprocess
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, List, Tuple
import argparse


def parse_issue_number(filename: str) -> Optional[int]:
    """
    Extract issue number from filename pattern: {repo}-{issue#}-{description}.{ext}

    Examples:
        "dotfiles-121-api-design.md" -> 121
        "auto_pb_swing_trader-122-test-data.json" -> 122
        "old-file.txt" -> None
    """
    # Updated pattern for repo-issue-description
    match = re.match(r'^([^-]+)-(\d+)-', filename)
    return int(match.group(2)) if match else None


def check_issue_status(issue_number: int) -> Optional[str]:
    """
    Check if GitHub issue is open or closed using gh CLI.

    Returns:
        "open", "closed", or None (if gh CLI fails or issue not found)
    """
    try:
        result = subprocess.run(
            ['gh', 'issue', 'view', str(issue_number), '--json', 'state'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            data = json.loads(result.stdout)
            return data.get('state', '').lower()
        else:
            # Issue not found or gh CLI error
            return None
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        return None


def get_file_age_days(filepath: Path) -> float:
    """Get file age in days based on modification time."""
    mtime = filepath.stat().st_mtime
    file_datetime = datetime.fromtimestamp(mtime, tz=timezone.utc)
    now = datetime.now(timezone.utc)
    age = now - file_datetime
    return age.total_seconds() / 86400


def should_delete(filepath: Path, age_threshold: int) -> Tuple[bool, str]:
    """
    Determine if file should be deleted and provide reason.

    Returns:
        (should_delete: bool, reason: str)
    """
    filename = filepath.name

    # Never delete README.md or other important files
    if filename.lower() in ['readme.md', '.gitkeep', '.gitignore']:
        return False, "Protected file"

    # Check file age
    age_days = get_file_age_days(filepath)

    # Check if filename has issue number
    issue_number = parse_issue_number(filename)

    if issue_number is not None:
        # Check issue status
        issue_status = check_issue_status(issue_number)

        if issue_status == 'closed':
            return True, f"Issue #{issue_number} is closed"
        elif issue_status == 'open':
            if age_days > age_threshold:
                return True, f"Issue #{issue_number} open but file age {age_days:.1f} days > {age_threshold} days"
            else:
                return False, f"Issue #{issue_number} is open and file age {age_days:.1f} days < {age_threshold} days"
        else:
            # Issue not found or gh CLI failed
            if age_days > age_threshold:
                return True, f"Issue #{issue_number} not found and file age {age_days:.1f} days > {age_threshold} days"
            else:
                return False, f"Issue #{issue_number} status unknown, keeping file (age {age_days:.1f} days)"
    else:
        # No issue number in filename, check age only
        if age_days > age_threshold:
            return True, f"No issue number and file age {age_days:.1f} days > {age_threshold} days"
        else:
            return False, f"No issue number but file age {age_days:.1f} days < {age_threshold} days"


def cleanup_temp(temp_path: Path, execute: bool = False, age_threshold: int = 30) -> None:
    """
    Clean up temp/ folder by deleting files based on criteria.

    Args:
        temp_path: Path to temp/ folder
        execute: If True, actually delete files. If False, dry run only.
        age_threshold: Age threshold in days (default: 30)
    """
    if not temp_path.exists():
        print(f"[INFO] temp/ folder not found: {temp_path}")
        return

    if not temp_path.is_dir():
        print(f"[ERROR] {temp_path} is not a directory")
        return

    # Collect all files in temp/
    files = [f for f in temp_path.iterdir() if f.is_file()]

    if not files:
        print(f"[INFO] temp/ folder is empty")
        return

    print(f"\n{'='*70}")
    print(f"Cleanup Mode: {'EXECUTE' if execute else 'DRY RUN (preview only)'}")
    print(f"Age Threshold: {age_threshold} days")
    print(f"temp/ folder: {temp_path}")
    print(f"{'='*70}\n")

    to_delete = []
    to_keep = []

    # Analyze each file
    for filepath in files:
        should_del, reason = should_delete(filepath, age_threshold)

        if should_del:
            to_delete.append((filepath, reason))
        else:
            to_keep.append((filepath, reason))

    # Report files to delete
    if to_delete:
        print(f"Files to DELETE ({len(to_delete)}):")
        for filepath, reason in to_delete:
            age_days = get_file_age_days(filepath)
            print(f"  X {filepath.name}")
            print(f"     Reason: {reason}")
            print(f"     Age: {age_days:.1f} days")
    else:
        print("No files to delete.")

    print()

    # Report files to keep
    if to_keep:
        print(f"Files to KEEP ({len(to_keep)}):")
        for filepath, reason in to_keep:
            age_days = get_file_age_days(filepath)
            print(f"  OK {filepath.name}")
            print(f"     Reason: {reason}")
            print(f"     Age: {age_days:.1f} days")

    print(f"\n{'='*70}\n")

    # Execute deletion if requested
    if execute and to_delete:
        print("Deleting files...")
        deleted_count = 0
        error_count = 0

        for filepath, reason in to_delete:
            try:
                filepath.unlink()
                print(f"  OK Deleted: {filepath.name}")
                deleted_count += 1
            except Exception as e:
                print(f"  X Failed to delete {filepath.name}: {e}")
                error_count += 1

        print(f"\nSummary: {deleted_count} deleted, {error_count} errors")
    elif not execute and to_delete:
        print("[DRY RUN] No files were actually deleted.")
        print("To execute deletion, run with --execute flag")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Cleanup SST3/temp/ folder based on issue status and file age",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cleanup-temp.py              # Dry run (preview only)
  python cleanup-temp.py --execute    # Actually delete files
  python cleanup-temp.py --age 45     # Custom age threshold (45 days)

Deletion Criteria:
  1. Issue linked in filename is closed, OR
  2. File age > threshold (default: 30 days)

Protected Files:
  - README.md, .gitkeep, .gitignore (never deleted)
"""
    )

    parser.add_argument(
        '--execute',
        action='store_true',
        help='Actually delete files (default: dry run only)'
    )

    parser.add_argument(
        '--age',
        type=int,
        default=30,
        help='Age threshold in days (default: 30)'
    )

    parser.add_argument(
        '--temp-path',
        type=Path,
        default=None,
        help='Path to temp/ folder (default: auto-detect from script location)'
    )

    args = parser.parse_args()

    # Validate age parameter
    if args.age < 0:
        parser.error("age must be non-negative")

    # Determine temp/ path
    if args.temp_path:
        temp_path = args.temp_path
    else:
        import os
        temp_dir = os.environ.get('SST3_TEMP')
        if not temp_dir:
            print("ERROR: SST3_TEMP environment variable not set.", file=sys.stderr)
            print("Set via: export SST3_TEMP=/path/to/temp", file=sys.stderr)
            sys.exit(1)
        temp_path = Path(temp_dir)

    # Run cleanup
    cleanup_temp(temp_path, execute=args.execute, age_threshold=args.age)


if __name__ == '__main__':
    main()
