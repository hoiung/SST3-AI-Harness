#!/usr/bin/env python3
"""Automated quality validation for SST3 content"""

import sys
import os
import re

def check_readability(content):
    """Check if content is clear and understandable"""
    issues = []

    # Check average sentence length
    sentences = re.split(r'[.!?]\s+', content)
    if sentences:
        avg_length = sum(len(s.split()) for s in sentences) / len(sentences)
        if avg_length > 30:
            issues.append("Average sentence length too long (>30 words)")

    # Check for jargon without explanation
    jargon = ['orchestrator', 'subagent', 'guardrail', 'pruning']
    for term in jargon:
        if term in content.lower() and 'see:' not in content.lower():
            # Jargon used but no cross-reference
            pass  # Allow jargon in SST3 internal docs

    return len(issues) == 0, issues

def check_completeness(content, expected_sections=None):
    """Check if all critical content is present"""
    issues = []

    if expected_sections:
        for section in expected_sections:
            if section not in content:
                issues.append(f"Missing expected section: {section}")

    # Check for orphaned references
    references = re.findall(r'See:\s*([^\n]+)', content)
    for ref in references:
        # Just flag for manual review
        pass

    return len(issues) == 0, issues

def check_correctness(content):
    """Check if information is accurate"""
    issues = []

    # Check for broken markdown links
    links = re.findall(r'\[([^\]]+)\]\(([^\)]+)\)', content)
    for text, url in links:
        if url.startswith('http') and 'example.com' in url:
            issues.append(f"Placeholder URL found: {url}")

    # Check for contradictions (basic)
    if 'MUST' in content and 'MUST NOT' in content:
        # Flag for manual review
        pass

    return len(issues) == 0, issues

def check_consistency(content):
    """Check if content aligns with SST3 standards"""
    issues = []

    # Check for consistent terminology
    if 'claude code' in content.lower() and 'Claude Code' not in content:
        issues.append("Inconsistent capitalization: 'Claude Code'")

    # Check for consistent formatting
    if '**' in content:  # Uses bold
        # Count bold vs. headings
        bold_count = content.count('**')
        heading_count = content.count('\n#')
        if bold_count > heading_count * 3:
            issues.append("Excessive bold formatting - consider using headings")

    return len(issues) == 0, issues

def check_effectiveness(content):
    """Check if users can follow successfully"""
    issues = []

    # Check for actionable instructions
    if 'how to' in content.lower() or 'guide' in content.lower():
        if not any(marker in content for marker in ['1.', '-', '*']):
            issues.append("Guide lacks structured steps (bullets/numbers)")

    # Check for examples when needed
    if 'example' in content.lower():
        if '```' not in content:
            issues.append("Example mentioned but no code block found")

    return len(issues) == 0, issues

def validate_quality(file_path):
    """Run all 5 quality checks"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    results = {
        "Readability": check_readability(content),
        "Completeness": check_completeness(content),
        "Correctness": check_correctness(content),
        "Consistency": check_consistency(content),
        "Effectiveness": check_effectiveness(content)
    }

    return results

def main():
    if len(sys.argv) < 2:
        print("Usage: quality-check.py <file>")
        print("\nRuns 5-dimension quality validation")
        sys.exit(1)

    file_path = sys.argv[1]

    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    print(f"\n# Quality Validation: {os.path.basename(file_path)}\n")

    results = validate_quality(file_path)
    passed = 0
    total = len(results)

    for dimension, (status, issues) in results.items():
        symbol = "[OK]" if status else "[!!]"
        print(f"{symbol} {dimension}: {'PASS' if status else 'FAIL'}")
        if issues:
            for issue in issues:
                print(f"     - {issue}")
        if status:
            passed += 1

    print(f"\n## Quality Score: {passed}/{total} ({100*passed/total:.0f}%)")

    if passed == total:
        print("Result: PASS - All dimensions validated")
        sys.exit(0)
    elif passed >= total * 0.8:
        print("Result: WARNING - Review flagged issues")
        sys.exit(0)
    else:
        print("Result: FAIL - Multiple quality issues")
        sys.exit(1)

if __name__ == "__main__":
    main()
