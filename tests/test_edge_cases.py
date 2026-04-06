#!/usr/bin/env python3
"""
Edge Cases Tests

Tests:
- P2-25-27: Stage rejection handling (Stages 0, 2, 4)
- P2-28-30: Multi-repo edge cases (GAS, Python, JavaScript projects)
- P2-31-33: Error recovery (pre-commit hook, CI/CD, merge conflicts)

Philosophy: Edge case coverage for robustness.
"""

import re
from pathlib import Path


class EdgeCasesTests:
    """Edge case tests for SST3"""

    def __init__(self, verbose=False):
        self.verbose = verbose
        self.tests_dir = Path(__file__).parent
        self.sst3_dir = self.tests_dir.parent
        self.dotfiles_dir = self.sst3_dir.parent

        self.passed_tests = []
        self.failed_tests = []

    def test_issue_enforcement_rejection(self):
        """
        Test 25: Issue Enforcement Rejection Handling

        What: Workflow rejects if no GitHub Issue exists
        Why: All work requires GitHub Issue
        Pass Criteria: WORKFLOW.md or issue-template.md has rejection procedure documented
        """
        workflow = self.sst3_dir / 'workflow' / 'WORKFLOW.md'
        if not workflow.exists():
            self.failed_tests.append({
                'name': 'Test 25: Issue Enforcement Rejection',
                'reason': "WORKFLOW.md not found"
            })
            if self.verbose:
                print(f"  [FAIL] Test 25: Issue Enforcement Rejection")
                print(f"    FAIL: WORKFLOW.md not found")
            return

        content = workflow.read_text(encoding='utf-8')

        rejection_patterns = [
            r'STOP if',
            r'No GitHub Issue',
            r'require.*issue',
        ]

        found = False
        for pattern in rejection_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                found = True
                break

        if not found:
            self.failed_tests.append({
                'name': 'Test 25: Issue Enforcement Rejection',
                'reason': "No rejection procedure documented"
            })
            if self.verbose:
                print(f"  [FAIL] Test 25: Issue Enforcement Rejection")
                print(f"    FAIL: No rejection procedure documented")
        else:
            self.passed_tests.append({
                'name': 'Test 25: Issue Enforcement Rejection',
                'details': "Issue enforcement rejection procedure documented"
            })
            if self.verbose:
                print(f"  [PASS] Test 25: Issue Enforcement Rejection")

    def test_stage_2_rejection_handling(self):
        """
        Test 26: Stage 2 Rejection Handling

        What: Stage 2 rejects combined objectives
        Why: Combined objectives unmeasurable
        Pass Criteria: stage-2 has combined objective rejection
        """
        stage_2 = self.sst3_dir / 'workflow' / 'stage-2-code-amendment.md'
        if not stage_2.exists():
            self.failed_tests.append({
                'name': 'Test 26: Stage 2 Rejection Handling',
                'reason': "stage-2-code-amendment.md not found"
            })
            if self.verbose:
                print(f"  [FAIL] Test 26: Stage 2 Rejection Handling")
                print(f"    FAIL: stage-2 file not found")
            return

        content = stage_2.read_text(encoding='utf-8')

        # Check for combined objective detection
        combined_patterns = [
            r'combined.*objective',
            r'multiple.*objective',
            r'separate.*issue',
        ]

        found = False
        for pattern in combined_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                found = True
                break

        if not found:
            self.failed_tests.append({
                'name': 'Test 26: Stage 2 Rejection Handling',
                'reason': "No combined objective rejection in stage-2"
            })
            if self.verbose:
                print(f"  [FAIL] Test 26: Stage 2 Rejection Handling")
                print(f"    FAIL: No combined objective rejection")
        else:
            self.passed_tests.append({
                'name': 'Test 26: Stage 2 Rejection Handling',
                'details': "Stage 2 combined objective rejection documented"
            })
            if self.verbose:
                print(f"  [PASS] Test 26: Stage 2 Rejection Handling")

    def test_stage_4_rejection_handling(self):
        """
        Test 27: Stage 4 Rejection Handling

        What: Stage 4 rejects if BLOCKING detected
        Why: BLOCKING issues must prevent PR creation
        Pass Criteria: stage-4 has BLOCKING rejection procedure
        """
        stage_4 = self.sst3_dir / 'workflow' / 'stage-4-verification.md'
        if not stage_4.exists():
            self.failed_tests.append({
                'name': 'Test 27: Stage 4 Rejection Handling',
                'reason': "stage-4-verification.md not found"
            })
            if self.verbose:
                print(f"  [FAIL] Test 27: Stage 4 Rejection Handling")
                print(f"    FAIL: stage-4 file not found")
            return

        content = stage_4.read_text(encoding='utf-8')

        # Check for BLOCKING rejection
        blocking_patterns = [
            r'BLOCKING',
            r'auto.*fail',
            r'prevent.*PR',
        ]

        found = False
        for pattern in blocking_patterns:
            if re.search(pattern, content):
                found = True
                break

        if not found:
            self.failed_tests.append({
                'name': 'Test 27: Stage 4 Rejection Handling',
                'reason': "No BLOCKING rejection in stage-4"
            })
            if self.verbose:
                print(f"  [FAIL] Test 27: Stage 4 Rejection Handling")
                print(f"    FAIL: No BLOCKING rejection")
        else:
            self.passed_tests.append({
                'name': 'Test 27: Stage 4 Rejection Handling',
                'details': "Stage 4 BLOCKING rejection documented"
            })
            if self.verbose:
                print(f"  [PASS] Test 27: Stage 4 Rejection Handling")

    def test_gas_project_specifics(self):
        """
        Test 28: GAS Project Specifics

        What: Google Apps Script specific guidance
        Why: GAS has unique constraints (.gs files, clasp)
        Pass Criteria: Documentation mentions GAS specifics
        """
        # Check for GAS-specific documentation
        docs_to_check = [
            self.sst3_dir / 'workflow' / 'WORKFLOW.md',
            self.sst3_dir / 'reference' / 'multi-repo-considerations.md',
        ]

        gas_found = False

        for doc_file in docs_to_check:
            if doc_file.exists():
                content = doc_file.read_text(encoding='utf-8')
                if re.search(r'gas|google apps script|\.gs', content, re.IGNORECASE):
                    gas_found = True
                    break

        if not gas_found:
            self.failed_tests.append({
                'name': 'Test 28: GAS Project Specifics',
                'reason': "No GAS-specific guidance found"
            })
            if self.verbose:
                print(f"  [FAIL] Test 28: GAS Project Specifics")
                print(f"    FAIL: No GAS-specific guidance")
        else:
            self.passed_tests.append({
                'name': 'Test 28: GAS Project Specifics',
                'details': "GAS-specific guidance documented"
            })
            if self.verbose:
                print(f"  [PASS] Test 28: GAS Project Specifics")

    def test_python_project_specifics(self):
        """
        Test 29: Python Project Specifics

        What: Python-specific guidance (pytest, pre-commit)
        Why: Python projects have specific tooling
        Pass Criteria: Documentation mentions Python specifics
        """
        docs_to_check = [
            self.sst3_dir / 'workflow' / 'WORKFLOW.md',
            self.sst3_dir / 'reference' / 'multi-repo-considerations.md',
        ]

        python_found = False

        for doc_file in docs_to_check:
            if doc_file.exists():
                content = doc_file.read_text(encoding='utf-8')
                if re.search(r'python|pytest|\.py', content, re.IGNORECASE):
                    python_found = True
                    break

        if not python_found:
            self.failed_tests.append({
                'name': 'Test 29: Python Project Specifics',
                'reason': "No Python-specific guidance found"
            })
            if self.verbose:
                print(f"  [FAIL] Test 29: Python Project Specifics")
                print(f"    FAIL: No Python-specific guidance")
        else:
            self.passed_tests.append({
                'name': 'Test 29: Python Project Specifics',
                'details': "Python-specific guidance documented"
            })
            if self.verbose:
                print(f"  [PASS] Test 29: Python Project Specifics")

    def test_javascript_project_specifics(self):
        """
        Test 30: JavaScript Project Specifics

        What: JavaScript-specific guidance (npm, node)
        Why: JavaScript projects have specific tooling
        Pass Criteria: Documentation mentions JavaScript specifics
        """
        docs_to_check = [
            self.sst3_dir / 'workflow' / 'WORKFLOW.md',
            self.sst3_dir / 'reference' / 'multi-repo-considerations.md',
        ]

        js_found = False

        for doc_file in docs_to_check:
            if doc_file.exists():
                content = doc_file.read_text(encoding='utf-8')
                if re.search(r'javascript|npm|node|\.js', content, re.IGNORECASE):
                    js_found = True
                    break

        if not js_found:
            self.failed_tests.append({
                'name': 'Test 30: JavaScript Project Specifics',
                'reason': "No JavaScript-specific guidance found"
            })
            if self.verbose:
                print(f"  [FAIL] Test 30: JavaScript Project Specifics")
                print(f"    FAIL: No JavaScript-specific guidance")
        else:
            self.passed_tests.append({
                'name': 'Test 30: JavaScript Project Specifics',
                'details': "JavaScript-specific guidance documented"
            })
            if self.verbose:
                print(f"  [PASS] Test 30: JavaScript Project Specifics")

    def test_precommit_hook_failures(self):
        """
        Test 31: Pre-commit Hook Failures

        What: What to do when pre-commit hooks fail
        Why: Pre-commit failures block commits
        Pass Criteria: Recovery procedure documented
        """
        # Check for pre-commit recovery documentation
        docs_to_check = [
            self.sst3_dir / 'reference' / 'self-healing-guide.md',
            self.sst3_dir / 'workflow' / 'stage-5-pr-creation.md',
        ]

        precommit_recovery = False

        for doc_file in docs_to_check:
            if doc_file.exists():
                content = doc_file.read_text(encoding='utf-8')
                if re.search(r'pre.*commit.*fail', content, re.IGNORECASE):
                    precommit_recovery = True
                    break

        if not precommit_recovery:
            self.failed_tests.append({
                'name': 'Test 31: Pre-commit Hook Failures',
                'reason': "No pre-commit failure recovery documented"
            })
            if self.verbose:
                print(f"  [FAIL] Test 31: Pre-commit Hook Failures")
                print(f"    FAIL: No pre-commit recovery")
        else:
            self.passed_tests.append({
                'name': 'Test 31: Pre-commit Hook Failures',
                'details': "Pre-commit failure recovery documented"
            })
            if self.verbose:
                print(f"  [PASS] Test 31: Pre-commit Hook Failures")

    def test_cicd_failures(self):
        """
        Test 32: CI/CD Failures

        What: What to do when CI/CD fails
        Why: CI/CD failures block PR merge
        Pass Criteria: Recovery procedure documented
        """
        docs_to_check = [
            self.sst3_dir / 'reference' / 'self-healing-guide.md',
            self.sst3_dir / 'workflow' / 'stage-5-pr-creation.md',
        ]

        cicd_recovery = False

        for doc_file in docs_to_check:
            if doc_file.exists():
                content = doc_file.read_text(encoding='utf-8')
                if re.search(r'ci.*fail|workflow.*fail|action.*fail', content, re.IGNORECASE):
                    cicd_recovery = True
                    break

        if not cicd_recovery:
            self.failed_tests.append({
                'name': 'Test 32: CI/CD Failures',
                'reason': "No CI/CD failure recovery documented"
            })
            if self.verbose:
                print(f"  [FAIL] Test 32: CI/CD Failures")
                print(f"    FAIL: No CI/CD recovery")
        else:
            self.passed_tests.append({
                'name': 'Test 32: CI/CD Failures',
                'details': "CI/CD failure recovery documented"
            })
            if self.verbose:
                print(f"  [PASS] Test 32: CI/CD Failures")

    def test_merge_conflicts(self):
        """
        Test 33: Merge Conflicts

        What: What to do when merge conflicts occur
        Why: Merge conflicts block PR merge
        Pass Criteria: Resolution procedure documented
        """
        docs_to_check = [
            self.sst3_dir / 'reference' / 'self-healing-guide.md',
            self.sst3_dir / 'workflow' / 'stage-5-pr-creation.md',
        ]

        conflict_recovery = False

        for doc_file in docs_to_check:
            if doc_file.exists():
                content = doc_file.read_text(encoding='utf-8')
                if re.search(r'merge.*conflict|conflict.*resolution', content, re.IGNORECASE):
                    conflict_recovery = True
                    break

        if not conflict_recovery:
            self.failed_tests.append({
                'name': 'Test 33: Merge Conflicts',
                'reason': "No merge conflict resolution documented"
            })
            if self.verbose:
                print(f"  [FAIL] Test 33: Merge Conflicts")
                print(f"    FAIL: No merge conflict resolution")
        else:
            self.passed_tests.append({
                'name': 'Test 33: Merge Conflicts',
                'details': "Merge conflict resolution documented"
            })
            if self.verbose:
                print(f"  [PASS] Test 33: Merge Conflicts")

    def run_all_tests(self):
        """Run all edge case tests"""
        if self.verbose:
            print("\n" + "="*60)
            print("EDGE CASES TESTS")
            print("="*60 + "\n")

        # Stage rejection handling (25-27)
        self.test_issue_enforcement_rejection()
        self.test_stage_2_rejection_handling()
        self.test_stage_4_rejection_handling()

        # Multi-repo edge cases (28-30)
        self.test_gas_project_specifics()
        self.test_python_project_specifics()
        self.test_javascript_project_specifics()

        # Error recovery (31-33)
        self.test_precommit_hook_failures()
        self.test_cicd_failures()
        self.test_merge_conflicts()

        if self.verbose:
            print("\n" + "-"*60)
            print(f"Edge Cases: {len(self.passed_tests)}/{len(self.passed_tests) + len(self.failed_tests)} tests passed")
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

    tests = EdgeCasesTests(verbose=True)
    results = tests.run_all_tests()

    if results['failed_tests']:
        print(f"\n✗ {len(results['failed_tests'])} test(s) FAILED")
        sys.exit(1)
    else:
        print(f"\n✓ All {results['total_tests']} edge case tests PASSED")
        sys.exit(0)
