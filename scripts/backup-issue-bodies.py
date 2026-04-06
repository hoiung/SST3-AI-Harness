#!/usr/bin/env python3
"""Backup issue bodies before Issue Assignment rollout.

This script creates a JSON snapshot of all open issue bodies across specified
repos. Used as a safety net before running rollout-issue-assignment.py.

Exit codes:
    0: Backup successful
    3: Error (gh CLI not found, file write error, repo not found)
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from sst3_utils import fix_windows_console, KNOWN_REPOS

fix_windows_console()


# Build REPOS path dict from sst3_utils.KNOWN_REPOS — single source of truth.
# dotfiles is special-cased (its scripts are inside SST3/scripts so the path
# resolution differs from sibling repos).
_DOTFILES_ROOT = Path(__file__).resolve().parent.parent.parent
_DEVPROJECTS = _DOTFILES_ROOT.parent
REPOS = {
    name: (_DOTFILES_ROOT if name == 'dotfiles' else _DEVPROJECTS / name)
    for name in KNOWN_REPOS
}


def fetch_open_issues(repo_path: Path) -> list[dict]:
    """Fetch all open issues for a repository.

    Args:
        repo_path: Path to repository directory

    Returns:
        List of issue dicts with number, title, body, labels

    Raises:
        subprocess.CalledProcessError: If gh CLI fails
    """
    result = subprocess.run(
        ['gh', 'issue', 'list', '--state', 'open', '--json', 'number,title,body,labels', '--limit', '1000'],
        cwd=repo_path,
        capture_output=True,
        text=True,
        encoding='utf-8',
        timeout=60,
        check=True
    )
    return json.loads(result.stdout)


def filter_non_epic_issues(issues: list[dict]) -> list[dict]:
    """Filter out issues with 'epic' label.

    Args:
        issues: List of issue dicts

    Returns:
        Filtered list excluding epic issues
    """
    return [
        issue for issue in issues
        if not any(label.get('name') == 'epic' for label in issue.get('labels', []))
    ]


def backup_issues(repos: list[str], output_path: str) -> dict:
    """Backup issue bodies from specified repositories.

    Args:
        repos: List of repository names ('dotfiles', 'auto_pb_swing_trader', etc.)
        output_path: Path to output JSON file

    Returns:
        Backup data dictionary

    Raises:
        FileNotFoundError: If repository path doesn't exist
        subprocess.CalledProcessError: If gh CLI fails
    """
    backups = {}
    total_issues = 0

    for repo_name in repos:
        if repo_name not in REPOS:
            print(f"Error: Unknown repo '{repo_name}'", file=sys.stderr)
            sys.exit(3)

        repo_path = REPOS[repo_name]
        if not repo_path.exists():
            print(f"Error: Repository path not found: {repo_path}", file=sys.stderr)
            sys.exit(3)

        print(f"Fetching issues from {repo_name}...")
        all_issues = fetch_open_issues(repo_path)
        filtered_issues = filter_non_epic_issues(all_issues)

        backups[repo_name] = [
            {
                'number': issue['number'],
                'title': issue['title'],
                'body': issue['body'],
                'labels': [label['name'] for label in issue.get('labels', [])],
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
            for issue in filtered_issues
        ]

        total_issues += len(backups[repo_name])
        print(f"  ✓ Backed up {len(backups[repo_name])} issues (excluded {len(all_issues) - len(backups[repo_name])} epic issues)")

    result = {
        'metadata': {
            'created_at': datetime.utcnow().isoformat() + 'Z',
            'repos': repos,
            'total_issues': total_issues
        },
        'backups': backups
    }

    # Atomic write backup file
    output = Path(output_path)
    tmp = output.with_suffix('.tmp')
    tmp.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    tmp.replace(output)
    print(f"\n✓ Backup saved to: {output_path}")
    print(f"  Total issues backed up: {total_issues}")

    return result


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Backup issue bodies before Stage Assignment rollout',
        epilog='''
Examples:
  # Backup dotfiles issues
  python SST3/scripts/backup-issue-bodies.py --repos dotfiles --output backup-dotfiles.json

  # Backup all repos
  python SST3/scripts/backup-issue-bodies.py --repos all --output backup-20251128.json

  # Backup specific repos
  python SST3/scripts/backup-issue-bodies.py --repos dotfiles,auto_pb_swing_trader --output backup.json
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--repos',
        required=True,
        help='Repositories to backup (dotfiles, auto_pb_swing_trader, tradebook_GAS, or "all")'
    )
    parser.add_argument(
        '--output',
        required=True,
        help='Output JSON file path (e.g., backup-20251128.json)'
    )

    args = parser.parse_args()

    # Parse repos argument
    if args.repos == 'all':
        repos = list(REPOS.keys())
    else:
        repos = [r.strip() for r in args.repos.split(',')]

    # Check for gh CLI
    try:
        subprocess.run(['gh', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: GitHub CLI (gh) not found or not working", file=sys.stderr)
        sys.exit(3)

    try:
        backup_issues(repos, args.output)
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(3)


if __name__ == '__main__':
    main()
