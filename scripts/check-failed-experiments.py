#!/usr/bin/env python3
"""
Check Failed Experiments - Infinite Loop Prevention

Prevents "Fix-Revert-Fix" infinite loops by checking if proposed fixes
have failed validation before. Implements 3-attempt threshold with
PERMANENT BLOCK after repeated failures.

Usage:
    # Check if fix should be applied
    python check-failed-experiments.py "Always use UTF-8 encoding" --issue 119

    # Add new failed experiment entry
    python check-failed-experiments.py --add-failure "UTF-8 encoding" \
        --issue 119 --reason "Breaks Windows cp1252" --alternative "Check encoding first"

    # List all failed experiments
    python check-failed-experiments.py --list

    # Get attempt count only
    python check-failed-experiments.py "UTF-8 encoding" --count

Exit Codes:
    0: Safe to apply (not in failed experiments)
    1: Apply with modification (1-2 prior failures)
    2: PERMANENT BLOCK (3+ failures)
    3: Error (missing log file, parse error, etc.)

Architecture:
    - temp/{issue#}-failed-experiments.log: Per-issue failures
    - .sst3-local/failed-experiments.log: Project-level patterns
    - SST3/reference/failed-experiments.md: Template/process guide
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from sst3_utils import get_repo_root, fix_windows_console
fix_windows_console()


class FailedExperimentChecker:
    """Check and manage failed experiments to prevent infinite loops"""

    def __init__(self, issue_number: Optional[int] = None, verbose: bool = False):
        """
        Initialize checker with optional issue number.

        Args:
            issue_number: Current issue number (for temp log path)
            verbose: Enable verbose output
        """
        self.issue_number = issue_number
        self.verbose = verbose
        self.repo_root = get_repo_root()

        # Log paths
        self.project_log = self.repo_root / ".sst3-local" / "failed-experiments.log"
        self.temp_log = None
        if issue_number:
            temp_dir = os.environ.get('SST3_TEMP')
            if not temp_dir:
                # Raise instead of sys.exit so callers can handle (avoids hard-exit
                # from constructor crashing entire pre-commit hook)
                raise EnvironmentError(
                    "SST3_TEMP environment variable not set. "
                    "Set via: export SST3_TEMP=/path/to/temp"
                )
            repo_name = self.repo_root.name
            self.temp_log = Path(temp_dir) / f"{repo_name}-{issue_number}-failed-experiments.log"

    def _get_repo_name(self) -> str:
        """Get repository name from current directory"""
        return self.repo_root.name

    def _vprint(self, message: str):
        """Print if verbose mode enabled"""
        if self.verbose:
            print(f"[DEBUG] {message}", file=sys.stderr)

    def parse_log(self, log_path: Path) -> List[Dict]:
        """
        Parse failed-experiments.log and return structured data.

        Args:
            log_path: Path to log file

        Returns:
            List of experiment dictionaries with keys:
            - title: Experiment title
            - description: Full description
            - attempts: List of attempt dicts (issue, date, reason)
            - status: Current status (PERMANENT BLOCK, etc.)
            - alternative: Suggested alternative approach
        """
        if not log_path.exists():
            self._vprint(f"Log file not found: {log_path}")
            return []

        experiments = []
        current_experiment = None

        try:
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            self._vprint(f"Error reading log: {e}")
            return []

        # Parse markdown structure
        lines = content.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # New experiment section (### Title)
            if line.startswith('### '):
                if current_experiment:
                    experiments.append(current_experiment)

                current_experiment = {
                    'title': line[4:].strip(),
                    'description': '',
                    'attempts': [],
                    'status': '',
                    'alternative': ''
                }

            # Description field
            elif line.startswith('**Description**:') and current_experiment:
                current_experiment['description'] = line.split(':', 1)[1].strip()

            # Attempts section
            elif line.startswith('**Attempts**:') and current_experiment:
                i += 1
                # Parse attempt list items
                while i < len(lines) and lines[i].strip().startswith('-'):
                    attempt_line = lines[i].strip()[1:].strip()
                    # Format: "Issue #119: 2025-11-10 - Validation failed (reason)"
                    # Support both arrow and dash separators
                    match = re.match(r'Issue #(\d+):\s*(\S+)\s*[-\u2192]\s*(.+)', attempt_line)
                    if match:
                        current_experiment['attempts'].append({
                            'issue': int(match.group(1)),
                            'date': match.group(2),
                            'reason': match.group(3).strip()
                        })
                    i += 1
                i -= 1  # Back up one line

            # Status field
            elif line.startswith('**Status**:') and current_experiment:
                current_experiment['status'] = line.split(':', 1)[1].strip()

            # Alternative field
            elif line.startswith('**Alternative**:') and current_experiment:
                current_experiment['alternative'] = line.split(':', 1)[1].strip()

            i += 1

        # Add last experiment
        if current_experiment:
            experiments.append(current_experiment)

        self._vprint(f"Parsed {len(experiments)} experiments from {log_path}")
        return experiments

    def fix_in_log(self, fix_description: str, log_path: Path) -> bool:
        """
        Check if fix description appears in failed experiments log.

        Args:
            fix_description: Description of the proposed fix
            log_path: Path to log file

        Returns:
            True if fix found in log, False otherwise
        """
        experiments = self.parse_log(log_path)
        fix_lower = fix_description.lower()

        for exp in experiments:
            # Check title and description (case-insensitive partial match)
            if fix_lower in exp['title'].lower() or fix_lower in exp['description'].lower():
                self._vprint(f"Found match in experiment: {exp['title']}")
                return True

        return False

    def get_attempt_count(self, fix_description: str, log_path: Path) -> int:
        """
        Get number of times this fix has been attempted.

        Args:
            fix_description: Description of the proposed fix
            log_path: Path to log file

        Returns:
            Number of attempts (0 if not found)
        """
        experiments = self.parse_log(log_path)
        fix_lower = fix_description.lower()

        for exp in experiments:
            if fix_lower in exp['title'].lower() or fix_lower in exp['description'].lower():
                count = len(exp['attempts'])
                self._vprint(f"Found {count} attempts for: {exp['title']}")
                return count

        return 0

    def get_experiment(self, fix_description: str, log_path: Path) -> Optional[Dict]:
        """
        Get full experiment data for a fix.

        Args:
            fix_description: Description of the proposed fix
            log_path: Path to log file

        Returns:
            Experiment dictionary or None if not found
        """
        experiments = self.parse_log(log_path)
        fix_lower = fix_description.lower()

        for exp in experiments:
            if fix_lower in exp['title'].lower() or fix_lower in exp['description'].lower():
                return exp

        return None

    def suggest_modification(self, fix_description: str, log_path: Path) -> str:
        """
        Suggest alternative approach based on failed experiment learnings.

        Args:
            fix_description: Description of the proposed fix
            log_path: Path to log file

        Returns:
            Suggested alternative or generic message
        """
        exp = self.get_experiment(fix_description, log_path)

        if exp and exp['alternative']:
            return exp['alternative']

        if exp and exp['attempts']:
            # Generate suggestion based on failure reasons
            reasons = [a['reason'] for a in exp['attempts']]
            return f"Previous failures: {', '.join(reasons[:2])}. Try different approach."

        return "No specific alternative documented. Analyze root cause before retrying."

    def should_apply_fix(self, fix_description: str, issue_number: Optional[int] = None) -> Tuple[Union[bool, str], str]:
        """
        Check if fix should be applied based on failed experiments history.

        Args:
            fix_description: Description of the proposed fix
            issue_number: Current issue number (uses self.issue_number if not provided)

        Returns:
            Tuple of (decision, reason) where decision is:
            - True: Safe to apply with 3-issue validation
            - False: Block application (already failed or 3+ attempts)
            - "with_modification": Apply with modifications (1-2 prior failures)
        """
        if issue_number is None:
            issue_number = self.issue_number

        # Check temp log first (issue-specific)
        if self.temp_log and self.temp_log.exists():
            if self.fix_in_log(fix_description, self.temp_log):
                return False, f"Already failed in Issue #{issue_number}"

        # Check project log (cross-issue patterns)
        if self.project_log.exists():
            if self.fix_in_log(fix_description, self.project_log):
                count = self.get_attempt_count(fix_description, self.project_log)
                exp = self.get_experiment(fix_description, self.project_log)

                if count >= 3:
                    issues = [str(a['issue']) for a in exp['attempts'][:3]] if exp else []
                    issues_str = f"Issues #{', #'.join(issues)}" if issues else "multiple issues"
                    return False, f"PERMANENT BLOCK - Failed 3+ times ({issues_str})"
                else:
                    return "with_modification", f"Failed {count} time(s) before - apply with modification"

        # Not found = safe to try
        return True, "Not in failed experiments - safe to apply with 3-issue validation"

    def add_failure(self, fix_description: str, issue_number: int,
                    reason: str, alternative: str = "") -> bool:
        """
        Add new failed experiment entry to appropriate log.

        Args:
            fix_description: Description of the failed fix
            issue_number: Issue number where it failed
            reason: Why it failed (validation error)
            alternative: Suggested alternative approach

        Returns:
            True if successfully added, False on error
        """
        # Determine which log to update
        target_log = self.project_log  # Default to project log

        # Check if this experiment already exists
        exp = self.get_experiment(fix_description, target_log)

        today = datetime.now().strftime("%Y-%m-%d")

        try:
            # Ensure parent directory exists
            target_log.parent.mkdir(parents=True, exist_ok=True)

            if exp:
                # Append to existing experiment
                self._vprint(f"Updating existing experiment: {exp['title']}")

                # Read current content
                with open(target_log, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                # Find the experiment section and add new attempt
                title_pattern = f"### {re.escape(exp['title'])}"
                # Insert new attempt after **Attempts**: line
                attempts_pattern = r'(\*\*Attempts\*\*:)'
                new_attempt = f"\n  - Issue #{issue_number}: {today} - {reason}"

                # Find and update
                content = re.sub(
                    f"({title_pattern}.*?{attempts_pattern})",
                    f"\\1{new_attempt}",
                    content,
                    flags=re.DOTALL
                )

                # Update status if needed (3+ attempts)
                attempt_count = len(exp['attempts']) + 1
                if attempt_count >= 3:
                    content = re.sub(
                        r'(\*\*Status\*\*:)[^\n]*',
                        f"\\1 PERMANENT BLOCK ({attempt_count}+ failures)",
                        content
                    )

                # Atomic write
                tmp = target_log.with_suffix('.tmp')
                tmp.write_text(content, encoding='utf-8')
                tmp.replace(target_log)

            else:
                # Create new experiment entry
                self._vprint(f"Creating new experiment: {fix_description}")

                # Generate title from description
                title = fix_description.split('.')[0].strip()
                if len(title) > 50:
                    title = title[:47] + "..."

                entry = f"""
### {title}
**Description**: {fix_description}
**Attempts**:
  - Issue #{issue_number}: {today} - {reason}
**Status**: Observed (1 failure)
**Alternative**: {alternative if alternative else "[To be determined]"}

"""
                # Append to file
                with open(target_log, 'a', encoding='utf-8') as f:
                    f.write(entry)

            self._vprint(f"Successfully added failure to {target_log}")
            return True

        except Exception as e:
            print(f"Error adding failure: {e}", file=sys.stderr)
            return False

    def list_experiments(self, log_path: Optional[Path] = None) -> List[Dict]:
        """
        List all failed experiments from log file.

        Args:
            log_path: Path to log file (uses project_log if not provided)

        Returns:
            List of experiment dictionaries
        """
        if log_path is None:
            log_path = self.project_log

        return self.parse_log(log_path)


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description="Check failed experiments to prevent infinite loops",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check if fix should be applied
  %(prog)s "Always use UTF-8 encoding" --issue 119

  # Add new failed experiment
  %(prog)s --add-failure "UTF-8 encoding" --issue 119 \\
      --reason "Breaks Windows cp1252" --alternative "Check encoding first"

  # List all failed experiments
  %(prog)s --list

  # Get attempt count
  %(prog)s "UTF-8 encoding" --count

Exit Codes:
  0: Safe to apply (not in failed experiments)
  1: Apply with modification (1-2 prior failures)
  2: PERMANENT BLOCK (3+ failures)
  3: Error (missing log file, parse error, etc.)

Environment:
  SST3_TEMP: REQUIRED when --issue is used. Path to temp folder for per-issue
             logs (e.g. export SST3_TEMP=/c/temp). Constructor raises
             EnvironmentError if unset.
        """
    )

    # Main argument (fix description)
    parser.add_argument(
        'fix_description',
        nargs='?',
        help='Description of proposed fix to check'
    )

    # Actions
    parser.add_argument(
        '--add-failure',
        metavar='DESCRIPTION',
        help='Add new failed experiment entry'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all failed experiments'
    )
    parser.add_argument(
        '--count',
        action='store_true',
        help='Show only attempt count for fix'
    )

    # Parameters
    parser.add_argument(
        '--issue',
        type=int,
        metavar='NUM',
        help='Issue number'
    )
    parser.add_argument(
        '--reason',
        metavar='TEXT',
        help='Failure reason (for --add-failure)'
    )
    parser.add_argument(
        '--alternative',
        metavar='TEXT',
        default='',
        help='Alternative approach suggestion (for --add-failure)'
    )
    parser.add_argument(
        '--log',
        metavar='PATH',
        help='Specific log file path (default: .sst3-local/failed-experiments.log)'
    )

    # Options
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output in JSON format'
    )

    args = parser.parse_args()

    # Initialize checker
    checker = FailedExperimentChecker(
        issue_number=args.issue,
        verbose=args.verbose
    )

    # Override log path if specified
    if args.log:
        checker.project_log = Path(args.log)

    try:
        # Action: List experiments
        if args.list:
            experiments = checker.list_experiments()

            if args.json:
                print(json.dumps(experiments, indent=2))
            else:
                if not experiments:
                    print("No failed experiments found.")
                    sys.exit(0)

                print(f"\n{'='*70}")
                print(f"FAILED EXPERIMENTS LOG")
                print(f"{'='*70}\n")

                for exp in experiments:
                    print(f"Title: {exp['title']}")
                    print(f"Description: {exp['description']}")
                    print(f"Attempts: {len(exp['attempts'])}")
                    if exp['attempts']:
                        for attempt in exp['attempts']:
                            print(f"  - Issue #{attempt['issue']}: {attempt['date']} → {attempt['reason']}")
                    print(f"Status: {exp['status']}")
                    if exp['alternative']:
                        print(f"Alternative: {exp['alternative']}")
                    print()

            sys.exit(0)

        # Action: Add failure
        if args.add_failure:
            if not args.issue:
                print("Error: --issue required with --add-failure", file=sys.stderr)
                sys.exit(3)
            if not args.reason:
                print("Error: --reason required with --add-failure", file=sys.stderr)
                sys.exit(3)

            success = checker.add_failure(
                args.add_failure,
                args.issue,
                args.reason,
                args.alternative
            )

            if success:
                print(f"Successfully added failure for Issue #{args.issue}")
                sys.exit(0)
            else:
                print("Failed to add entry", file=sys.stderr)
                sys.exit(3)

        # Action: Count only
        if args.count:
            if not args.fix_description:
                print("Error: fix description required with --count", file=sys.stderr)
                sys.exit(3)

            count = checker.get_attempt_count(args.fix_description, checker.project_log)

            if args.json:
                print(json.dumps({'fix': args.fix_description, 'attempts': count}))
            else:
                print(f"Attempt count: {count}")

            sys.exit(0)

        # Default action: Check if fix should be applied
        if not args.fix_description:
            parser.print_help()
            sys.exit(3)

        decision, reason = checker.should_apply_fix(args.fix_description, args.issue)

        # Determine exit code
        if decision is True:
            exit_code = 0
            status = "SAFE"
        elif decision == "with_modification":
            exit_code = 1
            status = "MODIFY"
        else:  # False
            exit_code = 2
            status = "BLOCK"

        # Output
        if args.json:
            result = {
                'fix': args.fix_description,
                'status': status,
                'exit_code': exit_code,
                'reason': reason,
                'decision': decision if isinstance(decision, bool) else decision
            }

            # Add alternative if available
            if decision == "with_modification" or decision is False:
                alternative = checker.suggest_modification(
                    args.fix_description,
                    checker.project_log
                )
                result['alternative'] = alternative

            print(json.dumps(result, indent=2))
        else:
            print(f"\nSTATUS: {status}")
            print(f"REASON: {reason}")

            if decision == "with_modification" or decision is False:
                alternative = checker.suggest_modification(
                    args.fix_description,
                    checker.project_log
                )
                print(f"ALTERNATIVE: {alternative}")

            print(f"EXIT: {exit_code}\n")

        sys.exit(exit_code)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(3)


# Unit Tests (run with: python check-failed-experiments.py --test)
def run_tests():
    """Run inline unit tests"""
    import tempfile
    import shutil

    print("\n" + "="*70)
    print("RUNNING UNIT TESTS")
    print("="*70 + "\n")

    # Create temporary directory for test logs
    test_dir = Path(tempfile.mkdtemp())

    try:
        # Test 1: Empty log (no failures)
        print("Test 1: Fix not in any log (should return True)")
        test_log = test_dir / "test1.log"
        test_log.write_text("")

        checker = FailedExperimentChecker()
        checker.project_log = test_log
        decision, reason = checker.should_apply_fix("New fix approach", 119)

        assert decision is True, f"Expected True, got {decision}"
        assert "safe to apply" in reason.lower(), f"Unexpected reason: {reason}"
        print(f"  [PASS] {reason}\n")

        # Test 2: One failure (should return with_modification)
        print("Test 2: Fix with 1 failure (should return with_modification)")
        test_log2 = test_dir / "test2.log"
        test_log2.write_text("""
### UTF-8 Encoding
**Description**: Always use UTF-8 encoding for Windows compatibility
**Attempts**:
  - Issue #119: 2025-11-10 - Validation failed (broke cp1252)
**Status**: Observed (1 failure)
**Alternative**: Check sys.stdout.encoding first
""", encoding='utf-8')

        checker2 = FailedExperimentChecker()
        checker2.project_log = test_log2
        decision, reason = checker2.should_apply_fix("UTF-8 encoding", 120)

        assert decision == "with_modification", f"Expected with_modification, got {decision}"
        assert "1 time" in reason, f"Unexpected reason: {reason}"
        print(f"  [PASS] {reason}\n")

        # Test 3: Three failures (should return False)
        print("Test 3: Fix with 3 failures (should return False - PERMANENT BLOCK)")
        test_log3 = test_dir / "test3.log"
        test_log3.write_text("""
### UTF-8 Encoding
**Description**: Always use UTF-8 encoding for Windows compatibility
**Attempts**:
  - Issue #119: 2025-11-10 - Validation failed (broke cp1252)
  - Issue #125: 2025-11-15 - Validation failed (broke cp1252)
  - Issue #130: 2025-11-20 - Validation failed (broke cp1252)
**Status**: PERMANENT BLOCK (3+ failures)
**Alternative**: Check sys.stdout.encoding, use UTF-8 only if supported
""", encoding='utf-8')

        checker3 = FailedExperimentChecker()
        checker3.project_log = test_log3
        decision, reason = checker3.should_apply_fix("UTF-8 encoding", 135)

        assert decision is False, f"Expected False, got {decision}"
        assert "PERMANENT BLOCK" in reason, f"Unexpected reason: {reason}"
        print(f"  [PASS] {reason}\n")

        # Test 4: Add new failure entry
        print("Test 4: Add new failure entry")
        test_log4 = test_dir / "test4.log"
        test_log4.write_text("")

        checker4 = FailedExperimentChecker()
        checker4.project_log = test_log4
        success = checker4.add_failure(
            "New problematic fix",
            140,
            "Tests failed",
            "Try different approach"
        )

        assert success, "Failed to add entry"
        content = test_log4.read_text()
        assert "New problematic fix" in content, "Fix not in log"
        assert "Issue #140" in content, "Issue number not in log"
        print(f"  [PASS] Entry added successfully\n")

        # Test 5: Parse log with multiple entries
        print("Test 5: Parse log with multiple entries")
        test_log5 = test_dir / "test5.log"
        test_log5.write_text("""
### Fix A
**Description**: First fix
**Attempts**:
  - Issue #100: 2025-11-01 - Error A
**Status**: Observed
**Alternative**: Alt A

### Fix B
**Description**: Second fix
**Attempts**:
  - Issue #101: 2025-11-02 - Error B1
  - Issue #102: 2025-11-03 - Error B2
**Status**: Warning (2 failures)
**Alternative**: Alt B
""", encoding='utf-8')

        checker5 = FailedExperimentChecker()
        experiments = checker5.parse_log(test_log5)

        assert len(experiments) == 2, f"Expected 2 experiments, got {len(experiments)}"
        assert experiments[0]['title'] == "Fix A", f"Wrong title: {experiments[0]['title']}"
        assert len(experiments[1]['attempts']) == 2, f"Expected 2 attempts, got {len(experiments[1]['attempts'])}"
        print(f"  [PASS] Parsed {len(experiments)} experiments correctly\n")

        print("="*70)
        print("ALL TESTS PASSED")
        print("="*70 + "\n")

    finally:
        # Cleanup
        shutil.rmtree(test_dir)


if __name__ == '__main__':
    # Check for test flag
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        run_tests()
    else:
        main()
