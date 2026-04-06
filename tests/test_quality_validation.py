#!/usr/bin/env python3
"""Quality Validation Tests for SST3 Regression Suite (Issue #133)

Tests 5-dimension quality framework and anti-patterns.
Baseline: 90% quality validation (Issue #131)
"""

import sys
from pathlib import Path


class QualityValidationTests:
    """Regression tests for SST3 quality validation framework"""

    def __init__(self, verbose=False):
        self.verbose = verbose
        self.sst3_root = Path(__file__).parent.parent
        self.results = {'total_tests': 0, 'passed_tests': 0, 'failed_tests': [], 'category': 'quality_validation'}

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

    def test_five_dimensions_defined(self):
        ref_file = self.sst3_root / 'reference' / 'quality-validation.md'
        if not ref_file.exists():
            return False, "quality-validation.md not found"

        content = ref_file.read_text(encoding='utf-8')
        dimensions = ['Readability', 'Completeness', 'Correctness', 'Consistency', 'Effectiveness']

        for dim in dimensions:
            if dim not in content:
                return False, f"Missing dimension: {dim}"

        return True, "All 5 dimensions defined"

    def test_pass_examples_present(self):
        ref_file = self.sst3_root / 'reference' / 'quality-validation.md'
        if not ref_file.exists():
            return False, "quality-validation.md not found"

        content = ref_file.read_text(encoding='utf-8')
        if 'PASS Example' not in content:
            return False, "No PASS examples found"

        pass_count = content.count('PASS Example')
        if pass_count < 5:
            return False, f"Only {pass_count} PASS examples (expected >=5)"

        return True, f"{pass_count} PASS examples present"

    def test_fail_examples_present(self):
        ref_file = self.sst3_root / 'reference' / 'quality-validation.md'
        if not ref_file.exists():
            return False, "quality-validation.md not found"

        content = ref_file.read_text(encoding='utf-8')
        if 'FAIL Example' not in content:
            return False, "No FAIL examples found"

        fail_count = content.count('FAIL Example')
        if fail_count < 5:
            return False, f"Only {fail_count} FAIL examples (expected >=5)"

        return True, f"{fail_count} FAIL examples present"

    def test_quality_check_script_exists(self):
        script_path = self.sst3_root / 'scripts' / 'quality-check.py'
        if not script_path.exists():
            return False, "quality-check.py not found"
        return True, "quality-check.py exists"

    def test_anti_patterns_documented(self):
        anti_file = self.sst3_root / 'standards' / 'ANTI-PATTERNS.md'
        if not anti_file.exists():
            return False, "ANTI-PATTERNS.md not found"

        content = anti_file.read_text(encoding='utf-8')
        if 'Pattern' not in content:
            return False, "No patterns documented"

        return True, "Anti-patterns documented"

    def run_all_tests(self):
        print("\n" + "="*60)
        print("QUALITY VALIDATION TESTS")
        print("="*60 + "\n")

        self.run_test("5 dimensions defined", self.test_five_dimensions_defined)
        self.run_test("PASS examples present", self.test_pass_examples_present)
        self.run_test("FAIL examples present", self.test_fail_examples_present)
        self.run_test("quality-check.py exists", self.test_quality_check_script_exists)
        self.run_test("Anti-patterns documented", self.test_anti_patterns_documented)

        print("\n" + "-"*60)
        passed = self.results['passed_tests']
        total = self.results['total_tests']
        percentage = (passed / total * 100) if total > 0 else 0
        print(f"Quality Validation: {passed}/{total} tests passed ({percentage:.0f}%)")
        print("-"*60 + "\n")

        return self.results


def main():
    import argparse
    parser = argparse.ArgumentParser(description='SST3 Quality Validation Tests')
    parser.add_argument('--verbose', '-v', action='store_true')
    args = parser.parse_args()

    tests = QualityValidationTests(verbose=args.verbose)
    results = tests.run_all_tests()
    sys.exit(0 if results['passed_tests'] == results['total_tests'] else 1)


if __name__ == '__main__':
    main()
