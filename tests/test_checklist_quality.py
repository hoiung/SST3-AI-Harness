#!/usr/bin/env python3
"""
Checklist Quality Tests for SST3 Regression Suite (Issue #133)

Tests that checklists implement "quality reminder loops" philosophy:
- STANDARDS.md references at decision points
- Guardrail reminders (DO/DON'Ts)
- Context loss recovery instructions
- Read-do-verify cycles
- Self-sufficient checklist items

Philosophy: "Even if it forgets, it gets reminded" - User's key insight

Test Categories:
1. Standards References (each stage references STANDARDS.md)
2. Guardrail Reminders (DO/DON'Ts at decision points)
3. Context Loss Recovery ("If context lost" instructions)
4. Quality Loops (read-do-verify cycles)
5. Self-Sufficiency (no assumed context)

Baseline: New tests (no baseline) - will establish baseline for Issue #135
"""

import re
import sys
from pathlib import Path


class ChecklistQualityTests:
    """Regression tests for SST3 checklist quality (quality reminder loops)"""

    def __init__(self, verbose=False):
        self.verbose = verbose
        self.sst3_root = Path(__file__).parent.parent
        self.workflow_dir = self.sst3_root / 'workflow'
        self.results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': [],
            'category': 'checklist_quality'
        }
        # SST3 Solo uses a single WORKFLOW.md (5-stage model, not 7 stage files)
        self.stages = [
            'WORKFLOW.md',
        ]

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

    def get_stage_content(self, stage_file):
        """Read stage file content"""
        stage_path = self.workflow_dir / stage_file
        if not stage_path.exists():
            return None
        return stage_path.read_text(encoding='utf-8')

    def test_checklist_standards_references(self):
        """
        Test 1: Each stage checklist has >=3 explicit STANDARDS.md references

        Philosophy: "If context lost, checklist reminds to check STANDARDS.md"
        Prevents: Context loss → quality degradation
        """
        total_references = 0
        stage_details = []
        min_per_stage = 3

        for stage_file in self.stages:
            content = self.get_stage_content(stage_file)
            if not content:
                return False, f"Stage file not found: {stage_file}"

            # Look for explicit STANDARDS.md references
            # Patterns: "STANDARDS.md", "See: ../standards/STANDARDS.md", etc.
            standards_refs = len(re.findall(r'STANDARDS\.md', content, re.IGNORECASE))

            total_references += standards_refs
            stage_details.append(f"{stage_file}: {standards_refs} refs")

        expected_total = min_per_stage * len(self.stages)  # 3 per stage × 5 stages = 15

        if total_references < expected_total:
            details = "\n    ".join(stage_details)
            return False, f"Only {total_references}/{expected_total} STANDARDS.md references found\n    {details}"

        return True, f"{total_references} STANDARDS.md references found across all stages (target: {expected_total})"

    def test_checklist_guardrail_reminders(self):
        """
        Test 2: Decision points reference DO/DON'Ts

        Philosophy: "Reminds to check important guardrails as it progresses"
        Prevents: Bypassing quality gates
        """
        critical_stages = [
            'stage-2-code-amendment.md',
            'stage-3-implementation.md',
            'stage-4-verification.md'
        ]

        total_guardrail_refs = 0
        stage_details = []
        min_per_stage = 2

        for stage_file in critical_stages:
            content = self.get_stage_content(stage_file)
            if not content:
                return False, f"Stage file not found: {stage_file}"

            # Look for DO/DON'T references in context
            # Patterns: "See DO's", "Check DON'Ts", "Review DO/DON'Ts", etc.
            do_refs = len(re.findall(r"DO['\s]s|DON['\s]Ts?|DO/DON['\s]T", content, re.IGNORECASE))

            total_guardrail_refs += do_refs
            stage_details.append(f"{stage_file}: {do_refs} guardrail refs")

        expected_total = min_per_stage * len(critical_stages)  # 2 per stage × 3 stages = 6

        if total_guardrail_refs < expected_total:
            details = "\n    ".join(stage_details)
            return False, f"Only {total_guardrail_refs}/{expected_total} guardrail reminders found\n    {details}"

        return True, f"{total_guardrail_refs} guardrail reminders found in critical stages (target: {expected_total})"

    def test_checklist_context_loss_recovery(self):
        """
        Test 3: "If context lost" recovery instructions exist

        Philosophy: "Even if it forgets, it gets reminded"
        Prevents: Dead-end when context lost
        """
        recovery_sections = 0
        missing_stages = []

        for stage_file in self.stages:
            content = self.get_stage_content(stage_file)
            if not content:
                return False, f"Stage file not found: {stage_file}"

            # Look for context loss recovery patterns
            # Patterns: "If context lost", "If resumed", "When resuming", "After interruption"
            has_recovery = bool(re.search(
                r'(if|when)\s+(context\s+lost|resumed|resuming|interrupted|restarted)',
                content,
                re.IGNORECASE
            ))

            if has_recovery:
                recovery_sections += 1
            else:
                missing_stages.append(stage_file)

        expected_total = len(self.stages)  # 1 per stage × 5 stages = 5

        if recovery_sections < expected_total:
            missing = ", ".join(missing_stages)
            return False, f"Only {recovery_sections}/{expected_total} stages have context loss recovery\n    Missing: {missing}"

        return True, f"{recovery_sections} stages have context loss recovery instructions"

    def test_checklist_quality_loops(self):
        """
        Test 4: Read-Do-Verify cycles complete in checklists

        Philosophy: Each major action has: 1) Read reference, 2) Execute, 3) Verify
        Prevents: Actions without validation
        """
        execution_stages = [
            'stage-1-research.md',
            'stage-2-code-amendment.md',
            'stage-3-implementation.md',
            'stage-4-verification.md',
            'stage-5-pr-creation.md'
        ]

        total_loops = 0
        stage_details = []
        min_per_stage = 2

        for stage_file in execution_stages:
            content = self.get_stage_content(stage_file)
            if not content:
                return False, f"Stage file not found: {stage_file}"

            # Count read-do-verify patterns
            # READ: Review, Read, Check, Verify, Analyze
            # DO: Create, Execute, Implement, Run, Generate
            # VERIFY: Test, Validate, Confirm, Ensure

            read_actions = len(re.findall(
                r'^\s*-\s*\[\s*\]\s*(Review|Read|Check|Verify|Analyze)',
                content,
                re.MULTILINE | re.IGNORECASE
            ))

            do_actions = len(re.findall(
                r'^\s*-\s*\[\s*\]\s*(Create|Execute|Implement|Run|Generate|Launch)',
                content,
                re.MULTILINE | re.IGNORECASE
            ))

            verify_actions = len(re.findall(
                r'^\s*-\s*\[\s*\]\s*(Test|Validate|Confirm|Ensure)',
                content,
                re.MULTILINE | re.IGNORECASE
            ))

            # A complete loop requires all 3 phases present
            complete_loops = min(read_actions, do_actions, verify_actions)
            total_loops += complete_loops
            stage_details.append(f"{stage_file}: {complete_loops} loops (R:{read_actions}/D:{do_actions}/V:{verify_actions})")

        expected_total = min_per_stage * len(execution_stages)  # 2 per stage × 5 stages = 10

        if total_loops < expected_total:
            details = "\n    ".join(stage_details)
            return False, f"Only {total_loops}/{expected_total} complete read-do-verify loops found\n    {details}"

        return True, f"{total_loops} complete read-do-verify loops found (target: {expected_total})"

    def test_checklist_self_sufficiency(self):
        """
        Test 5: Checklist items don't assume prior context

        Philosophy: Items work without assumed context
        Prevents: Broken checklists with context loss
        """
        problematic_patterns = [
            r'\bas\s+discussed\b',
            r'\blike\s+before\b',
            r'\bremember\s+to\b',
            r'\bthe\s+file\b',  # Should specify which file
            r'\bit\s+works\b',   # Should specify what
            r'\bthis\s+step\b',  # Should specify which step
        ]

        total_violations = 0
        violation_details = []

        for stage_file in self.stages:
            content = self.get_stage_content(stage_file)
            if not content:
                return False, f"Stage file not found: {stage_file}"

            # Extract only checklist items (lines starting with - [ ])
            checklist_items = re.findall(r'^\s*-\s*\[\s*\]\s*(.+)$', content, re.MULTILINE)

            stage_violations = 0
            for item in checklist_items:
                for pattern in problematic_patterns:
                    if re.search(pattern, item, re.IGNORECASE):
                        stage_violations += 1
                        if self.verbose:
                            violation_details.append(f"{stage_file}: '{item[:50]}...'")
                        break  # Count each item only once

            total_violations += stage_violations

        if total_violations > 0:
            details = "\n    ".join(violation_details[:5])  # Show first 5
            more = f"\n    ... and {total_violations - 5} more" if total_violations > 5 else ""
            return False, f"{total_violations} checklist items with context assumptions found\n    {details}{more}"

        return True, "All checklist items are self-sufficient (no context assumptions)"

    def run_all_tests(self):
        """Run all checklist quality tests"""
        print("\n" + "="*60)
        print("CHECKLIST QUALITY TESTS (Quality Reminder Loops)")
        print("="*60 + "\n")

        self.run_test("Test 1: Checklist Standards References",
                     self.test_checklist_standards_references)
        self.run_test("Test 2: Checklist Guardrail Reminders",
                     self.test_checklist_guardrail_reminders)
        self.run_test("Test 3: Checklist Context Loss Recovery",
                     self.test_checklist_context_loss_recovery)
        self.run_test("Test 4: Checklist Quality Loops",
                     self.test_checklist_quality_loops)
        self.run_test("Test 5: Checklist Self-Sufficiency",
                     self.test_checklist_self_sufficiency)

        # Summary
        print("\n" + "-"*60)
        passed = self.results['passed_tests']
        total = self.results['total_tests']
        percentage = (passed / total * 100) if total > 0 else 0

        print(f"Checklist Quality: {passed}/{total} tests passed ({percentage:.0f}%)")

        if self.results['failed_tests']:
            print("\nFailed Tests:")
            for fail in self.results['failed_tests']:
                print(f"  - {fail['name']}: {fail['reason']}")

        print("-"*60 + "\n")

        return self.results


def main():
    """Run checklist quality tests standalone"""
    import argparse
    parser = argparse.ArgumentParser(description='SST3 Checklist Quality Tests')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    args = parser.parse_args()

    tests = ChecklistQualityTests(verbose=args.verbose)
    results = tests.run_all_tests()

    # Exit with appropriate code
    if results['passed_tests'] == results['total_tests']:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
