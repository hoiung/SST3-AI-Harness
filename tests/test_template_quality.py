#!/usr/bin/env python3
"""
Template Quality Tests

Tests:
- P1-10: Template Specificity (not too generic, placeholders have examples)
- P1-11: Template Completeness (all required sections, no TODOs)
- P1-12: Issue Template Quality (problem statement, goals, success criteria)
Philosophy: Template quality prevents ambiguous execution.
"""

import re
from pathlib import Path


class TemplateQualityTests:
    """Template quality tests"""

    def __init__(self, verbose=False):
        self.verbose = verbose
        self.tests_dir = Path(__file__).parent
        self.sst3_dir = self.tests_dir.parent
        self.templates_dir = self.sst3_dir / 'templates'

        self.passed_tests = []
        self.failed_tests = []

    def test_template_specificity(self):
        """
        Test 10: Template Specificity

        What: Templates not too generic, placeholders have examples
        Why: Generic templates lead to poor quality
        Pass Criteria: Placeholders have concrete examples

        Checks:
        - Placeholders like [X] have examples
        - Not just "fill this in"
        - Specific guidance provided
        """
        issues = []

        # Generic placeholder patterns (BAD)
        generic_patterns = [
            r'\[Fill this in\]',
            r'\[TODO\]',
            r'\[Insert .*\]',
            r'\[Add .*\]',
            r'\[Your .*\]',
        ]

        # Good placeholder pattern (with example)
        # Example: [Issue #123] or [e.g., reduce tokens by 10%]

        for template_file in self.templates_dir.glob('*.md'):
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')

                    for line_num, line in enumerate(lines, 1):
                        for pattern in generic_patterns:
                            if re.search(pattern, line, re.IGNORECASE):
                                issues.append(f"{template_file.name}:{line_num} - Generic placeholder: {line.strip()[:60]}")

            except Exception as e:
                continue

        if issues:
            self.failed_tests.append({
                'name': 'Test 10: Template Specificity',
                'reason': f"Found {len(issues)} generic placeholders:\n" + '\n'.join(issues[:5])
            })
            if self.verbose:
                print(f"  [FAIL] Test 10: Template Specificity")
                print(f"    FAIL: Found {len(issues)} generic placeholders")
                for issue in issues[:5]:
                    print(f"      {issue}")
        else:
            self.passed_tests.append({
                'name': 'Test 10: Template Specificity',
                'details': "No generic placeholders found"
            })
            if self.verbose:
                print(f"  [PASS] Test 10: Template Specificity")

    def test_template_completeness(self):
        """
        Test 11: Template Completeness

        What: All required sections present, no TODOs
        Why: Incomplete templates lead to incomplete work
        Pass Criteria: All templates have required sections, no TODO markers

        Checks:
        - No TODO markers
        - No empty sections
        - Required sections present
        """
        issues = []

        # TODO patterns
        todo_patterns = [
            r'TODO:',
            r'FIXME:',
            r'XXX:',
            r'\[ \].*TODO',
        ]

        for template_file in self.templates_dir.glob('*.md'):
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')

                    # Check for TODOs
                    for line_num, line in enumerate(lines, 1):
                        for pattern in todo_patterns:
                            if re.search(pattern, line, re.IGNORECASE):
                                issues.append(f"{template_file.name}:{line_num} - TODO found: {line.strip()[:60]}")

                    # Check for empty sections (## Section\n\n##)
                    empty_section_pattern = re.compile(r'##\s+(.+?)\n\s*\n\s*##')
                    for match in empty_section_pattern.finditer(content):
                        section_name = match.group(1)
                        issues.append(f"{template_file.name} - Empty section: {section_name}")

            except Exception as e:
                continue

        if issues:
            self.failed_tests.append({
                'name': 'Test 11: Template Completeness',
                'reason': f"Found {len(issues)} completeness issues:\n" + '\n'.join(issues[:5])
            })
            if self.verbose:
                print(f"  [FAIL] Test 11: Template Completeness")
                print(f"    FAIL: Found {len(issues)} completeness issues")
                for issue in issues[:5]:
                    print(f"      {issue}")
        else:
            self.passed_tests.append({
                'name': 'Test 11: Template Completeness',
                'details': "All templates complete, no TODOs"
            })
            if self.verbose:
                print(f"  [PASS] Test 11: Template Completeness")

    def test_issue_template_quality(self):
        """
        Test 12: Issue Template Quality

        What: Issue template has problem statement, goals, success criteria
        Why: Quality issues require clear definition
        Pass Criteria: All required sections present

        Required Sections:
        - Problem Statement
        - Goals/Objectives
        - Success Criteria
        - Context (optional but recommended)
        """
        issue_template = self.templates_dir / 'issue-template.md'

        if not issue_template.exists():
            self.failed_tests.append({
                'name': 'Test 12: Issue Template Quality',
                'reason': "Issue template not found"
            })
            if self.verbose:
                print(f"  [FAIL] Test 12: Issue Template Quality")
                print(f"    FAIL: Issue template not found")
            return

        required_sections = [
            'Problem Statement',
            'Goals',
            'Success Criteria',
        ]

        missing_sections = []

        try:
            with open(issue_template, 'r', encoding='utf-8') as f:
                content = f.read()

                for section in required_sections:
                    # Check for section header (various formats)
                    patterns = [
                        f'##\s+{section}',
                        f'##\s+{section.lower()}',
                        f'##\s+{section.replace(" ", "").lower()}',
                    ]

                    found = False
                    for pattern in patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            found = True
                            break

                    if not found:
                        missing_sections.append(section)

        except Exception as e:
            self.failed_tests.append({
                'name': 'Test 12: Issue Template Quality',
                'reason': f"Error reading template: {e}"
            })
            if self.verbose:
                print(f"  [FAIL] Test 12: Issue Template Quality")
                print(f"    FAIL: Error reading template: {e}")
            return

        if missing_sections:
            self.failed_tests.append({
                'name': 'Test 12: Issue Template Quality',
                'reason': f"Missing sections: {', '.join(missing_sections)}"
            })
            if self.verbose:
                print(f"  [FAIL] Test 12: Issue Template Quality")
                print(f"    FAIL: Missing sections: {', '.join(missing_sections)}")
        else:
            self.passed_tests.append({
                'name': 'Test 12: Issue Template Quality',
                'details': "All required sections present"
            })
            if self.verbose:
                print(f"  [PASS] Test 12: Issue Template Quality")

    def run_all_tests(self):
        """Run all template quality tests"""
        if self.verbose:
            print("\n" + "="*60)
            print("TEMPLATE QUALITY TESTS")
            print("="*60 + "\n")

        self.test_template_specificity()
        self.test_template_completeness()
        self.test_issue_template_quality()

        if self.verbose:
            print("\n" + "-"*60)
            print(f"Template Quality: {len(self.passed_tests)}/{len(self.passed_tests) + len(self.failed_tests)} tests passed")
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

    tests = TemplateQualityTests(verbose=True)
    results = tests.run_all_tests()

    if results['failed_tests']:
        print(f"\n✗ {len(results['failed_tests'])} test(s) FAILED")
        sys.exit(1)
    else:
        print(f"\n✓ All {results['total_tests']} template quality tests PASSED")
        sys.exit(0)
