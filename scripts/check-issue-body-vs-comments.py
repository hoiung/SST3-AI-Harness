#!/usr/bin/env python3
"""
Validate GitHub Issue body contains all critical insights (not buried in comments).

This script enforces the principle: "Insights go in BODY, not comments"
- Comments are for discussion (temporal, context-dependent)
- Body is for facts (permanent, search-discoverable)
- If information changes task definition, it MUST update the body

Exit codes:
  0: Validation passed (no insights found in comments OR all insights already in body)
  1: Validation failed (insights detected in comments that should be in body)
  3: Error (gh CLI not found, Issue not found, API error)
"""

import argparse
import re
import sys
from typing import List, Dict, Tuple

from sst3_utils import fetch_issue_data as _fetch_issue_data, fix_windows_console

fix_windows_console()


# Exit codes
EXIT_SUCCESS = 0  # No violations OR all insights in body
EXIT_FAILURE = 1  # Insights in comments need body edits
EXIT_ERROR = 3    # Script error (gh CLI not found, API error)


def fetch_issue_data(issue_num: int, repo: str = None) -> dict:
    """Fetch Issue body and comments using gh CLI. Wraps sst3_utils with validation."""
    data = _fetch_issue_data(issue_num, ['body', 'comments', 'title', 'url'], repo)

    if data is None:
        print(f"❌ Error fetching Issue #{issue_num}")
        sys.exit(EXIT_ERROR)

    # Validate required fields (NO FALLBACKS)
    if 'body' not in data or data['body'] is None:
        print(f"❌ Issue #{issue_num} body is empty or null")
        sys.exit(EXIT_ERROR)

    if 'comments' not in data:
        print(f"❌ Issue #{issue_num} response missing 'comments' field")
        sys.exit(EXIT_ERROR)

    return data


def detect_insight_patterns(comment_text: str) -> List[Tuple[str, str]]:
    """
    Detect insight patterns in comment text that suggest content should be in body.

    Args:
        comment_text: Comment body text

    Returns:
        List of (pattern_type, matched_text) tuples
        Empty list if no patterns detected
    """
    insights = []

    # Pattern 1: Checkboxes in comments (should be in body)
    if re.search(r'^- \[([ x])\]', comment_text, re.MULTILINE):
        checkbox_count = len(re.findall(r'^- \[([ x])\]', comment_text, re.MULTILINE))
        insights.append((
            'checkboxes_in_comment',
            f"{checkbox_count} checkbox(es) found - checkboxes belong in Issue body for tracking"
        ))

    # Pattern 2: Bug/blocker discoveries
    bug_patterns = [
        r'\b(found|discovered|detected)\s+(a\s+)?(bug|issue|problem|blocker)',
        r'\b(blocking|blocked by)\b',
        r'\bactually\s+(broken|failing|not working)',
    ]
    for pattern in bug_patterns:
        matches = re.findall(pattern, comment_text, re.IGNORECASE)
        if matches:
            snippet = comment_text[:100].replace('\n', ' ')
            insights.append((
                'bug_discovery',
                f"Bug/blocker mentioned: '{snippet}...'"
            ))
            break  # Only report once per comment

    # Pattern 3: New requirements discovered
    req_patterns = [
        r'\b(new|additional|missing)\s+(requirement|feature|need)',
        r'\bshould\s+also\s+(add|include|implement)',
        r'\bturns out we need',
    ]
    for pattern in req_patterns:
        matches = re.findall(pattern, comment_text, re.IGNORECASE)
        if matches:
            snippet = comment_text[:100].replace('\n', ' ')
            insights.append((
                'new_requirement',
                f"New requirement mentioned: '{snippet}...'"
            ))
            break  # Only report once per comment

    # Pattern 4: Technical decisions/architecture changes
    decision_patterns = [
        r'\b(decided to|switching to|changed approach)',
        r'\b(will use|using|chose)\s+\w+\s+(instead of|rather than)',
        r'\barchitecture change:',
    ]
    for pattern in decision_patterns:
        matches = re.findall(pattern, comment_text, re.IGNORECASE)
        if matches:
            snippet = comment_text[:100].replace('\n', ' ')
            insights.append((
                'technical_decision',
                f"Technical decision mentioned: '{snippet}...'"
            ))
            break  # Only report once per comment

    # Pattern 5: Cross-issue impacts
    cross_issue_patterns = [
        r'#\d+\s+(is\s+)?(affected|impacted|blocked|related)',
        r'(affects|impacts|breaks)\s+#\d+',
        r'need to update\s+#\d+',
    ]
    for pattern in cross_issue_patterns:
        matches = re.findall(pattern, comment_text, re.IGNORECASE)
        if matches:
            # Extract issue numbers
            issue_refs = re.findall(r'#(\d+)', comment_text)
            insights.append((
                'cross_issue_impact',
                f"Cross-issue impact: References #{', #'.join(issue_refs)}"
            ))
            break  # Only report once per comment

    # Pattern 6: Root cause analysis
    root_cause_patterns = [
        r'\broot cause:',
        r'\bactually\s+(caused by|due to)',
        r'\bthe real (issue|problem) is',
    ]
    for pattern in root_cause_patterns:
        matches = re.findall(pattern, comment_text, re.IGNORECASE)
        if matches:
            snippet = comment_text[:100].replace('\n', ' ')
            insights.append((
                'root_cause_analysis',
                f"Root cause explained: '{snippet}...'"
            ))
            break  # Only report once per comment

    return insights


def check_insight_in_body(insight_type: str, comment_snippet: str, body_text: str) -> bool:
    """
    Check if insight already exists in Issue body.

    Args:
        insight_type: Type of insight (for context)
        comment_snippet: Snippet from comment containing insight
        body_text: Issue body text

    Returns:
        True if insight appears to be in body, False otherwise
    """
    # For checkboxes, check if similar checkboxes exist in body
    if insight_type == 'checkboxes_in_comment':
        # If body has checkboxes, assume they're tracked (weak check)
        return bool(re.search(r'^- \[([ x])\]', body_text, re.MULTILINE))

    # For cross-issue impacts, check if issue references exist in body
    if insight_type == 'cross_issue_impact':
        issue_nums = re.findall(r'#(\d+)', comment_snippet)
        for num in issue_nums:
            if f'#{num}' not in body_text:
                return False
        return True

    # For other insights, do fuzzy text matching (first 50 chars)
    # Extract meaningful words from comment snippet
    words = re.findall(r'\b\w{4,}\b', comment_snippet.lower())[:5]

    if not words:
        return False

    # Check if at least 3 of the words appear in body
    matches = sum(1 for word in words if word in body_text.lower())
    return matches >= min(3, len(words))


def validate_issue(issue_num: int, repo: str = None, verbose: bool = False) -> Tuple[bool, List[Dict]]:
    """
    Validate Issue has insights in body (not just comments).

    Args:
        issue_num: GitHub Issue number
        repo: Repository in OWNER/REPO format (optional)
        verbose: Show detailed output

    Returns:
        (passed, violations)
        - passed: True if no violations, False otherwise
        - violations: List of dicts with comment index, insight type, and details
    """
    issue_data = fetch_issue_data(issue_num, repo)

    body = issue_data['body']
    comments = issue_data.get('comments', [])

    if verbose:
        print(f"\nAnalyzing Issue #{issue_num}: {issue_data.get('title', 'Untitled')}")
        print(f"URL: {issue_data.get('url', 'N/A')}")
        print(f"Comments to analyze: {len(comments)}")
        print()

    violations = []

    for idx, comment in enumerate(comments, start=1):
        comment_body = comment.get('body', '')
        created_at = comment.get('createdAt', 'unknown')
        author = comment.get('author', {}).get('login', 'unknown')

        # Detect insights in this comment
        insights = detect_insight_patterns(comment_body)

        if not insights:
            continue

        if verbose:
            print(f"Comment #{idx} ({author} at {created_at}):")

        for insight_type, insight_text in insights:
            # Check if insight already in body
            in_body = check_insight_in_body(insight_type, insight_text, body)

            if not in_body:
                violations.append({
                    'comment_num': idx,
                    'author': author,
                    'created_at': created_at,
                    'insight_type': insight_type,
                    'insight_text': insight_text,
                    'comment_url': f"{issue_data.get('url', '')}#issuecomment-{comment.get('id', '')}"
                })

                if verbose:
                    print(f"  ❌ [{insight_type}] {insight_text}")
                    print(f"     NOT found in Issue body - needs body edit")
            else:
                if verbose:
                    print(f"  ✅ [{insight_type}] {insight_text}")
                    print(f"     Already in Issue body")

        if verbose and insights:
            print()

    passed = len(violations) == 0
    return passed, violations


def main():
    parser = argparse.ArgumentParser(
        description='Validate GitHub Issue body contains critical insights (not buried in comments)',
        epilog='Principle: Insights go in BODY, not comments. Comments are temporal, body is permanent.'
    )
    parser.add_argument('--issue', type=int, required=True,
                       help='GitHub Issue number')
    parser.add_argument('--repo', type=str,
                       help='Repository in OWNER/REPO format (default: current repo)')
    parser.add_argument('--verbose', action='store_true',
                       help='Show detailed analysis output')
    args = parser.parse_args()

    # Validate Issue
    passed, violations = validate_issue(args.issue, args.repo, args.verbose)

    if passed:
        print(f"✅ Issue #{args.issue}: All insights in body (or no insights in comments)")
        sys.exit(EXIT_SUCCESS)
    else:
        print(f"❌ Issue #{args.issue}: {len(violations)} insight(s) found in comments need body edits")
        print()
        print("Violations:")
        for v in violations:
            print(f"  - Comment #{v['comment_num']} ({v['author']} at {v['created_at']})")
            print(f"    Type: {v['insight_type']}")
            print(f"    Detail: {v['insight_text']}")
            print(f"    URL: {v['comment_url']}")
            print()

        print("Action Required:")
        print(f"  1. Review each comment above")
        print(f"  2. Edit Issue #{args.issue} BODY (not comments) to include insights")
        print(f"  3. Re-run this script to verify exit code 0")
        print()
        print("Principle: Comments are for discussion, body is for facts.")
        print("If information changes the task, it MUST be in the body for discoverability.")

        sys.exit(EXIT_FAILURE)


if __name__ == '__main__':
    main()
