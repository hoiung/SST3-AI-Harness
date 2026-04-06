#!/usr/bin/env python3
"""
SST3 Regression Test Suite Runner (Issue #133)

Main test runner that orchestrates all 8 test categories, calculates
quality score, and compares against baseline.

Usage:
    python regression-suite.py              # Run all tests
    python regression-suite.py --verbose     # Verbose output
    python regression-suite.py --category discoverability  # Run specific category
    python regression-suite.py --baseline    # Compare against baseline

Exit Codes:
    0: All tests passed (quality ≥90/100)
    1: Some tests failed or quality <90/100
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

# Import test modules
from test_discoverability import DiscoverabilityTests
# test_stage_execution and test_subagent_quality never created — removed (#399)
from test_monitoring import MonitoringTests
from test_recovery import RecoveryTests
from test_communication import CommunicationTests
from test_quality_validation import QualityValidationTests
from test_cross_repo import CrossRepoTests
# New P0 test categories (Issue #133)
from test_checklist_quality import ChecklistQualityTests
from test_execution_validation import ExecutionValidationTests
from test_semantic_quality import SemanticQualityTests
# Additional test categories (Issue #133)
from test_path_portability import PathPortabilityTests
from test_template_quality import TemplateQualityTests
from test_edge_cases import EdgeCasesTests
from test_framework_validation import FrameworkValidationTests


class RegressionSuite:
    """Main regression test suite orchestrator"""

    def __init__(self, verbose=False):
        self.verbose = verbose
        self.tests_dir = Path(__file__).parent
        self.metrics_dir = self.tests_dir.parent.parent / 'SST3-metrics' / 'test-results'
        self.baseline_file = self.metrics_dir / 'baseline-measurements.json'

        # Test category weights (total = 100%)
        # Updated for Issue #133 (125 total tests)
        self.weights = {
            # P0 categories (17 tests) - 60% weight
            'checklist_quality': 25,      # 5 tests - quality loops foundation
            'execution_validation': 20,   # 5 tests - catastrophic failure prevention
            'semantic_quality': 15,       # 4 tests - clarity for quality loops

            # P1 categories (21 tests) - 28% weight
            'path_portability': 4,        # 4 tests - cross-platform support
            'template_quality': 4,        # 4 tests - template completeness
            'communication': 5,           # 9 tests (5 original + 4 new) - communication protocols

            # Supporting categories - 12% weight
            'discoverability': 3,
            'quality_validation': 2,
            'monitoring': 2,
            'recovery': 2,
            'cross_repo': 1,

            # P2 Edge cases - 2% weight
            'edge_cases': 1,              # 9 tests - edge case handling
            'framework_validation': 1     # 3 tests - framework validation
        }

        self.results = {}
        self.baseline = None

    def load_baseline(self):
        """Load baseline measurements from JSON"""
        if not self.baseline_file.exists():
            print(f"WARNING: Baseline file not found: {self.baseline_file}")
            return None

        try:
            with open(self.baseline_file, 'r') as f:
                self.baseline = json.load(f)
            return self.baseline
        except Exception as e:
            print(f"ERROR loading baseline: {e}")
            return None

    def run_category(self, category_name):
        """Run tests for a specific category"""
        test_classes = {
            # P0 categories
            'checklist_quality': ChecklistQualityTests,
            'execution_validation': ExecutionValidationTests,
            'semantic_quality': SemanticQualityTests,
            # P1 categories
            'path_portability': PathPortabilityTests,
            'template_quality': TemplateQualityTests,
            'communication': CommunicationTests,
            # Supporting categories
            'discoverability': DiscoverabilityTests,
            'quality_validation': QualityValidationTests,
            'monitoring': MonitoringTests,
            'recovery': RecoveryTests,
            'cross_repo': CrossRepoTests,
            # P2 categories
            'edge_cases': EdgeCasesTests,
            'framework_validation': FrameworkValidationTests
        }

        if category_name not in test_classes:
            print(f"ERROR: Unknown category: {category_name}")
            return None

        test_class = test_classes[category_name]
        test_instance = test_class(verbose=self.verbose)
        return test_instance.run_all_tests()

    def calculate_category_score(self, results):
        """Calculate 0-100 score for a category"""
        passed = results['passed_tests']
        total = results['total_tests']

        if total == 0:
            return 0

        return (passed / total) * 100

    def calculate_overall_score(self):
        """Calculate weighted overall quality score (0-100)"""
        total_score = 0

        for category, weight in self.weights.items():
            if category in self.results:
                category_score = self.calculate_category_score(self.results[category])
                weighted_score = category_score * (weight / 100)
                total_score += weighted_score

        return total_score

    def run_all_tests(self):
        """Run all test categories"""
        print("\n" + "="*70)
        print("SST3 REGRESSION TEST SUITE")
        print("="*70)
        if self.baseline:
            print(f"Baseline: {self.baseline['overall_score']}/100 (Issue #{self.baseline['issue']})")
        else:
            print("Baseline: Not loaded")
        print("="*70 + "\n")

        # Run each category
        for category in self.weights.keys():
            self.results[category] = self.run_category(category)

        return self.results

    def generate_report(self, show_baseline=False):
        """Generate comprehensive test report"""
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70 + "\n")

        # Category results
        print("Category Results:")
        print("-" * 70)

        total_passed = 0
        total_tests = 0

        for category, weight in self.weights.items():
            if category not in self.results:
                continue

            results = self.results[category]
            passed = results['passed_tests']
            total = results['total_tests']
            percentage = (passed / total * 100) if total > 0 else 0

            total_passed += passed
            total_tests += total

            # Status indicator
            if percentage == 100:
                status = "[PASS]"
            elif percentage >= 80:
                status = "[WARN]"
            else:
                status = "[FAIL]"

            print(f"  {status} {category:25} {passed:2}/{total:2} tests ({percentage:3.0f}%) [weight: {weight}%]")

        print("-" * 70)

        # Overall score
        overall_score = self.calculate_overall_score()
        print(f"\nOverall Quality Score: {overall_score:.1f}/100")
        print(f"Total Tests: {total_passed}/{total_tests} passed")

        # Baseline comparison
        if show_baseline and self.baseline:
            baseline_score = self.baseline['overall_score']
            diff = overall_score - baseline_score

            print(f"\nBaseline Comparison:")
            print(f"  Baseline: {baseline_score}/100 (Issue #{self.baseline['issue']})")
            print(f"  Current:  {overall_score:.1f}/100")
            print(f"  Change:   {diff:+.1f} points")

            if diff >= 0:
                print(f"  Status:   [PASS] PASS (quality maintained or improved)")
            elif diff >= -2:
                print(f"  Status:   [WARN] ACCEPTABLE (within ±2 points)")
            else:
                print(f"  Status:   [FAIL] REGRESSION DETECTED (quality decreased)")

        # Final verdict
        print("\n" + "="*70)
        if overall_score >= 90:
            print("RESULT: [PASS] PASS - Quality meets threshold (>=90/100)")
            exit_code = 0
        elif overall_score >= 85:
            print("RESULT: [WARN] WARNING - Quality below target (85-89/100)")
            exit_code = 0  # Warning but not failure
        else:
            print("RESULT: [FAIL] FAIL - Quality below acceptable threshold (<85/100)")
            exit_code = 1

        print("="*70 + "\n")

        return exit_code

    def list_failed_tests(self):
        """List all failed tests"""
        failed_count = 0

        for category, results in self.results.items():
            if results['failed_tests']:
                failed_count += len(results['failed_tests'])

        if failed_count > 0:
            print("\nFailed Tests:")
            print("-" * 70)

            for category, results in self.results.items():
                if results['failed_tests']:
                    print(f"\n{category.upper()}:")
                    for fail in results['failed_tests']:
                        print(f"  [FAIL] {fail['name']}")
                        print(f"    Reason: {fail['reason']}")

            print("-" * 70 + "\n")

    def write_baseline(self, formatted_results):
        """Write/update baseline measurements"""
        baseline_path = self.metrics_dir / 'baseline-measurements.json'
        baseline_path.parent.mkdir(parents=True, exist_ok=True)

        baseline = {
            "version": "2.0.0",
            "date": datetime.now().isoformat(),
            "issue": "#133",
            "overall_score": formatted_results["overall_score"],
            "total_tests": formatted_results["total_tests"],
            "passed_tests": formatted_results["passed_tests"],
            "category_scores": formatted_results["category_scores"]
        }

        with open(baseline_path, 'w') as f:
            json.dump(baseline, f, indent=2)

        return str(baseline_path)

    def write_execution_results(self, formatted_results):
        """Write timestamped execution results"""
        timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        history_dir = self.metrics_dir / 'execution-history'
        history_dir.mkdir(parents=True, exist_ok=True)

        result_path = history_dir / f"{timestamp}.json"

        with open(result_path, 'w') as f:
            json.dump(formatted_results, f, indent=2)

        # Also write as latest
        latest_path = self.metrics_dir / 'latest-results.json'
        with open(latest_path, 'w') as f:
            json.dump(formatted_results, f, indent=2)

        return str(result_path)

    def format_results_for_json(self):
        """Format test results for JSON output"""
        category_scores = {}
        category_details = {}
        total_tests = 0
        total_passed = 0

        for category, results in self.results.items():
            passed = results['passed_tests']
            total = results['total_tests']
            percentage = (passed / total * 100) if total > 0 else 0

            category_scores[category] = {
                "score": round(percentage, 1),
                "passed": passed,
                "total": total,
                "weight": self.weights[category]
            }

            category_details[category] = {
                "passed_tests": passed,
                "failed_tests": results['failed_tests'],
                "total_tests": total
            }

            total_tests += total
            total_passed += passed

        overall_score = self.calculate_overall_score()

        return {
            "timestamp": datetime.now().isoformat(),
            "overall_score": round(overall_score, 1),
            "total_tests": total_tests,
            "passed_tests": total_passed,
            "failed_tests": total_tests - total_passed,
            "category_scores": category_scores,
            "category_details": category_details,
            "baseline_comparison": self._get_baseline_comparison(overall_score) if self.baseline else None
        }

    def _get_baseline_comparison(self, current_score):
        """Get baseline comparison data"""
        if not self.baseline:
            return None

        baseline_score = self.baseline.get('overall_score', 0)
        diff = current_score - baseline_score

        return {
            "baseline_score": baseline_score,
            "current_score": current_score,
            "difference": round(diff, 1),
            "status": "improved" if diff >= 0 else ("acceptable" if diff >= -2 else "regression"),
            "issue": self.baseline.get('issue', 'unknown')
        }


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='SST3 Regression Test Suite',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python regression-suite.py                 # Run all tests
  python regression-suite.py --verbose       # Verbose output
  python regression-suite.py --category discoverability  # Specific category
  python regression-suite.py --baseline      # Compare against baseline
        """
    )

    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')
    parser.add_argument('--category', '-c', type=str,
                       help='Run specific category only')
    parser.add_argument('--baseline', '-b', action='store_true',
                       help='Show baseline comparison')
    parser.add_argument('--update-baseline', action='store_true',
                       help='Update baseline measurements with current results')

    args = parser.parse_args()

    # Initialize suite
    suite = RegressionSuite(verbose=args.verbose)
    suite.load_baseline()

    # Run tests
    if args.category:
        # Run single category
        result = suite.run_category(args.category)
        if result:
            score = suite.calculate_category_score(result)
            print(f"\nCategory Score: {score:.1f}/100")
            exit_code = 0 if score >= 80 else 1
        else:
            exit_code = 1
    else:
        # Run all categories
        suite.run_all_tests()
        exit_code = suite.generate_report(show_baseline=args.baseline)

        # Show failed tests if any
        suite.list_failed_tests()

        # Write results to JSON files
        formatted_results = suite.format_results_for_json()
        result_file = suite.write_execution_results(formatted_results)
        print(f"\nResults written to: {result_file}")
        print(f"Latest results: {suite.metrics_dir / 'latest-results.json'}")

        # Update baseline if requested
        if args.update_baseline:
            baseline_file = suite.write_baseline(formatted_results)
            print(f"Baseline updated: {baseline_file}")

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
