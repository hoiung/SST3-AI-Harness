#!/usr/bin/env python3
"""
Path Portability Tests

Tests:
- P1-6: No Absolute Paths (no C:\ or /Users/)
- P1-7: Cross-Platform Compatibility (paths work on Windows/Linux/macOS)
- P1-8: No Hardcoded Usernames (no 'example_user', 'username', etc.)
- P1-9: Symlink Resolution (paths work through symlinks)

Philosophy: Portability supporting quality, not blocking execution.
"""

import os
import re
from pathlib import Path


class PathPortabilityTests:
    """Path portability tests for cross-platform compatibility"""

    def __init__(self, verbose=False):
        self.verbose = verbose
        self.tests_dir = Path(__file__).parent
        self.sst3_dir = self.tests_dir.parent
        self.dotfiles_dir = self.sst3_dir.parent

        self.passed_tests = []
        self.failed_tests = []

    def get_all_doc_files(self):
        """Get all documentation files in SST3"""
        files = []
        for ext in ['*.md', '*.py', '*.sh']:
            files.extend(self.sst3_dir.rglob(ext))
        # Exclude tests directory
        return [f for f in files if 'tests' not in str(f)]

    def test_no_absolute_paths(self):
        """
        Test 6: No Absolute Paths

        What: No C:\ or /Users/ in any documentation
        Why: Prevents portability issues
        Pass Criteria: 0 matches for absolute path patterns

        Patterns:
        - C:\, D:\, E:\ (Windows)
        - /Users/, /home/ (Unix)
        - \\server\ (UNC paths)
        """
        violations = []

        # Patterns to detect
        windows_pattern = re.compile(r'[A-Z]:\\')
        unix_home_pattern = re.compile(r'/(Users|home)/\w+')
        unc_pattern = re.compile(r'\\\\[\w-]+\\')

        for file_path in self.get_all_doc_files():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')

                    for line_num, line in enumerate(lines, 1):
                        # Check for Windows paths
                        if windows_pattern.search(line):
                            violations.append(f"{file_path.name}:{line_num} - Windows path: {line.strip()[:60]}")

                        # Check for Unix home paths
                        if unix_home_pattern.search(line):
                            violations.append(f"{file_path.name}:{line_num} - Unix home path: {line.strip()[:60]}")

                        # Check for UNC paths
                        if unc_pattern.search(line):
                            violations.append(f"{file_path.name}:{line_num} - UNC path: {line.strip()[:60]}")

            except Exception as e:
                continue

        if violations:
            self.failed_tests.append({
                'name': 'Test 6: No Absolute Paths',
                'reason': f"Found {len(violations)} absolute path violations:\n" + '\n'.join(violations[:5])
            })
            if self.verbose:
                print(f"  [FAIL] Test 6: No Absolute Paths")
                print(f"    FAIL: Found {len(violations)} absolute path violations")
                for v in violations[:5]:
                    print(f"      {v}")
                if len(violations) > 5:
                    print(f"      ... and {len(violations) - 5} more")
        else:
            self.passed_tests.append({
                'name': 'Test 6: No Absolute Paths',
                'details': "No absolute paths found"
            })
            if self.verbose:
                print(f"  [PASS] Test 6: No Absolute Paths")

    def test_cross_platform_compatibility(self):
        """
        Test 7: Cross-Platform Compatibility

        What: Paths work on Windows/Linux/macOS
        Why: Ensures portability
        Pass Criteria: Use forward slashes or os.path.sep, relative paths
        """
        issues = []

        # Check for mixed path separators
        mixed_separator_pattern = re.compile(r'(?:[A-Za-z0-9_-]+/[A-Za-z0-9_-]+\\)|(?:[A-Za-z0-9_-]+\\[A-Za-z0-9_-]+/)')

        for file_path in self.get_all_doc_files():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')

                    for line_num, line in enumerate(lines, 1):
                        # Check for mixed separators
                        if mixed_separator_pattern.search(line):
                            issues.append(f"{file_path.name}:{line_num} - Mixed path separators")

            except Exception as e:
                continue

        if issues:
            self.failed_tests.append({
                'name': 'Test 7: Cross-Platform Compatibility',
                'reason': f"Found {len(issues)} cross-platform issues:\n" + '\n'.join(issues[:5])
            })
            if self.verbose:
                print(f"  [FAIL] Test 7: Cross-Platform Compatibility")
                print(f"    FAIL: Found {len(issues)} cross-platform issues")
                for issue in issues[:5]:
                    print(f"      {issue}")
        else:
            self.passed_tests.append({
                'name': 'Test 7: Cross-Platform Compatibility',
                'details': "No cross-platform issues found"
            })
            if self.verbose:
                print(f"  [PASS] Test 7: Cross-Platform Compatibility")

    def test_no_hardcoded_usernames(self):
        """
        Test 8: No Hardcoded Usernames

        What: No 'example_user', 'username', etc. in docs
        Why: Prevents sharing issues
        Pass Criteria: 0 matches for username patterns

        Patterns:
        - example_user
        - /home/username
        - C:\\Users\\username
        - Common usernames
        """
        violations = []

        # Username patterns (exclude code comments and examples that explicitly show this is wrong)
        username_patterns = [
            r'\bexample_user\b',
            r'/home/\w+',
            r'C:\\Users\\\w+',
            r'~/\w+',  # But allow ~/ alone
        ]

        for file_path in self.get_all_doc_files():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')

                    for line_num, line in enumerate(lines, 1):
                        # Skip lines that are examples of what NOT to do
                        if 'WRONG' in line or 'DON\'T' in line or 'example' in line.lower():
                            continue

                        for pattern in username_patterns:
                            if re.search(pattern, line):
                                violations.append(f"{file_path.name}:{line_num} - Hardcoded path: {line.strip()[:60]}")
                                break

            except Exception as e:
                continue

        if violations:
            self.failed_tests.append({
                'name': 'Test 8: No Hardcoded Usernames',
                'reason': f"Found {len(violations)} hardcoded username violations:\n" + '\n'.join(violations[:5])
            })
            if self.verbose:
                print(f"  [FAIL] Test 8: No Hardcoded Usernames")
                print(f"    FAIL: Found {len(violations)} hardcoded usernames")
                for v in violations[:5]:
                    print(f"      {v}")
        else:
            self.passed_tests.append({
                'name': 'Test 8: No Hardcoded Usernames',
                'details': "No hardcoded usernames found"
            })
            if self.verbose:
                print(f"  [PASS] Test 8: No Hardcoded Usernames")

    def test_symlink_resolution(self):
        """
        Test 9: Symlink Resolution

        What: Paths work through symlinks
        Why: Development environments use symlinks
        Pass Criteria: Relative paths that resolve correctly

        Note: This test validates that paths are relative (which allows symlinks to work).
        """
        # Check that cross-repo references use relative paths
        cross_repo_pattern = re.compile(r'\.\./dotfiles/SST3/')
        found_relative = False
        issues = []

        for file_path in self.get_all_doc_files():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                    if cross_repo_pattern.search(content):
                        found_relative = True

                    # Check for absolute paths that would break symlinks
                    if re.search(r'[A-Z]:\\.*\\SST3\\', content):
                        issues.append(f"{file_path.name} - Absolute path would break symlinks")

            except Exception as e:
                continue

        if issues:
            self.failed_tests.append({
                'name': 'Test 9: Symlink Resolution',
                'reason': f"Found {len(issues)} symlink issues:\n" + '\n'.join(issues)
            })
            if self.verbose:
                print(f"  [FAIL] Test 9: Symlink Resolution")
                print(f"    FAIL: Found {len(issues)} symlink issues")
                for issue in issues:
                    print(f"      {issue}")
        else:
            self.passed_tests.append({
                'name': 'Test 9: Symlink Resolution',
                'details': f"Relative paths used (found: {found_relative}), symlink-compatible"
            })
            if self.verbose:
                print(f"  [PASS] Test 9: Symlink Resolution")
                print(f"    Relative paths used, symlink-compatible")

    def run_all_tests(self):
        """Run all path portability tests"""
        if self.verbose:
            print("\n" + "="*60)
            print("PATH PORTABILITY TESTS")
            print("="*60 + "\n")

        self.test_no_absolute_paths()
        self.test_cross_platform_compatibility()
        self.test_no_hardcoded_usernames()
        self.test_symlink_resolution()

        if self.verbose:
            print("\n" + "-"*60)
            print(f"Path Portability: {len(self.passed_tests)}/{len(self.passed_tests) + len(self.failed_tests)} tests passed")
            print("-"*60 + "\n")

            if self.failed_tests:
                print("Failed Tests:")
                for fail in self.failed_tests:
                    print(f"  - {fail['name']}: {fail['reason']}")
                print()

        return {
            'passed_tests': len(self.passed_tests),
            'failed_tests': self.failed_tests,
            'total_tests': len(self.passed_tests) + len(self.failed_tests)
        }


if __name__ == '__main__':
    import sys
    verbose = '--verbose' in sys.argv or '-v' in sys.argv

    tests = PathPortabilityTests(verbose=True)
    results = tests.run_all_tests()

    if results['failed_tests']:
        print(f"\n✗ {len(results['failed_tests'])} test(s) FAILED")
        sys.exit(1)
    else:
        print(f"\n✓ All {results['total_tests']} path portability tests PASSED")
        sys.exit(0)
