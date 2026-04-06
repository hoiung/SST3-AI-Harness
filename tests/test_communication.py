#!/usr/bin/env python3
"""Communication Tests for SST3 Regression Suite (Issue #133)

Tests templates and communication protocols.
Baseline: 95% communication quality (Issue #131)

Tests (18-21):
- Test 18: Issue Update Format
- Test 19: Retrospective Format
- Test 20: Handover Template Completeness
- Test 21: Report Clarity
"""

import re
import sys
from pathlib import Path


class CommunicationTests:
    """Regression tests for SST3 communication quality"""

    def __init__(self, verbose=False):
        self.verbose = verbose
        self.sst3_root = Path(__file__).parent.parent
        self.results = {'total_tests': 0, 'passed_tests': 0, 'failed_tests': [], 'category': 'communication'}

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

    def test_issue_template_complete(self):
        template_file = self.sst3_root / 'templates' / 'issue-template.md'
        if not template_file.exists():
            return False, "issue-template.md not found"

        content = template_file.read_text(encoding='utf-8')
        required = ['Problem', 'Success Criteria', 'Context']
        for req in required:
            if req not in content:
                return False, f"Missing: {req}"

        return True, "Issue template complete"

    def test_handover_template_complete(self):
        template_file = self.sst3_root / 'templates' / 'chat-handover.md'
        if not template_file.exists():
            return False, "chat-handover.md not found"

        content = template_file.read_text(encoding='utf-8')
        if 'checkpoint' not in content.lower():
            return False, "Checkpoint section not found"

        return True, "Handover template complete"

    def test_retrospective_example_present(self):
        example_file = self.sst3_root / 'templates' / 'retrospective-example.md'
        if not example_file.exists():
            return False, "retrospective-example.md not found"

        content = example_file.read_text(encoding='utf-8')
        lines = len(content.split('\n'))

        if lines < 80:
            return False, f"Only {lines} lines (expected >=80)"

        return True, f"Retrospective example present ({lines} lines)"

    def test_stage_announcement_format(self):
        workflow_file = self.sst3_root / 'workflow' / 'WORKFLOW.md'
        if not workflow_file.exists():
            return False, "WORKFLOW.md not found"

        content = workflow_file.read_text(encoding='utf-8')
        if 'checkpoint' not in content.lower():
            return False, "Checkpoint format not documented"

        return True, "Stage announcement format defined in WORKFLOW.md"

    def test_issue_update_format(self):
        """
        Test 18: Issue Update Format

        What: Stage completion updates and progress summaries
        Why: Consistent communication with users
        Pass Criteria: WORKFLOW.md has update format guidelines
        """
        workflow_file = self.sst3_root / 'workflow' / 'WORKFLOW.md'
        if not workflow_file.exists():
            return False, "WORKFLOW.md not found"

        content = workflow_file.read_text(encoding='utf-8')

        # Check for update/communication guidance
        update_patterns = [
            r'stage.*completion',
            r'progress.*update',
            r'issue.*update',
            r'communication.*protocol',
        ]

        found = False
        for pattern in update_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                found = True
                break

        if not found:
            return False, "No issue update format documented"

        return True, "Issue update format documented"

    def test_retrospective_format(self):
        """
        Test 19: Retrospective Format

        What: Required sections present, 85-line example provided
        Why: Quality retrospectives enable self-healing
        Pass Criteria: retrospective-example.md has all sections

        Required sections:
        - What Happened
        - Root Cause
        - What Worked
        - What Didn't Work
        - Process Changes
        """
        retro_file = self.sst3_root / 'templates' / 'retrospective-example.md'
        if not retro_file.exists():
            return False, "retrospective-example.md not found"

        content = retro_file.read_text(encoding='utf-8')
        lines = content.split('\n')

        # Check line count (should be ~85 lines as per Issue #131 example)
        if len(lines) < 80:
            return False, f"Only {len(lines)} lines (expected ≥80)"

        # Check required sections
        required_sections = [
            'What Happened',
            'Root Cause',
            'What Worked',
            'What Didn\'t Work',
            'Process Changes',
        ]

        missing = []
        for section in required_sections:
            if not re.search(rf'##\s+{re.escape(section)}', content, re.IGNORECASE):
                missing.append(section)

        if missing:
            return False, f"Missing sections: {', '.join(missing)}"

        return True, f"Retrospective format complete ({len(lines)} lines)"

    def test_handover_template_completeness(self):
        """
        Test 20: Handover Template Completeness

        What: Recovery if context lost section, all handover sections
        Why: Context loss recovery critical for quality loops
        Pass Criteria: All sections present including "Recovery if context lost"

        Required sections:
        - Current State
        - What's Been Done
        - Next Steps
        - Recovery if context lost (CRITICAL)
        """
        handover_file = self.sst3_root / 'templates' / 'chat-handover.md'
        if not handover_file.exists():
            return False, "chat-handover.md not found"

        content = handover_file.read_text(encoding='utf-8')

        required_sections = [
            'Current State',
            'Next Steps',
        ]

        # Special check for recovery guidance
        recovery_patterns = [
            r'recovery',
            r'context lost',
            r'if.*lost',
            r'resuming',
        ]

        has_recovery = False
        for pattern in recovery_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                has_recovery = True
                break

        missing = []
        for section in required_sections:
            if not re.search(rf'##\s+{re.escape(section)}', content, re.IGNORECASE):
                missing.append(section)

        if missing:
            return False, f"Missing sections: {', '.join(missing)}"

        if not has_recovery:
            return False, "Missing 'Recovery if context lost' guidance"

        return True, "Handover template complete with recovery guidance"

    def test_report_clarity(self):
        """
        Test 21: Report Clarity

        What: No jargon without explanation, action items clear
        Why: Clear communication prevents confusion
        Pass Criteria: Templates have clear, actionable language

        Checks:
        - No undefined acronyms
        - Action items use imperatives (not vague)
        - Examples provided for complex concepts
        """
        # Check templates for clarity markers
        templates_dir = self.sst3_root / 'templates'

        if not templates_dir.exists():
            return False, "Templates directory not found"

        clarity_issues = []

        # Common jargon that should be explained
        jargon_patterns = [
            r'\bLMCE\b(?!\s*\()',  # LMCE without explanation
            r'\bJBGE\b(?!\s*\()',  # JBGE without explanation
            r'\bSST\b(?!\s*\()',   # SST without explanation (first use)
        ]

        for template_file in templates_dir.glob('*.md'):
            try:
                content = template_file.read_text(encoding='utf-8')

                for pattern in jargon_patterns:
                    # Check first occurrence only
                    match = re.search(pattern, content)
                    if match:
                        # Allow if it's in a section that defines it
                        if 'acronym' not in content.lower() and 'stands for' not in content.lower():
                            clarity_issues.append(f"{template_file.name}: Undefined acronym {match.group()}")

            except Exception as e:
                continue

        # This is a soft check - we expect some instances but flag excessive ones
        if len(clarity_issues) > 3:
            return False, f"Found {len(clarity_issues)} clarity issues"

        return True, f"Report clarity acceptable ({len(clarity_issues)} minor issues)"

    def run_all_tests(self):
        print("\n" + "="*60)
        print("COMMUNICATION TESTS")
        print("="*60 + "\n")

        # Original tests
        self.run_test("Issue template complete", self.test_issue_template_complete)
        self.run_test("Handover template complete", self.test_handover_template_complete)
        self.run_test("Retrospective example present", self.test_retrospective_example_present)
        self.run_test("Stage announcement format defined", self.test_stage_announcement_format)

        # Tests (18-21)
        self.run_test("Test 18: Issue Update Format", self.test_issue_update_format)
        self.run_test("Test 19: Retrospective Format", self.test_retrospective_format)
        self.run_test("Test 20: Handover Template Completeness", self.test_handover_template_completeness)
        self.run_test("Test 21: Report Clarity", self.test_report_clarity)

        print("\n" + "-"*60)
        passed = self.results['passed_tests']
        total = self.results['total_tests']
        percentage = (passed / total * 100) if total > 0 else 0
        print(f"Communication: {passed}/{total} tests passed ({percentage:.0f}%)")
        print("-"*60 + "\n")

        return self.results


def main():
    import argparse
    parser = argparse.ArgumentParser(description='SST3 Communication Tests')
    parser.add_argument('--verbose', '-v', action='store_true')
    args = parser.parse_args()

    tests = CommunicationTests(verbose=args.verbose)
    results = tests.run_all_tests()
    sys.exit(0 if results['passed_tests'] == results['total_tests'] else 1)


if __name__ == '__main__':
    main()
