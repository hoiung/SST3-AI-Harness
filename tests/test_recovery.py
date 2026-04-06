#!/usr/bin/env python3
"""Recovery Tests for SST3 Regression Suite (Issue #133)

Tests self-healing and recovery playbooks.
Baseline: 90% recovery quality (Issue #131)
"""

import re
import sys
from pathlib import Path


class RecoveryTests:
    """Regression tests for SST3 recovery systems"""

    def __init__(self, verbose=False):
        self.verbose = verbose
        self.sst3_root = Path(__file__).parent.parent
        self.results = {'total_tests': 0, 'passed_tests': 0, 'failed_tests': [], 'category': 'recovery'}

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

    def test_self_healing_guide_exists(self):
        guide_file = self.sst3_root / 'reference' / 'self-healing-guide.md'
        if not guide_file.exists():
            return False, "self-healing-guide.md not found"
        return True, "Self-healing guide exists"

    def test_self_healing_scenarios_count(self):
        guide_file = self.sst3_root / 'reference' / 'self-healing-guide.md'
        if not guide_file.exists():
            return False, "self-healing-guide.md not found"

        content = guide_file.read_text(encoding='utf-8')
        scenarios = len(re.findall(r'###?\s+Scenario\s+\d+', content, re.IGNORECASE))

        if scenarios < 10:
            return False, f"Only {scenarios} scenarios (expected >=10)"
        return True, f"{scenarios} scenarios documented"

    def test_auto_rollback_script_exists(self):
        script_path = self.sst3_root / 'scripts' / 'auto-rollback.py'
        if not script_path.exists():
            return False, "auto-rollback.py not found"
        return True, "auto-rollback.py exists"

    def test_failed_experiments_tracking(self):
        ref_file = self.sst3_root / 'reference' / 'failed-experiments.md'
        if not ref_file.exists():
            return False, "failed-experiments.md not found"
        return True, "Failed experiments tracking exists"

    def test_recovery_playbooks_present(self):
        guide_file = self.sst3_root / 'reference' / 'self-healing-guide.md'
        if not guide_file.exists():
            return False, "self-healing-guide.md not found"

        content = guide_file.read_text(encoding='utf-8')
        if 'playbook' not in content.lower() and 'recovery' not in content.lower():
            return False, "Recovery playbooks not present"
        return True, "Recovery playbooks present"

    def run_all_tests(self):
        print("\n" + "="*60)
        print("RECOVERY TESTS")
        print("="*60 + "\n")

        self.run_test("Self-healing guide exists", self.test_self_healing_guide_exists)
        self.run_test(">=10 self-healing scenarios", self.test_self_healing_scenarios_count)
        self.run_test("auto-rollback.py exists", self.test_auto_rollback_script_exists)
        self.run_test("Failed experiments tracking", self.test_failed_experiments_tracking)
        self.run_test("Recovery playbooks present", self.test_recovery_playbooks_present)

        print("\n" + "-"*60)
        passed = self.results['passed_tests']
        total = self.results['total_tests']
        percentage = (passed / total * 100) if total > 0 else 0
        print(f"Recovery: {passed}/{total} tests passed ({percentage:.0f}%)")
        print("-"*60 + "\n")

        return self.results


def main():
    import argparse
    parser = argparse.ArgumentParser(description='SST3 Recovery Tests')
    parser.add_argument('--verbose', '-v', action='store_true')
    args = parser.parse_args()

    tests = RecoveryTests(verbose=args.verbose)
    results = tests.run_all_tests()
    sys.exit(0 if results['passed_tests'] == results['total_tests'] else 1)


if __name__ == '__main__':
    main()
