#!/usr/bin/env python3
"""
Semantic Quality Tests for SST3 Regression Suite (Issue #133)

Tests that ensure semantic clarity for effective quality loops:
- No ambiguous language
- JBGE compliance (conciseness)
- Concrete examples present
- LMCE concrete guidance

Philosophy: Ambiguity defeats quality loops (can't follow unclear instructions)

Test Categories:
1. Ambiguous Language Detection (subjective phrases)
2. JBGE Compliance Validation (concise guidance)
3. Concrete Examples Present (not abstractions)
4. LMCE Concrete Guidance (measurable criteria)

Baseline: Prevents Issue #108 (subjective instructions), #94 (verbose solutions)
"""

import re
import sys
from pathlib import Path


class SemanticQualityTests:
    """Regression tests for SST3 semantic quality (clarity for quality loops)"""

    def __init__(self, verbose=False):
        self.verbose = verbose
        self.sst3_root = Path(__file__).parent.parent
        self.workflow_dir = self.sst3_root / 'workflow'
        self.standards_dir = self.sst3_root / 'standards'
        self.results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': [],
            'category': 'semantic_quality'
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

    def test_no_ambiguous_language(self):
        """
        Test 11: SST3 files avoid subjective phrases

        Philosophy: Ambiguity defeats quality loops (can't follow unclear instructions)
        Prevents: Issue #108 (subjective instructions shipped)
        """
        ambiguous_patterns = [
            r'\bwhen\s+appropriate\b',
            r'\bif\s+needed\b',
            r'\bconsider\b',
            r'\bmight\b',
            r'\bshould\s+probably\b',
            r'\bas\s+necessary\b',
            r'\bwhen\s+possible\b',
            r'\bideally\b',
        ]

        sst2_files = []
        # Scan workflow files
        if self.workflow_dir.exists():
            sst2_files.extend(self.workflow_dir.glob('*.md'))
        # Scan standards files
        if self.standards_dir.exists():
            sst2_files.extend(self.standards_dir.glob('*.md'))

        total_violations = 0
        violation_details = []
        max_allowed = 5  # Some OK in examples

        for file_path in sst2_files:
            content = file_path.read_text(encoding='utf-8')

            for pattern in ambiguous_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    total_violations += len(matches)
                    if self.verbose:
                        violation_details.append(f"{file_path.name}: {len(matches)} × '{pattern}'")

        if total_violations > max_allowed:
            details = "\n    ".join(violation_details[:10])  # Show first 10
            more = f"\n    ... and {total_violations - 10} more" if total_violations > 10 else ""
            return False, f"{total_violations} ambiguous phrases found (max allowed: {max_allowed})\n    {details}{more}"

        return True, f"Only {total_violations} ambiguous phrases found (acceptable: ≤{max_allowed})"

    def test_jbge_compliance(self):
        """
        Test 12: Content provides value without verbosity

        Philosophy: JBGE is foundation principle - checklists reference it constantly
        Prevents: Issue #94 (5000-word verbose solutions)
        """
        # Check that no sections are excessively long without structure
        sst2_files = []
        if self.workflow_dir.exists():
            sst2_files.extend(self.workflow_dir.glob('*.md'))
        if self.standards_dir.exists():
            sst2_files.extend(self.standards_dir.glob('*.md'))

        violations = []
        max_section_lines = 200

        for file_path in sst2_files:
            content = file_path.read_text(encoding='utf-8')

            # Split by headers (## or ###)
            sections = re.split(r'^#{2,3}\s+', content, flags=re.MULTILINE)

            for i, section in enumerate(sections[1:], 1):  # Skip first empty split
                lines = section.split('\n')

                # Check if section has sub-headings
                has_subheadings = bool(re.search(r'^#{3,4}\s+', section, re.MULTILINE))

                if len(lines) > max_section_lines and not has_subheadings:
                    violations.append(f"{file_path.name}: Section {i} has {len(lines)} lines without sub-headings")

        if violations:
            details = "\n    ".join(violations[:5])
            more = f"\n    ... and {len(violations) - 5} more" if len(violations) > 5 else ""
            return False, f"{len(violations)} sections exceed {max_section_lines} lines without structure\n    {details}{more}"

        return True, f"No sections exceed {max_section_lines} lines without sub-headings (JBGE compliant)"

    def test_concrete_examples_present(self):
        """
        Test 13: Critical sections have examples (not just abstractions)

        Philosophy: Checklists reference examples - without concrete examples, references are useless
        Prevents: Issue #131 (abstraction degradation)
        """
        critical_files = [
            self.standards_dir / 'STANDARDS.md',
            self.standards_dir / 'ANTI-PATTERNS.md',
        ]

        # Also check quality-validation if it exists
        quality_val = self.sst3_root / 'reference' / 'quality-validation.md'
        if quality_val.exists():
            critical_files.append(quality_val)

        total_examples = 0
        file_details = []
        min_total = 15  # 15 examples across 3 files

        for file_path in critical_files:
            if not file_path.exists():
                continue

            content = file_path.read_text(encoding='utf-8')

            # Count example patterns
            example_markers = len(re.findall(r'(Example:|For instance|e\.g\.,|```)', content, re.IGNORECASE))

            total_examples += example_markers
            file_details.append(f"{file_path.name}: {example_markers} examples")

        if total_examples < min_total:
            details = "\n    ".join(file_details)
            return False, f"Only {total_examples}/{min_total} examples found in critical files\n    {details}"

        return True, f"{total_examples} concrete examples found across critical files (target: {min_total})"

    def test_lmce_concrete_guidance(self):
        """
        Test 14: LMCE principle has concrete measurement tests

        Philosophy: LMCE section is referenced in every stage checklist
        Prevents: Subjective application of principles
        """
        standards_file = self.standards_dir / 'STANDARDS.md'

        if not standards_file.exists():
            return False, "STANDARDS.md not found"

        content = standards_file.read_text(encoding='utf-8')

        # Find LMCE section
        lmce_match = re.search(
            r'#{1,3}\s*LMCE\b.*?(?=#{1,3}\s|\Z)',
            content,
            re.DOTALL | re.IGNORECASE
        )

        if not lmce_match:
            return False, "LMCE section not found in STANDARDS.md"

        lmce_section = lmce_match.group(0)

        # Count measurement tests/criteria in LMCE section
        # Look for: numbered tests, criteria, thresholds, examples
        measurement_tests = len(re.findall(
            r'(test:|criteria:|threshold:|measure:|\d+\.\s+\*\*|Example:)',
            lmce_section,
            re.IGNORECASE
        ))

        min_tests = 4  # At least 4 measurable criteria

        if measurement_tests < min_tests:
            return False, f"LMCE section has only {measurement_tests}/{min_tests} measurable criteria"

        # Check section isn't too abstract
        abstract_words = len(re.findall(
            r'\b(important|should|consider|appropriate|good|better|best)\b',
            lmce_section,
            re.IGNORECASE
        ))

        concrete_words = len(re.findall(
            r'\b(must|always|never|<=|>=|<|>|\d+)\b',
            lmce_section,
            re.IGNORECASE
        ))

        if abstract_words > concrete_words:
            return False, f"LMCE section too abstract ({abstract_words} abstract vs {concrete_words} concrete words)"

        return True, f"LMCE section has {measurement_tests} measurement tests (concrete, not abstract)"

    def run_all_tests(self):
        """Run all semantic quality tests"""
        print("\n" + "="*60)
        print("SEMANTIC QUALITY TESTS (Clarity for Quality Loops)")
        print("="*60 + "\n")

        self.run_test("Test 11: No Ambiguous Language",
                     self.test_no_ambiguous_language)
        self.run_test("Test 12: JBGE Compliance",
                     self.test_jbge_compliance)
        self.run_test("Test 13: Concrete Examples Present",
                     self.test_concrete_examples_present)
        self.run_test("Test 14: LMCE Concrete Guidance",
                     self.test_lmce_concrete_guidance)

        # Summary
        print("\n" + "-"*60)
        passed = self.results['passed_tests']
        total = self.results['total_tests']
        percentage = (passed / total * 100) if total > 0 else 0

        print(f"Semantic Quality: {passed}/{total} tests passed ({percentage:.0f}%)")

        if self.results['failed_tests']:
            print("\nFailed Tests:")
            for fail in self.results['failed_tests']:
                print(f"  - {fail['name']}: {fail['reason']}")

        print("-"*60 + "\n")

        return self.results


def main():
    """Run semantic quality tests standalone"""
    import argparse
    parser = argparse.ArgumentParser(description='SST3 Semantic Quality Tests')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    args = parser.parse_args()

    tests = SemanticQualityTests(verbose=args.verbose)
    results = tests.run_all_tests()

    # Exit with appropriate code
    if results['passed_tests'] == results['total_tests']:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
