#!/usr/bin/env python3
"""
Automated Rollback Tool for Failed Self-Healing Changes

Executes automatic rollback when Stage 5 validation fails or 3-issue
validation shows 0/3 success rate. Uses git revert for reversible rollback.

Usage:
    auto-rollback.py <issue-number> [options]

    # Dry-run (preview only)
    auto-rollback.py 119 --dry-run

    # Execute rollback
    auto-rollback.py 119 --execute

    # Rollback from specific commit
    auto-rollback.py 119 --since-commit abc123 --execute

    # Preserve files before reverting
    auto-rollback.py 119 --preserve-dir "$SST3_TEMP/backup" --execute

Safety:
    - Default is dry-run mode (no changes)
    - Confirmation prompt unless --yes flag
    - Preserves files in temp/ before reverting
    - Uses git revert (reversible, not reset)
    - Documents rollback in Issue comments
"""

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from sst3_utils import get_repo_root, fix_windows_console, fetch_issue_data


class AutoRollback:
    """Automated rollback system for failed changes"""

    def __init__(self, issue_number: int, dry_run: bool = True,
                 preserve_dir: Optional[str] = None, since_commit: Optional[str] = None):
        self.issue_number = issue_number
        self.dry_run = dry_run
        self.preserve_dir = Path(preserve_dir) if preserve_dir else None
        self.since_commit = since_commit
        self.repo_root = get_repo_root()

    def get_issue_data(self) -> Optional[Dict]:
        """Fetch Issue data using shared sst3_utils.fetch_issue_data helper.

        Refactored from direct subprocess.run to deduplicate against
        sst3_utils.fetch_issue_data per dotfiles#405 Phase 7 (audit Finding 15).
        """
        return fetch_issue_data(
            self.issue_number,
            ['title', 'body', 'comments', 'state'],
        )

    def should_rollback(self, issue_data: Dict) -> Tuple[bool, str]:
        """Determine if rollback should be executed"""
        body = issue_data.get('body', '')
        comments = [c['body'] for c in issue_data.get('comments', [])]
        all_text = body + '\n'.join(comments)

        # Check for validation failure indicators
        failure_indicators = [
            ('Solo Assignment FAIL', 'Stage 5 verification failed'),
            ('Verification Loop FAIL', 'Stage 4 verification failed'),
            ('VALIDATION FAIL', 'Validation failed'),
            ('0/3 success', '3-issue validation showed 0/3 success'),
            ('AUTO-REVERT', 'Auto-revert triggered from validation protocol'),
            ('REVERT NEEDED', 'Manual revert request'),
        ]

        for indicator, reason in failure_indicators:
            if indicator in all_text:
                return True, reason

        return False, "No rollback indicators found"

    def get_commits_since_issue_start(self) -> List[str]:
        """Get list of commits associated with this issue"""
        if self.since_commit:
            # Rollback from specific commit
            commit_range = f"{self.since_commit}..HEAD"
        else:
            # Find commits mentioning this issue
            try:
                result = subprocess.run(
                    ['git', 'log', '--oneline', '--all', '--grep', f'#{self.issue_number}'],
                    capture_output=True,
                    text=True,
                    check=True
                )
                commits = [line.split()[0] for line in result.stdout.strip().split('\n') if line]
                return commits
            except subprocess.CalledProcessError:
                return []

        # Get commits in range
        try:
            result = subprocess.run(
                ['git', 'log', '--oneline', commit_range],
                capture_output=True,
                text=True,
                check=True
            )
            commits = [line.split()[0] for line in result.stdout.strip().split('\n') if line]
            return commits
        except subprocess.CalledProcessError:
            return []

    def get_changed_files(self, commits: List[str]) -> List[str]:
        """Get list of files changed in commits"""
        all_files = set()

        for commit in commits:
            try:
                result = subprocess.run(
                    ['git', 'show', '--name-only', '--pretty=', commit],
                    capture_output=True,
                    text=True,
                    check=True
                )
                files = [f for f in result.stdout.strip().split('\n') if f]
                all_files.update(files)
            except subprocess.CalledProcessError:
                continue

        return sorted(all_files)

    def preserve_files(self, files: List[str]) -> bool:
        """Preserve files before rollback"""
        if not self.preserve_dir:
            return True

        try:
            self.preserve_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_dir = self.preserve_dir / f"rollback_issue{self.issue_number}_{timestamp}"
            backup_dir.mkdir(parents=True, exist_ok=True)

            print(f"Preserving files to: {backup_dir}")

            for file_path in files:
                src = self.repo_root / file_path
                if src.exists():
                    dst = backup_dir / file_path
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
                    print(f"  Preserved: {file_path}")

            # Create metadata file
            metadata = {
                'issue_number': self.issue_number,
                'timestamp': timestamp,
                'files_preserved': files,
                'reason': 'Rollback preparation'
            }

            metadata_file = backup_dir / 'rollback_metadata.json'
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)

            print(f"\nBackup complete: {len(files)} files preserved")
            return True

        except Exception as e:
            print(f"Error preserving files: {e}", file=sys.stderr)
            return False

    def execute_rollback(self, commits: List[str]) -> bool:
        """Execute git revert for commits"""
        if not commits:
            print("No commits to revert")
            return False

        print(f"\nReverting {len(commits)} commits...")

        # Revert in reverse order (newest first)
        for commit in reversed(commits):
            try:
                if self.dry_run:
                    print(f"  [DRY-RUN] Would revert: {commit}")
                else:
                    result = subprocess.run(
                        ['git', 'revert', '--no-edit', commit],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    print(f"  Reverted: {commit}")
            except subprocess.CalledProcessError as e:
                print(f"  Error reverting {commit}: {e}", file=sys.stderr)
                if not self.dry_run:
                    # Abort revert on failure
                    subprocess.run(['git', 'revert', '--abort'],
                                 capture_output=True, check=False)
                    return False

        return True

    def document_rollback(self, commits: List[str], reason: str) -> bool:
        """Document rollback in Issue comment"""
        comment = f"""## Auto-Rollback Executed - Issue #{self.issue_number}

**Timestamp**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Reason**: {reason}
**Commits Reverted**: {len(commits)}

### Reverted Commits
{chr(10).join(f'- {commit}' for commit in commits)}

### Failed Experiment Documentation
This rollback has been documented in `SST3/reference/failed-experiments.md`.

### Recovery Actions
1. Analyze why validation failed
2. Refine approach based on learnings
3. Create new issue if alternative approach needed

**Note**: This was an automatic rollback triggered by validation failure.
The changes have been preserved and can be recovered if needed.
"""

        if self.dry_run:
            print("\n[DRY-RUN] Would post to Issue:")
            print(comment)
            return True

        try:
            result = subprocess.run(
                ['gh', 'issue', 'comment', str(self.issue_number), '--body', comment],
                capture_output=True,
                text=True,
                check=True
            )
            print(f"\nRollback documented in Issue #{self.issue_number}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error posting to Issue: {e}", file=sys.stderr)
            return False

    def update_failed_experiments(self, reason: str, files: List[str]) -> bool:
        """Update failed-experiments.md with entry"""
        failed_experiments_path = self.repo_root / 'SST3' / 'reference' / 'failed-experiments.md'

        if not failed_experiments_path.exists():
            print(f"Warning: failed-experiments.md not found at {failed_experiments_path}",
                  file=sys.stderr)
            return False

        entry = f"""
### Issue #{self.issue_number} - {datetime.now().strftime('%Y-%m-%d')}
**Origin**: Issue #{self.issue_number}
**Description**: Changes rolled back due to validation failure
**Reason**: {reason}
**Files Affected**: {', '.join(files[:5])}{'...' if len(files) > 5 else ''}
**Observations**: Validation failed during 3-issue observation period
**Alternative**: Review validation feedback and refine approach

"""

        if self.dry_run:
            print("\n[DRY-RUN] Would add to failed-experiments.md:")
            print(entry)
            return True

        try:
            with open(failed_experiments_path, 'a', encoding='utf-8') as f:
                f.write(entry)
            print(f"Updated failed-experiments.md")
            return True
        except Exception as e:
            print(f"Error updating failed-experiments.md: {e}", file=sys.stderr)
            return False

    def run(self, skip_confirmation: bool = False) -> bool:
        """Execute complete rollback workflow"""
        print("=" * 70)
        print(f"AUTO-ROLLBACK - Issue #{self.issue_number}")
        print("=" * 70)
        print(f"Mode: {'DRY-RUN (preview only)' if self.dry_run else 'EXECUTE (will make changes)'}")
        print()

        # Step 1: Fetch Issue data
        print("Step 1: Checking Issue data...")
        issue_data = self.get_issue_data()
        if not issue_data:
            print("Failed to fetch Issue data")
            return False

        # Step 2: Check if rollback needed
        print("\nStep 2: Checking rollback conditions...")
        should_rollback, reason = self.should_rollback(issue_data)

        if not should_rollback:
            print(f"✓ No rollback needed: {reason}")
            return True

        print(f"⚠ Rollback needed: {reason}")

        # Step 3: Get commits to revert
        print("\nStep 3: Identifying commits to revert...")
        commits = self.get_commits_since_issue_start()

        if not commits:
            print("No commits found for this issue")
            return False

        print(f"Found {len(commits)} commits to revert:")
        for commit in commits:
            print(f"  - {commit}")

        # Step 4: Get changed files
        print("\nStep 4: Identifying changed files...")
        files = self.get_changed_files(commits)
        print(f"Found {len(files)} files affected:")
        for f in files[:10]:
            print(f"  - {f}")
        if len(files) > 10:
            print(f"  ... and {len(files) - 10} more")

        # Step 5: Confirmation
        if not self.dry_run and not skip_confirmation:
            print("\n⚠ WARNING: This will execute git revert on the above commits")
            response = input("Continue? (yes/no): ").strip().lower()
            if response != 'yes':
                print("Rollback cancelled")
                return False

        # Step 6: Preserve files
        if self.preserve_dir:
            print("\nStep 5: Preserving files...")
            if not self.preserve_files(files):
                print("Failed to preserve files")
                if not self.dry_run:
                    return False

        # Step 7: Execute rollback
        print("\nStep 6: Executing rollback...")
        if not self.execute_rollback(commits):
            print("Rollback failed")
            return False

        # Step 8: Document rollback
        print("\nStep 7: Documenting rollback...")
        self.document_rollback(commits, reason)

        # Step 9: Update failed experiments
        print("\nStep 8: Updating failed-experiments.md...")
        self.update_failed_experiments(reason, files)

        print("\n" + "=" * 70)
        if self.dry_run:
            print("DRY-RUN COMPLETE - No changes made")
            print("Run with --execute to perform actual rollback")
        else:
            print("ROLLBACK COMPLETE")
            print(f"Changes from Issue #{self.issue_number} have been reverted")
            if self.preserve_dir:
                print(f"Files preserved in: {self.preserve_dir}")
        print("=" * 70)

        return True


def main():
    fix_windows_console()

    parser = argparse.ArgumentParser(
        description='Automated rollback for failed self-healing changes',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Preview rollback (dry-run)
  auto-rollback.py 119 --dry-run

  # Execute rollback with confirmation
  auto-rollback.py 119 --execute

  # Execute without confirmation
  auto-rollback.py 119 --execute --yes

  # Rollback from specific commit
  auto-rollback.py 119 --since-commit abc123 --execute

  # Preserve files before rollback
  auto-rollback.py 119 --preserve-dir "$SST3_TEMP/backup" --execute

Safety Notes:
  - Default is dry-run mode (safe to run)
  - Uses git revert (not reset) - reversible
  - Confirmation prompt unless --yes
  - Files can be preserved before rollback
        """
    )

    parser.add_argument('issue_number', type=int,
                       help='GitHub Issue number to rollback')
    parser.add_argument('--dry-run', action='store_true', default=True,
                       help='Preview mode (default, no changes made)')
    parser.add_argument('--execute', action='store_true',
                       help='Execute actual rollback (overrides --dry-run)')
    parser.add_argument('--yes', action='store_true',
                       help='Skip confirmation prompt')
    parser.add_argument('--since-commit', type=str,
                       help='Rollback commits since this commit hash')
    parser.add_argument('--preserve-dir', type=str,
                       help='Directory to preserve files before rollback')

    args = parser.parse_args()

    # Execute overrides dry-run
    dry_run = not args.execute

    rollback = AutoRollback(
        issue_number=args.issue_number,
        dry_run=dry_run,
        preserve_dir=args.preserve_dir,
        since_commit=args.since_commit
    )

    success = rollback.run(skip_confirmation=args.yes)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
