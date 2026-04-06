#!/usr/bin/env python3
"""
Cross-Repo Path Validation Prevention for SST3 (Issue #298)

Purpose:
- Prevent SST3 markdown files from using relative paths that break cross-repo references
- Ensure all SST3 file references use ../dotfiles/SST3/ prefix for discoverability
- Catch patterns like `SST3/`, `../templates/`, `../workflow/` that should be `../dotfiles/SST3/...`

Problem Solved:
When SST3 docs reference other SST3 files using repo-relative paths (e.g., `SST3/workflow/...`),
those paths work from dotfiles repo but BREAK from other repos (auto_pb_swing_trader, tradebook_GAS).
This makes SST3 features undiscoverable from other repos, violating the discoverability requirement.

Correct Pattern:
- From dotfiles repo: `SST3/workflow/WORKFLOW.md` (repo-relative)
- From other repos: `../dotfiles/SST3/workflow/WORKFLOW.md` (cross-repo)
- SST3 docs should use: `../dotfiles/SST3/workflow/WORKFLOW.md` (works everywhere)

Exceptions:
- CLAUDE_TEMPLATE.md: Intentionally uses repo-relative paths (template for other repos)
- Code blocks showing "wrong" examples (prefixed with ❌ or "DON'T:")
- Paths already using `../dotfiles/SST3/` (correct format)

Usage:
  python SST3/scripts/check-crossrepo-paths.py                # Check for violations
  python SST3/scripts/check-crossrepo-paths.py --fix          # Show suggested fixes (dry-run)
  python SST3/scripts/check-crossrepo-paths.py --verbose      # Verbose output

Exit codes:
  0: No violations found
  1: Violations found (BLOCKS commit)
"""

import argparse
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional


class CrossRepoPathChecker:
    """Validates cross-repo path format in SST3 markdown files."""

    def __init__(self, verbose: bool = False):
        """
        Initialize path checker.

        Args:
            verbose: Enable verbose output
        """
        self.verbose = verbose
        self.dotfiles_root = Path(__file__).resolve().parents[2]  # Go up to dotfiles
        self.sst3_root = self.dotfiles_root / "SST3"

        # Track violations
        self.violations: List[Dict] = []

        # Patterns to catch (backticked paths referencing SST3 files)
        # Match backticked paths like `SST3/...`, `../templates/...`, etc.
        self.violation_patterns = [
            r'`SST3/(workflow|templates|reference|standards|scripts)/',
            r'`\.\./workflow/',
            r'`\.\./templates/',
            r'`\.\./reference/',
            r'`\.\./standards/',
            r'`\.\./scripts/',
        ]

        # Exception patterns (paths that are correct)
        self.exception_patterns = [
            r'`\.\./dotfiles/SST3/',  # Already correct format
            r'`SST3-metrics/',        # SST3-metrics folder (not SST3)
            r'`\.\./DevProjects/',    # DevProjects references
        ]

        # Files to exclude from validation
        self.excluded_files = {
            'CLAUDE_TEMPLATE.md',  # Template uses repo-relative paths intentionally
        }

    def log(self, message: str):
        """Log verbose output."""
        if self.verbose:
            print(f"  [DEBUG] {message}")

    def is_in_wrong_example_block(self, lines: List[str], line_idx: int) -> bool:
        """
        Check if the line is in a "wrong example" code block.

        Args:
            lines: All lines in the file
            line_idx: Current line index (0-based)

        Returns:
            True if line is in a wrong example block, False otherwise
        """
        # Look backwards for context markers (❌, "DON'T:", "BAD:", etc.)
        context_window = 5  # Lines to check before current line
        start_idx = max(0, line_idx - context_window)

        for i in range(start_idx, line_idx + 1):
            line = lines[i]
            # Check for wrong example markers
            if any(marker in line for marker in ['❌', '✗', "DON'T:", "BAD:", "WRONG:"]):
                self.log(f"Line {line_idx + 1} is in wrong example block (marker at line {i + 1})")
                return True

        return False

    def check_file(self, file_path: Path) -> List[Dict]:
        """
        Check a single markdown file for cross-repo path violations.

        Args:
            file_path: Path to markdown file

        Returns:
            List of violations found
        """
        if file_path.name in self.excluded_files:
            self.log(f"Skipping excluded file: {file_path.name}")
            return []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
        except Exception as e:
            print(f"ERROR: Could not read {file_path}: {e}")
            return []

        violations = []
        # #406 Phase 9: pre-commit passes RELATIVE paths (e.g. SST3/foo.md);
        # `Path('SST3/foo.md').relative_to('/home/.../dotfiles')` raises
        # ValueError. Resolve to absolute first.
        relative_path = file_path.resolve().relative_to(self.dotfiles_root)

        for line_num, line in enumerate(lines, 1):
            # Skip if in wrong example block
            if self.is_in_wrong_example_block(lines, line_num - 1):
                continue

            # Check for exception patterns first (correct format)
            is_exception = False
            for exception_pattern in self.exception_patterns:
                if re.search(exception_pattern, line):
                    is_exception = True
                    break

            if is_exception:
                continue

            # Check for violation patterns
            for violation_pattern in self.violation_patterns:
                matches = re.finditer(violation_pattern, line)
                for match in matches:
                    # Extract the full path (until closing backtick)
                    # Pattern includes opening backtick, so match.start() is where backtick is
                    backtick_start = match.start()
                    backtick_end = line.find('`', match.end())

                    if backtick_end == -1:
                        continue

                    wrong_path = line[backtick_start + 1:backtick_end]

                    # Skip if already has ../dotfiles/ prefix
                    if wrong_path.startswith('../dotfiles/'):
                        continue

                    # Generate correct path
                    if wrong_path.startswith('SST3/'):
                        correct_path = f"../dotfiles/{wrong_path}"
                    elif wrong_path.startswith('../'):
                        # Paths like ../workflow/ should be ../dotfiles/SST3/workflow/
                        relative_part = wrong_path[3:]  # Remove ../
                        correct_path = f"../dotfiles/SST3/{relative_part}"
                    else:
                        correct_path = f"../dotfiles/SST3/{wrong_path}"

                    violations.append({
                        'file': str(relative_path),
                        'line': line_num,
                        'wrong_path': wrong_path,
                        'correct_path': correct_path,
                        'line_content': line.strip()
                    })

        return violations

    def check_all_files(self, files: Optional[List[Path]] = None) -> List[Dict]:
        """
        Check markdown files for cross-repo path violations.

        Args:
            files: Optional explicit file list (from pre-commit pass_filenames).
                   If None or empty, scans all SST3 doc directories (manual run).
                   dotfiles#406 F1.16: honor pre-commit pass_filenames instead
                   of always rescanning all 4 directories.

        Returns:
            List of all violations found
        """
        all_violations = []

        if files:
            self.log(f"Scanning {len(files)} file(s) from argv")
            for md_file in files:
                if not md_file.exists() or md_file.suffix != '.md':
                    continue
                self.log(f"Checking {md_file}")
                all_violations.extend(self.check_file(md_file))
            return all_violations

        self.log("Scanning all SST3 markdown directories (manual run)...")
        directories = [
            self.sst3_root / 'workflow',
            self.sst3_root / 'templates',
            self.sst3_root / 'reference',
            self.sst3_root / 'standards',
        ]

        for directory in directories:
            if not directory.exists():
                self.log(f"Directory not found: {directory}")
                continue

            for md_file in directory.glob('*.md'):
                self.log(f"Checking {md_file.relative_to(self.dotfiles_root)}")
                violations = self.check_file(md_file)
                all_violations.extend(violations)

        return all_violations

    def print_violations(self, violations: List[Dict], show_fixes: bool = False):
        """
        Print violations in a readable format.

        Args:
            violations: List of violations to print
            show_fixes: If True, show suggested fixes
        """
        if not violations:
            print("[OK] No cross-repo path violations found")
            return

        print(f"[FAIL] Found {len(violations)} cross-repo path violation(s):")
        print()

        # Group violations by file
        by_file = {}
        for v in violations:
            file = v['file']
            if file not in by_file:
                by_file[file] = []
            by_file[file].append(v)

        for file, file_violations in sorted(by_file.items()):
            print(f"File: {file}")
            for v in file_violations:
                print(f"  Line {v['line']}: `{v['wrong_path']}`")
                if show_fixes:
                    print(f"    Should be: `{v['correct_path']}`")
                    print(f"    Context: {v['line_content'][:80]}...")
            print()

        if show_fixes:
            print("Suggested Fixes:")
            print("-" * 50)
            for file, file_violations in sorted(by_file.items()):
                print(f"\n{file}:")
                for v in file_violations:
                    print(f"  Line {v['line']}: Replace `{v['wrong_path']}` with `{v['correct_path']}`")
        else:
            print("Run with --fix to see suggested corrections")

    def validate(self, show_fixes: bool = False, files: Optional[List[Path]] = None) -> bool:
        """
        Run validation and report results.

        Args:
            show_fixes: If True, show suggested fixes
            files: Optional explicit file list from argv (pre-commit pass_filenames)

        Returns:
            True if no violations found, False otherwise
        """
        print("Cross-Repo Path Validation Check")
        print("=" * 50)
        print()

        violations = self.check_all_files(files=files)
        self.violations = violations

        self.print_violations(violations, show_fixes)

        return len(violations) == 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Cross-Repo Path Validation Prevention for SST3',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python SST3/scripts/check-crossrepo-paths.py           # Check for violations
  python SST3/scripts/check-crossrepo-paths.py --fix     # Show suggested fixes
  python SST3/scripts/check-crossrepo-paths.py -v        # Verbose output

Exit Codes:
  0: No violations found
  1: Violations found (blocks commit)
        """
    )
    parser.add_argument(
        '--fix',
        action='store_true',
        help='Show suggested fixes for violations (dry-run, does not modify files)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    parser.add_argument(
        'files', nargs='*',
        help='Optional file list (from pre-commit pass_filenames). '
             'If empty, scans all SST3 doc directories.'
    )

    args = parser.parse_args()

    file_list = [Path(f) for f in args.files] if args.files else None

    checker = CrossRepoPathChecker(verbose=args.verbose)
    success = checker.validate(show_fixes=args.fix, files=file_list)

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
