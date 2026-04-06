#!/usr/bin/env python3
"""Cross-Repo Tests for SST3 Regression Suite (Issue #133)

Tests SST3 works correctly across all repositories.
Baseline: 95% cross-repo quality (Issue #131)
"""

import sys
from pathlib import Path


class CrossRepoTests:
    """Regression tests for cross-repo SST3 functionality"""

    def __init__(self, verbose=False):
        self.verbose = verbose
        self.devprojects_root = Path(__file__).resolve().parents[3]
        self.sst3_root = self.devprojects_root / 'dotfiles' / 'SST3'
        self.results = {'total_tests': 0, 'passed_tests': 0, 'failed_tests': [], 'category': 'cross_repo'}

    def run_test(self, test_name, test_func):
        self.results['total_tests'] += 1
        try:
            passed, message = test_func()
            if passed:
                self.results['passed_tests'] += 1
                print(f"[PASS] {test_name}")
            else:
                self.results['failed_tests'].append({'name': test_name, 'reason': message})
                print(f"[FAIL] {test_name}: {message}")
        except Exception as e:
            self.results['failed_tests'].append({'name': test_name, 'reason': str(e)})
            print(f"[FAIL] {test_name}: ERROR - {str(e)}")

    def test_repos_exist(self):
        expected_repos = ['dotfiles', 'auto_pb_swing_trader', 'tradebook_GAS']
        missing = []

        for repo in expected_repos:
            repo_path = self.devprojects_root / repo
            if not repo_path.exists():
                missing.append(repo)

        if missing:
            return False, f"Missing repos: {', '.join(missing)}"

        return True, f"All {len(expected_repos)} repos exist"

    def test_relative_paths_resolve(self):
        other_repos = ['auto_pb_swing_trader', 'tradebook_GAS']
        failed_repos = []

        for repo in other_repos:
            repo_path = self.devprojects_root / repo
            sst2_path = repo_path / '..' / 'dotfiles' / 'SST3'

            if not sst2_path.exists():
                failed_repos.append(repo)

        if failed_repos:
            return False, f"Relative paths don't resolve from: {', '.join(failed_repos)}"

        return True, f"Relative paths resolve from {len(other_repos)} repos"

    def test_claude_template_exists(self):
        template_path = self.sst3_root / 'templates' / 'CLAUDE_TEMPLATE.md'
        if not template_path.exists():
            return False, "CLAUDE_TEMPLATE.md not found"

        content = template_path.read_text(encoding='utf-8')
        if 'MANDATORY READING' not in content:
            return False, "Template structure incomplete"

        return True, "CLAUDE_TEMPLATE.md structure valid"

    def test_sst2_local_support(self):
        standards_file = self.sst3_root / 'standards' / 'STANDARDS.md'
        if not standards_file.exists():
            return False, "STANDARDS.md not found"

        content = standards_file.read_text(encoding='utf-8')
        if '.sst2-local' not in content:
            return False, ".sst2-local support not documented"

        return True, ".sst2-local support documented"

    def test_multi_language_support(self):
        standards_file = self.sst3_root / 'standards' / 'STANDARDS.md'
        if not standards_file.exists():
            return False, "STANDARDS.md not found"

        content = standards_file.read_text(encoding='utf-8')
        languages = ['Python', 'JavaScript', 'TypeScript']

        found_languages = [lang for lang in languages if lang in content]

        if len(found_languages) < 2:
            return False, f"Only {len(found_languages)} languages mentioned (expected >=2)"

        return True, f"{len(found_languages)} languages supported"

    def run_all_tests(self):
        print("\n" + "="*60)
        print("CROSS-REPO TESTS")
        print("="*60 + "\n")

        self.run_test("All repos exist", self.test_repos_exist)
        self.run_test("Relative paths resolve", self.test_relative_paths_resolve)
        self.run_test("CLAUDE_TEMPLATE.md exists", self.test_claude_template_exists)
        self.run_test(".sst2-local support documented", self.test_sst2_local_support)
        self.run_test("Multi-language support", self.test_multi_language_support)

        print("\n" + "-"*60)
        passed = self.results['passed_tests']
        total = self.results['total_tests']
        percentage = (passed / total * 100) if total > 0 else 0
        print(f"Cross-Repo: {passed}/{total} tests passed ({percentage:.0f}%)")
        print("-"*60 + "\n")

        return self.results


def main():
    import argparse
    parser = argparse.ArgumentParser(description='SST3 Cross-Repo Tests')
    parser.add_argument('--verbose', '-v', action='store_true')
    args = parser.parse_args()

    tests = CrossRepoTests(verbose=args.verbose)
    results = tests.run_all_tests()
    sys.exit(0 if results['passed_tests'] == results['total_tests'] else 1)


if __name__ == '__main__':
    main()
