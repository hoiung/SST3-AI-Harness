#!/usr/bin/env python3
"""
Validate GitHub Issue checkboxes for SST3 stage completion.

This script ensures stage gates work correctly by:
- START gate (subagent): Validate all previous stages complete before starting work
- END gate (main agent): Validate current stage complete before proceeding
- Closure: Validate all stages complete before closing Issue

Exit codes:
  0: Validation passed (all checkboxes complete)
  1: Validation failed (checkboxes incomplete)
  3: Error (gh CLI not found, Issue not found, etc.)
"""

import argparse
import re
import sys
from typing import Dict, List

from sst3_utils import fetch_issue_data as _fetch_issue_data, fix_windows_console

fix_windows_console()


# Exit codes
EXIT_SUCCESS = 0  # All validations passed
EXIT_FAILURE = 1  # Validation failed (checkboxes incomplete)
EXIT_ERROR = 3    # Script error (gh CLI not found, Issue not found, etc.)


def fetch_issue_data(issue_num: int) -> dict:
    """Fetch Issue body and comments using gh CLI."""
    data = _fetch_issue_data(issue_num, ['body', 'comments'])
    if data is None:
        print(f"❌ Error fetching Issue #{issue_num}")
        sys.exit(EXIT_ERROR)
    return data


def _parse_text_for_checkboxes(
    text: str,
    source: str,
    timestamp: str | None,
    checkboxes: dict,
    mode: str = 'stage'
) -> None:
    """
    Parse checkboxes from text and APPEND to checkboxes dict.

    Args:
        text: Text to parse
        source: Source identifier (body, comment-N)
        timestamp: Timestamp if from comment
        checkboxes: Dict to append to {stage_num: [checkbox_dicts]} OR {'solo': [checkbox_dicts]}
        mode: 'stage' for Stage mode, 'solo' for Solo mode
    """
    if mode == 'stage':
        header_pattern = r'^##+ Stage (\d+):'
    else:  # mode == 'solo'
        header_pattern = r'^##+ Solo Assignment'

    checkbox_pattern = r'^- \[([ x])\] (.+)$'

    current_section = None  # stage_num (int) or 'solo' (str)

    for line in text.split('\n'):
        line = line.strip()

        # Check for mode-specific header
        if mode == 'stage':
            header_match = re.match(header_pattern, line)
            if header_match:
                stage_num = int(header_match.group(1))
                if stage_num not in checkboxes:
                    checkboxes[stage_num] = []
                current_section = stage_num
                continue
        else:  # mode == 'solo'
            if re.match(header_pattern, line):
                if 'solo' not in checkboxes:
                    checkboxes['solo'] = []
                current_section = 'solo'
                continue

        # Reset current_section when hitting a level-2 header that doesn't match our pattern
        # Note: ### subsections within Stage/Solo sections should NOT reset
        if re.match(r'^## [^#]', line):  # Only ## headers (not ### or deeper)
            if mode == 'stage' and not re.match(header_pattern, line):
                current_section = None
            elif mode == 'solo' and not re.match(header_pattern, line):
                current_section = None
            continue

        # Check for checkbox within current section
        if current_section is not None:
            checkbox_match = re.match(checkbox_pattern, line)
            if checkbox_match:
                checked = checkbox_match.group(1) == 'x'
                text = checkbox_match.group(2)
                checkboxes[current_section].append({
                    'checked': checked,
                    'text': text,
                    'source': source,
                    'timestamp': timestamp
                })


def parse_checkboxes(issue_data: dict, source: str = 'all', mode: str = 'stage') -> Dict[int | str, List[dict]]:
    """
    Extract checkboxes from Issue body AND/OR comments based on source parameter.

    Args:
        issue_data: Dict with 'body' and 'comments' keys from gh CLI
        source: Where to parse checkboxes from ('body', 'comments', or 'all')

    Expected format:
    ## Stage 1: Research
    - [ ] Checkbox 1
    - [x] Checkbox 2

    ## Stage 1: Research
    - [ ] Checkbox 3

    Returns:
    {
        0: [
            {'checked': False, 'text': 'Checkbox 1', 'source': 'body', 'timestamp': None},
            {'checked': True, 'text': 'Checkbox 2', 'source': 'body', 'timestamp': None}
        ],
        1: [
            {'checked': False, 'text': 'Checkbox 3', 'source': 'comment', 'timestamp': '2025-01-01T00:00:00Z'}
        ]
    }
    """
    checkboxes = {}

    # 1. Parse body checkboxes (if source is 'body' or 'all')
    if source in ('body', 'all'):
        _parse_text_for_checkboxes(
            text=issue_data['body'],
            source='body',
            timestamp=None,
            checkboxes=checkboxes,
            mode=mode
        )

    # 2. Parse each comment's checkboxes (if source is 'comments' or 'all')
    if source in ('comments', 'all'):
        for idx, comment in enumerate(issue_data.get('comments', []), start=1):
            _parse_text_for_checkboxes(
                text=comment['body'],
                source=f'comment-{idx}',
                timestamp=comment.get('createdAt'),
                checkboxes=checkboxes,
            mode=mode
            )

    return checkboxes


def validate_issue_setup(issue_body: str) -> bool:
    """
    Validate Issue has proper structure for SST3 workflow.

    Checks:
    - At least one ##+ Stage X: (H2 or deeper) section exists
    - Acceptance Criteria section exists
    - At least one checkbox exists
    """
    has_stage_sections = bool(re.search(r'^##+ Stage \d+:', issue_body, re.MULTILINE))
    has_acceptance_criteria = bool(re.search(r'^## Acceptance Criteria', issue_body, re.MULTILINE))
    has_checkboxes = bool(re.search(r'^- \[([ x])\]', issue_body, re.MULTILINE))

    issues = []
    if not has_stage_sections:
        issues.append("Missing ##+ Stage X: section headers")
    if not has_acceptance_criteria:
        issues.append("Missing ## Acceptance Criteria section")
    if not has_checkboxes:
        issues.append("No checkboxes found in Issue body")

    if issues:
        print("❌ Issue setup validation failed:")
        for issue in issues:
            print(f"  - {issue}")
        return False

    print("✅ Issue setup valid (has stage sections, acceptance criteria, checkboxes)")
    return True


def validate_stage(stages: Dict[int, List[dict]], stage_num: int, verbose: bool = False) -> bool:
    """
    Validate single stage complete.
    Used by orchestrator END gate.
    """
    if stage_num not in stages:
        print(f"❌ Stage {stage_num} not found in Issue")
        print(f"Available stages: {sorted(stages.keys())}")
        return False

    checkboxes = stages[stage_num]
    if not checkboxes:
        print(f"❌ Stage {stage_num} has no checkboxes")
        return False

    total = len(checkboxes)
    checked = sum(1 for cb in checkboxes if cb['checked'])

    # Count sources
    sources = {}
    for cb in checkboxes:
        source = cb.get('source', 'unknown')
        sources[source] = sources.get(source, 0) + 1

    if checked == total:
        source_summary = ', '.join(f"{count} from {src}" for src, count in sources.items())
        print(f"✅ Stage {stage_num} complete ({checked}/{total} checkboxes from {len(sources)} source(s): {source_summary})")
        if verbose:
            print("\nAll checkboxes ticked:")
            for cb in checkboxes:
                source_label = f"[{cb.get('source', 'unknown')}]"
                print(f"  ✅ {source_label} {cb['text']}")
        return True
    else:
        source_summary = ', '.join(f"{count} from {src}" for src, count in sources.items())
        print(f"❌ Stage {stage_num} incomplete ({checked}/{total} checkboxes from {len(sources)} source(s): {source_summary})")
        print("\nMissing:")
        for cb in checkboxes:
            if not cb['checked']:
                source_label = f"[{cb.get('source', 'unknown')}]"
                print(f"  - [ ] {source_label} {cb['text']}")
        print(f"\n⚠️ BLOCKED: Cannot proceed to Stage {stage_num + 1}")
        return False


def validate_through_stage(stages: Dict[int, List[dict]], through_stage: int, verbose: bool = False) -> bool:
    """
    Validate all stages 0 through N complete.
    Used by subagent START gate.
    """
    if not stages:
        print("❌ No stage sections found in Issue")
        return False

    # Validate each stage 0 through through_stage
    all_passed = True
    total_checkboxes = 0
    total_checked = 0

    for stage_num in range(0, through_stage + 1):
        if stage_num not in stages:
            print(f"❌ Stage {stage_num} not found in Issue")
            all_passed = False
            continue

        checkboxes = stages[stage_num]
        stage_total = len(checkboxes)
        stage_checked = sum(1 for cb in checkboxes if cb['checked'])

        total_checkboxes += stage_total
        total_checked += stage_checked

        if stage_checked < stage_total:
            print(f"❌ Stage {stage_num} incomplete ({stage_checked}/{stage_total} checkboxes)")
            if verbose:
                print("  Missing:")
                for cb in checkboxes:
                    if not cb['checked']:
                        print(f"    - [ ] {cb['text']}")
            all_passed = False
        else:
            print(f"✅ Stage {stage_num} complete ({stage_checked}/{stage_total} checkboxes)")

    print(f"\n{'✅' if all_passed else '❌'} Stages 0-{through_stage}: {total_checked}/{total_checkboxes} checkboxes")

    if not all_passed:
        print(f"⚠️ BLOCKED: Cannot start Stage {through_stage + 1}")

    return all_passed


def validate_all_stages(stages: Dict[int, List[dict]], verbose: bool = False) -> bool:
    """
    Validate all stages complete.
    Used for Issue closure validation.
    """
    if not stages:
        print("❌ No stage sections found in Issue")
        return False

    max_stage = max(stages.keys())
    return validate_through_stage(stages, max_stage, verbose)

def validate_solo_assignment(issue_data: dict, source: str = 'all', verbose: bool = False) -> bool:
    """
    Validate Solo Assignment checkboxes complete.
    Used by Solo mode END gate.

    Args:
        issue_data: Dict with 'body' and 'comments' keys from gh CLI
        source: Where to parse checkboxes from ('body', 'comments', or 'all')
        verbose: Show detailed output

    Returns:
        True if all Solo checkboxes complete, False otherwise
    """
    checkboxes = parse_checkboxes(issue_data, source, mode='solo')

    if 'solo' not in checkboxes:
        print("❌ Solo Assignment section not found in Issue")
        print("Expected header: ## Solo Assignment (SST3 Automated)")
        return False

    solo_checkboxes = checkboxes['solo']
    if not solo_checkboxes:
        print("❌ Solo Assignment section has no checkboxes")
        return False

    total = len(solo_checkboxes)
    checked = sum(1 for cb in solo_checkboxes if cb['checked'])

    # Count sources
    sources = {}
    for cb in solo_checkboxes:
        source_label = cb.get('source', 'unknown')
        sources[source_label] = sources.get(source_label, 0) + 1

    if checked == total:
        source_summary = ', '.join(f"{count} from {src}" for src, count in sources.items())
        print(f"✅ Solo Assignment complete ({checked}/{total} checkboxes from {len(sources)} source(s): {source_summary})")
        if verbose:
            print("\nAll checkboxes ticked:")
            for cb in solo_checkboxes:
                source_label = f"[{cb.get('source', 'unknown')}]"
                print(f"  ✅ {source_label} {cb['text']}")
        return True
    else:
        source_summary = ', '.join(f"{count} from {src}" for src, count in sources.items())
        print(f"❌ Solo Assignment incomplete ({checked}/{total} checkboxes from {len(sources)} source(s): {source_summary})")
        print("\nMissing:")
        for cb in solo_checkboxes:
            if not cb['checked']:
                source_label = f"[{cb.get('source', 'unknown')}]"
                print(f"  - [ ] {source_label} {cb['text']}")
        print("\n⚠️ INCOMPLETE: Solo mode validation failed")
        return False


def check_mode_mutual_exclusion(issue_body: str) -> tuple[bool, str | None]:
    """
    Verify Issue has exactly ONE mode header (Solo OR Stage, not both).

    Args:
        issue_body: Issue body text

    Returns:
        (is_valid, error_message)
        - (True, None): Exactly one mode header found
        - (False, error_message): Both headers found OR neither found
    """
    has_solo = bool(re.search(r'^##+ Solo Assignment', issue_body, re.MULTILINE))
    has_stage = bool(re.search(r'^##+ Stage \d+:', issue_body, re.MULTILINE))

    if has_solo and has_stage:
        return (False, "❌ ERROR: Issue contains BOTH Solo Assignment AND Stage Assignment headers\nIssue must use exactly ONE mode (Solo OR Stages, not both)")

    if not has_solo and not has_stage:
        return (False, "❌ ERROR: Issue contains NEITHER Solo Assignment NOR Stage Assignment header\nIssue must have at least one mode header")

    return (True, None)




def main():
    parser = argparse.ArgumentParser(
        description='Validate GitHub Issue checkboxes for SST3 Solo workflow'
    )
    parser.add_argument('--issue', type=int, required=True,
                       help='GitHub Issue number')
    parser.add_argument('--solo', action='store_true', required=True,
                       help='Validate Solo Assignment complete (Solo mode END gate)')
    parser.add_argument('--source', choices=['body', 'comments', 'all'],
                       default='all',
                       help='Which source to parse: body, comments, or all (default: all)')
    parser.add_argument('--verbose', action='store_true',
                       help='Show detailed output')
    args = parser.parse_args()

    # Fetch Issue
    issue_data = fetch_issue_data(args.issue)

    # Mutual exclusion check
    is_valid, error_msg = check_mode_mutual_exclusion(issue_data['body'])
    if not is_valid:
        print(error_msg)
        sys.exit(EXIT_ERROR)

    # Validate Solo Assignment
    result = validate_solo_assignment(issue_data, args.source, args.verbose)
    sys.exit(EXIT_SUCCESS if result else EXIT_FAILURE)


if __name__ == '__main__':
    main()
