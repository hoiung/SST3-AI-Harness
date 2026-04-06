#!/usr/bin/env python3
"""
Execution Validation Tests for SST3 Regression Suite (Issue #133)

Tests that prevent catastrophic execution failures (NOT token gates):
- BLOCKING keyword detection (Issue #124)
- Combined objectives detection (Issue #124)
- Content preservation comprehension (Issue #124)
- Baseline measurement enforcement (Issue #124, #128)
- Diff analysis requirement

Philosophy: Execution failure prevention (catastrophic, not token-related)

Test Categories:
1. BLOCKING Detection Execution (auto-fail on BLOCKING keyword)
2. Combined Objective Detection (multiple objectives flagged)
3. Content Preservation Comprehension (large deletions validated)
4. Baseline Measurement Enforcement (optimizations require baseline)
5. Diff Analysis Requirement (large changes documented)

Baseline: Prevents Issue #124 catastrophic failure pattern (4.5h rollback, 305K tokens)
"""

import re
import sys
from pathlib import Path


class ExecutionValidationTests:
    """Regression tests for SST3 execution validation (catastrophic failure prevention)"""

    def __init__(self, verbose=False):
        self.verbose = verbose
        self.sst3_root = Path(__file__).parent.parent
        self.workflow_dir = self.sst3_root / 'workflow'
        self.results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': [],
            'category': 'execution_validation'
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
                if message and self.verbose:
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

    def test_blocking_keyword_detection(self):
        """
        Test 6: Stage 4 auto-fails on BLOCKING keyword

        Philosophy: Execution failure prevention (NOT token gate)
        Prevents: Issue #124 (BLOCKING ignored, PR created with critical issues)
        """
        stage4_file = self.workflow_dir / 'stage-4-verification.md'

        if not stage4_file.exists():
            return False, "stage-4-verification.md not found"

        content = stage4_file.read_text(encoding='utf-8')

        # Check for BLOCKING detection guidance
        has_blocking_detection = bool(re.search(
            r'BLOCKING',
            content,
            re.IGNORECASE
        ))

        if not has_blocking_detection:
            return False, "No BLOCKING keyword detection documented in Stage 4"

        # Check for auto-fail guidance
        has_auto_fail = bool(re.search(
            r'(auto[- ]fail|must fail|fail immediately|block|stop|prevent)',
            content,
            re.IGNORECASE
        ))

        if not has_auto_fail:
            return False, "BLOCKING keyword found but no auto-fail guidance documented"

        return True, "BLOCKING detection with auto-fail guidance documented in Stage 4"

    def test_combined_objectives_detection(self):
        """
        Test 7: Issue body parser detects multiple objectives

        Philosophy: Execution failure prevention (Issue #124: 4.5h, 305K tokens wasted)
        Prevents: Combined objectives without baseline = unmeasurable
        """
        stage0_file = self.workflow_dir / 'stage-0-issue-enforcement.md'

        if not stage0_file.exists():
            return False, "stage-0-issue-enforcement.md not found"

        content = stage0_file.read_text(encoding='utf-8')

        # Check for multiple objective detection guidance
        has_objective_check = bool(re.search(
            r'(multiple|combined|several)\s+(objective|goal|requirement|task)',
            content,
            re.IGNORECASE
        ))

        if not has_objective_check:
            return False, "No multiple objective detection guidance in issue enforcement"

        return True, "Multiple objective detection guidance documented in issue enforcement"

    def test_content_preservation_comprehension(self):
        """
        Test 8: Large deletions (>100 lines) trigger comprehension checks

        Philosophy: Execution failure prevention (Issue #124: 95% deletion passed generic test)
        Prevents: 4,186 words → 207 words passed generic "content preserved" check
        """
        stage4_file = self.workflow_dir / 'stage-4-verification.md'

        if not stage4_file.exists():
            return False, "stage-4-verification.md not found"

        content = stage4_file.read_text(encoding='utf-8')

        # Check for deletion threshold guidance
        has_deletion_threshold = bool(re.search(
            r'(>|greater than|more than|exceeds?)\s*\d+\s*(line|deletion)',
            content,
            re.IGNORECASE
        ))

        if not has_deletion_threshold:
            return False, "No deletion threshold guidance in Stage 4"

        # Check for comprehension testing requirement
        has_comprehension = bool(re.search(
            r'(comprehension|use[- ]case|scenario|validation|test)',
            content,
            re.IGNORECASE
        ))

        if not has_comprehension:
            return False, "Deletion threshold found but no comprehension testing requirement"

        return True, "Large deletion comprehension testing documented in Stage 4 (>100 lines)"

    def test_baseline_measurement_enforcement(self):
        """
        Test 9: Optimizations require before/after measurements

        Philosophy: Execution validation (optimization requires measurable baseline)
        Prevents: Issue #124/#128 unmeasurable changes
        """
        stage2_file = self.workflow_dir / 'stage-2-code-amendment.md'

        if not stage2_file.exists():
            return False, "stage-2-code-amendment.md not found"

        content = stage2_file.read_text(encoding='utf-8')

        # Check for baseline/optimization guidance
        has_baseline = bool(re.search(
            r'(baseline|before[- ]measurement|current\s+state|initial\s+value)',
            content,
            re.IGNORECASE
        ))

        if not has_baseline:
            return False, "No baseline measurement guidance in Stage 2"

        # Check for optimization-specific guidance
        has_optimization = bool(re.search(
            r'optimi[sz]ation|performance|improve|reduce|increase',
            content,
            re.IGNORECASE
        ))

        if not has_optimization:
            return False, "No optimization guidance in Stage 2"

        # Check for measurement requirement
        has_measurement = bool(re.search(
            r'(measure|metric|quantif|before.*after|after.*before)',
            content,
            re.IGNORECASE
        ))

        if not has_measurement:
            return False, "Baseline/optimization found but no measurement requirement documented"

        return True, "Baseline measurement requirement for optimizations documented in Stage 2"

    def test_diff_analysis_requirement(self):
        """
        Test 10: Large changes require explicit diff review

        Philosophy: Execution validation
        Prevents: Issue #124 (1,504 line deletions without review)
        """
        stage4_file = self.workflow_dir / 'stage-4-verification.md'

        if not stage4_file.exists():
            return False, "stage-4-verification.md not found"

        content = stage4_file.read_text(encoding='utf-8')

        # Check for diff analysis guidance
        has_diff = bool(re.search(
            r'(git\s+diff|diff\s+review|diff\s+analysis|review.*change)',
            content,
            re.IGNORECASE
        ))

        if not has_diff:
            return False, "No diff analysis requirement documented in Stage 4"

        return True, "Diff analysis requirement for substantial changes documented in Stage 4"

    def run_all_tests(self):
        """Run all execution validation tests"""
        print("\n" + "="*60)
        print("EXECUTION VALIDATION TESTS (Catastrophic Failure Prevention)")
        print("="*60 + "\n")

        self.run_test("Test 6: BLOCKING Keyword Detection",
                     self.test_blocking_keyword_detection)
        self.run_test("Test 7: Combined Objectives Detection",
                     self.test_combined_objectives_detection)
        self.run_test("Test 8: Content Preservation Comprehension",
                     self.test_content_preservation_comprehension)
        self.run_test("Test 9: Baseline Measurement Enforcement",
                     self.test_baseline_measurement_enforcement)
        self.run_test("Test 10: Diff Analysis Requirement",
                     self.test_diff_analysis_requirement)

        # Summary
        print("\n" + "-"*60)
        passed = self.results['passed_tests']
        total = self.results['total_tests']
        percentage = (passed / total * 100) if total > 0 else 0

        print(f"Execution Validation: {passed}/{total} tests passed ({percentage:.0f}%)")

        if self.results['failed_tests']:
            print("\nFailed Tests:")
            for fail in self.results['failed_tests']:
                print(f"  - {fail['name']}: {fail['reason']}")

        print("-"*60 + "\n")

        return self.results


def main():
    """Run execution validation tests standalone"""
    import argparse
    parser = argparse.ArgumentParser(description='SST3 Execution Validation Tests')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    args = parser.parse_args()

    tests = ExecutionValidationTests(verbose=args.verbose)
    results = tests.run_all_tests()

    # Exit with appropriate code
    if results['passed_tests'] == results['total_tests']:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
