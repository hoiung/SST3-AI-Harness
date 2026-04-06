#!/usr/bin/env python3
"""
Discoverability Tests for SST3 Regression Suite (Issue #133)

Tests that all SST3 files are discoverable from CLAUDE.md in ALL repos.
Extends SST3/scripts/check-discoverability.py with regression test framework.

Test Categories:
1. Entry points (CLAUDE.md exists in all repos)
2. SST3 references (CLAUDE.md → SST3)
3. File discoverability (100% of SST3 files reachable)
4. Discovery chain length (≤4 steps)
5. Cross-repo paths (../dotfiles/SST3/ works)
6. No broken references

Baseline: 100% discoverability (Issue #131)
"""

import sys
from pathlib import Path

# Add scripts directory to path to import DiscoverabilityChecker
scripts_dir = Path(__file__).parent.parent / 'scripts'
sys.path.insert(0, str(scripts_dir))

# Import using importlib since filename has hyphens
import importlib.util
spec = importlib.util.spec_from_file_location("check_discoverability", scripts_dir / "check-discoverability.py")
check_disc_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_disc_module)
DiscoverabilityChecker = check_disc_module.DiscoverabilityChecker


class DiscoverabilityTests:
    """Regression tests for SST3 discoverability"""

    def __init__(self, verbose=False):
        self.verbose = verbose
        self.checker = DiscoverabilityChecker(verbose=verbose)
        self.results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': [],
            'category': 'discoverability'
        }

    def log(self, message):
        if self.verbose:
            print(f"  [TEST] {message}")

    def run_test(self, test_name, test_func):
        """Run a single test and track results"""
        self.results['total_tests'] += 1
        self.log(f"Running: {test_name}")

        try:
            passed, message = test_func()
            if passed:
                self.results['passed_tests'] += 1
                print(f"[PASS] {test_name}")
                if message:
                    print(f"  {message}")
            else:
                self.results['failed_tests'].append({
                    'name': test_name,
                    'reason': message
                })
                print(f"[FAIL] {test_name}")
                print(f"  FAIL: {message}")
            return passed
        except Exception as e:
            self.results['failed_tests'].append({
                'name': test_name,
                'reason': f"Exception: {str(e)}"
            })
            print(f"[FAIL] {test_name}")
            print(f"  ERROR: {str(e)}")
            return False

    def test_claude_md_exists_all_repos(self):
        """Test 1: CLAUDE.md exists in all repos"""
        self.checker.repos = self.checker.discover_repos()

        if len(self.checker.repos) < 3:
            return False, f"Expected 3 repos, found {len(self.checker.repos)}"

        repo_names = [r['name'] for r in self.checker.repos]
        expected = ['dotfiles', 'auto_pb_swing_trader', 'tradebook_GAS']

        for expected_repo in expected:
            if expected_repo not in repo_names:
                return False, f"Missing repo: {expected_repo}"

        return True, f"Found {len(self.checker.repos)} repos: {', '.join(repo_names)}"

    def test_claude_references_sst2(self):
        """Test 2: All CLAUDE.md files reference SST3"""
        all_valid = True
        invalid_repos = []

        for repo in self.checker.repos:
            valid, line_num = self.checker.validate_entry_point(repo)
            if not valid:
                all_valid = False
                invalid_repos.append(repo['name'])

        if not all_valid:
            return False, f"Repos without SST3 reference: {', '.join(invalid_repos)}"

        return True, f"All {len(self.checker.repos)} repos reference SST3"

    def test_all_files_discoverable(self):
        """Test 3: 100% of SST3 files are discoverable from all repos"""
        self.checker.features = self.checker.discover_sst3_features()
        total_features = len(self.checker.features)
        total_paths = total_features * len(self.checker.repos)
        valid_paths = 0
        undiscoverable = []

        for feature in self.checker.features:
            feature_discoverable = False
            for repo in self.checker.repos:
                path = self.checker.trace_discovery_path(repo, feature)
                if path:
                    valid_paths += 1
                    feature_discoverable = True

            if not feature_discoverable:
                feature_rel = feature.relative_to(self.checker.dotfiles_root)
                undiscoverable.append(str(feature_rel))

        percentage = (valid_paths / total_paths * 100) if total_paths > 0 else 0

        if percentage < 100:
            return False, f"Only {percentage:.1f}% discoverable. Missing: {', '.join(undiscoverable[:3])}"

        return True, f"{valid_paths}/{total_paths} paths discoverable (100%)"

    def test_discovery_chain_length(self):
        """Test 4: All features discoverable within 4 steps from CLAUDE.md"""
        max_steps = 0
        long_chains = []

        for feature in self.checker.features:
            for repo in self.checker.repos:
                path = self.checker.trace_discovery_path(repo, feature)
                if path:
                    steps = len(path) - 1  # Don't count starting point
                    if steps > max_steps:
                        max_steps = steps
                    if steps > 4:
                        feature_rel = feature.relative_to(self.checker.dotfiles_root)
                        long_chains.append(f"{str(feature_rel)} ({steps} steps)")

        if long_chains:
            return False, f"Features with >4 steps: {', '.join(long_chains[:3])}"

        return True, f"Max chain length: {max_steps} steps (<=4 required)"

    def test_cross_repo_paths_resolve(self):
        """Test 5: ../dotfiles/SST3/ paths resolve from other repos"""
        non_dotfiles_repos = [r for r in self.checker.repos if r['name'] != 'dotfiles']

        if not non_dotfiles_repos:
            return False, "No non-dotfiles repos to test cross-repo paths"

        all_resolve = True
        failed_repos = []

        for repo in non_dotfiles_repos:
            # Check if relative path to SST3 exists
            sst2_path = repo['root'] / '..' / 'dotfiles' / 'SST3'
            if not sst2_path.exists():
                all_resolve = False
                failed_repos.append(repo['name'])

        if not all_resolve:
            return False, f"Repos where ../dotfiles/SST3/ doesn't resolve: {', '.join(failed_repos)}"

        return True, f"Cross-repo paths resolve in {len(non_dotfiles_repos)} repos"

    def test_no_broken_references(self):
        """Test 6: No broken references in discovery chain"""
        broken_refs = []

        # Check workflow files for broken references
        workflow_dir = self.checker.sst3_root / 'workflow'
        for md_file in workflow_dir.glob('*.md'):
            content = md_file.read_text(encoding='utf-8')

            # Find all markdown links
            import re
            links = re.findall(r'\[([^\]]+)\]\(([^\)]+)\)', content)

            for link_text, link_path in links:
                # Skip external URLs
                if link_path.startswith('http'):
                    continue

                # Check if referenced file exists
                if link_path.startswith('../'):
                    ref_file = md_file.parent / link_path
                else:
                    ref_file = md_file.parent / link_path

                if not ref_file.exists():
                    broken_refs.append(f"{md_file.name}: {link_path}")

        if broken_refs:
            return False, f"Broken references: {', '.join(broken_refs[:3])}"

        return True, "No broken references found"

    def run_all_tests(self):
        """Run all discoverability tests"""
        print("\n" + "="*60)
        print("DISCOVERABILITY TESTS")
        print("="*60 + "\n")

        # Discover repos and features first
        self.checker.repos = self.checker.discover_repos()
        self.checker.features = self.checker.discover_sst3_features()

        # Run tests
        self.run_test("CLAUDE.md exists in all repos", self.test_claude_md_exists_all_repos)
        self.run_test("All CLAUDE.md reference SST3", self.test_claude_references_sst2)
        self.run_test("100% of files discoverable", self.test_all_files_discoverable)
        self.run_test("Discovery chain <=4 steps", self.test_discovery_chain_length)
        self.run_test("Cross-repo paths resolve", self.test_cross_repo_paths_resolve)
        self.run_test("No broken references", self.test_no_broken_references)

        # Summary
        print("\n" + "-"*60)
        passed = self.results['passed_tests']
        total = self.results['total_tests']
        percentage = (passed / total * 100) if total > 0 else 0

        print(f"Discoverability: {passed}/{total} tests passed ({percentage:.0f}%)")

        if self.results['failed_tests']:
            print("\nFailed Tests:")
            for fail in self.results['failed_tests']:
                print(f"  - {fail['name']}: {fail['reason']}")

        print("-"*60 + "\n")

        return self.results


def main():
    """Run discoverability tests standalone"""
    import argparse
    parser = argparse.ArgumentParser(description='SST3 Discoverability Tests')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    args = parser.parse_args()

    tests = DiscoverabilityTests(verbose=args.verbose)
    results = tests.run_all_tests()

    # Exit with appropriate code
    if results['passed_tests'] == results['total_tests']:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
