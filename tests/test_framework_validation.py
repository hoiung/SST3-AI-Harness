#!/usr/bin/env python3
"""
Framework Validation Tests

Tests:
- P2-34: Self-Healing Framework (validation protocol exists)
- P2-36: Failed Experiments Tracking (failed experiments logged)

Philosophy: Framework validation for robustness.
"""

import re
from pathlib import Path


class FrameworkValidationTests:
    """Framework validation tests"""

    def __init__(self, verbose=False):
        self.verbose = verbose
        self.tests_dir = Path(__file__).parent
        self.sst3_dir = self.tests_dir.parent
        self.dotfiles_dir = self.sst3_dir.parent

        self.passed_tests = []
        self.failed_tests = []

    def test_self_healing_framework(self):
        """
        Test 34: Self-Healing Framework

        What: Validation protocol exists (Issue #132)
        Why: Ensures self-healing patterns work
        Pass Criteria: self-healing-guide.md has validation protocol

        Requirements:
        - VALIDATING marker process
        - 3-issue test requirement
        - Scenario coverage (≥10 scenarios)
        """
        healing_guide = self.sst3_dir / 'reference' / 'self-healing-guide.md'

        if not healing_guide.exists():
            self.failed_tests.append({
                'name': 'Test 34: Self-Healing Framework',
                'reason': "self-healing-guide.md not found"
            })
            if self.verbose:
                print(f"  [FAIL] Test 34: Self-Healing Framework")
                print(f"    FAIL: self-healing-guide.md not found")
            return

        content = healing_guide.read_text(encoding='utf-8')

        # Check for VALIDATING marker
        if 'VALIDATING' not in content:
            self.failed_tests.append({
                'name': 'Test 34: Self-Healing Framework',
                'reason': "No VALIDATING marker process documented"
            })
            if self.verbose:
                print(f"  [FAIL] Test 34: Self-Healing Framework")
                print(f"    FAIL: No VALIDATING marker")
            return

        # Check for 3-issue test requirement
        if not re.search(r'3.*issue|three.*issue', content, re.IGNORECASE):
            self.failed_tests.append({
                'name': 'Test 34: Self-Healing Framework',
                'reason': "No 3-issue test requirement documented"
            })
            if self.verbose:
                print(f"  [FAIL] Test 34: Self-Healing Framework")
                print(f"    FAIL: No 3-issue test requirement")
            return

        # Check for scenario coverage (count scenario headers)
        scenario_count = len(re.findall(r'##\s+Scenario', content, re.IGNORECASE))

        if scenario_count < 10:
            self.failed_tests.append({
                'name': 'Test 34: Self-Healing Framework',
                'reason': f"Only {scenario_count} scenarios (expected ≥10)"
            })
            if self.verbose:
                print(f"  [FAIL] Test 34: Self-Healing Framework")
                print(f"    FAIL: Only {scenario_count} scenarios")
        else:
            self.passed_tests.append({
                'name': 'Test 34: Self-Healing Framework',
                'details': f"Self-healing framework complete ({scenario_count} scenarios)"
            })
            if self.verbose:
                print(f"  [PASS] Test 34: Self-Healing Framework")
                print(f"    {scenario_count} scenarios, VALIDATING marker, 3-issue test")

    def test_failed_experiments_tracking(self):
        """
        Test 36: Failed Experiments Tracking

        What: Failed experiments logged
        Why: Learn from failures
        Pass Criteria: Documentation references failed experiments

        Requirements:
        - Failed experiments section exists
        - Lessons learned documented
        - Anti-patterns identified
        """
        # Check for failed experiments documentation
        docs_to_check = [
            self.sst3_dir / 'reference' / 'self-healing-guide.md',
            self.sst3_dir / 'reference' / 'failed-experiments.md',
            self.sst3_dir / 'workflow' / 'WORKFLOW.md',
        ]

        experiments_documented = False
        found_in = None

        for doc_file in docs_to_check:
            if doc_file.exists():
                content = doc_file.read_text(encoding='utf-8')

                # Check for failed experiments section
                patterns = [
                    r'failed.*experiment',
                    r'what.*didn.*work',
                    r'anti.*pattern',
                    r'lessons.*learned',
                ]

                for pattern in patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        experiments_documented = True
                        found_in = doc_file.name
                        break

                if experiments_documented:
                    break

        if not experiments_documented:
            self.failed_tests.append({
                'name': 'Test 36: Failed Experiments Tracking',
                'reason': "No failed experiments documentation found"
            })
            if self.verbose:
                print(f"  [FAIL] Test 36: Failed Experiments Tracking")
                print(f"    FAIL: No failed experiments documented")
        else:
            # Count number of experiments/lessons
            content = doc_file.read_text(encoding='utf-8')
            experiment_count = len(re.findall(r'##\s+.*(?:failed|anti|lesson)', content, re.IGNORECASE))

            self.passed_tests.append({
                'name': 'Test 36: Failed Experiments Tracking',
                'details': f"Failed experiments documented in {found_in} ({experiment_count} entries)"
            })
            if self.verbose:
                print(f"  [PASS] Test 36: Failed Experiments Tracking")
                print(f"    {experiment_count} failed experiments/lessons in {found_in}")

    def run_all_tests(self):
        """Run all framework validation tests"""
        if self.verbose:
            print("\n" + "="*60)
            print("FRAMEWORK VALIDATION TESTS")
            print("="*60 + "\n")

        self.test_self_healing_framework()
        self.test_failed_experiments_tracking()

        if self.verbose:
            print("\n" + "-"*60)
            print(f"Framework Validation: {len(self.passed_tests)}/{len(self.passed_tests) + len(self.failed_tests)} tests passed")
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

    tests = FrameworkValidationTests(verbose=True)
    results = tests.run_all_tests()

    if results['failed_tests']:
        print(f"\n✗ {len(results['failed_tests'])} test(s) FAILED")
        sys.exit(1)
    else:
        print(f"\n✓ All {results['total_tests']} framework validation tests PASSED")
        sys.exit(0)
