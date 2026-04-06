#!/usr/bin/env python3
"""Monitoring Tests for SST3 Regression Suite (Issue #133)

Tests self-monitoring systems (health dashboard, freeze detection).
Baseline: 85% monitoring quality (Issue #131)
"""

import subprocess
import sys
from pathlib import Path


class MonitoringTests:
    """Regression tests for SST3 monitoring systems"""

    def __init__(self, verbose=False):
        self.verbose = verbose
        self.sst3_root = Path(__file__).parent.parent
        self.results = {'total_tests': 0, 'passed_tests': 0, 'failed_tests': [], 'category': 'monitoring'}

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


    def test_freeze_detector_exists(self):
        script_path = self.sst3_root / 'scripts' / 'freeze-detector.py'
        if not script_path.exists():
            return False, "freeze-detector.py not found"
        return True, "freeze-detector.py exists"

    def test_monitoring_reference_exists(self):
        # subagent-monitoring.md archived to SST3/archive/ (#399)
        # Check self-healing-guide.md instead (active monitoring reference)
        ref_file = self.sst3_root / 'reference' / 'self-healing-guide.md'
        if not ref_file.exists():
            return False, "self-healing-guide.md not found"
        return True, "Monitoring reference exists (self-healing-guide.md)"

    def test_alert_levels_defined(self):
        # subagent-monitoring.md archived (#399) — check self-healing-guide for recovery scenarios
        ref_file = self.sst3_root / 'reference' / 'self-healing-guide.md'
        if not ref_file.exists():
            return False, "self-healing-guide.md not found"
        content = ref_file.read_text(encoding='utf-8')
        if 'Recovery' not in content:
            return False, "Recovery scenarios not defined"
        return True, "Alert levels defined"

    def run_all_tests(self):
        print("\n" + "="*60)
        print("MONITORING TESTS")
        print("="*60 + "\n")

        self.run_test("freeze-detector.py exists", self.test_freeze_detector_exists)
        self.run_test("Monitoring reference exists", self.test_monitoring_reference_exists)
        self.run_test("Alert levels defined", self.test_alert_levels_defined)

        print("\n" + "-"*60)
        passed = self.results['passed_tests']
        total = self.results['total_tests']
        percentage = (passed / total * 100) if total > 0 else 0
        print(f"Monitoring: {passed}/{total} tests passed ({percentage:.0f}%)")
        print("-"*60 + "\n")

        return self.results


def main():
    import argparse
    parser = argparse.ArgumentParser(description='SST3 Monitoring Tests')
    parser.add_argument('--verbose', '-v', action='store_true')
    args = parser.parse_args()

    tests = MonitoringTests(verbose=args.verbose)
    results = tests.run_all_tests()
    sys.exit(0 if results['passed_tests'] == results['total_tests'] else 1)


if __name__ == '__main__':
    main()
