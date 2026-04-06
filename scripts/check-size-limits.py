#!/usr/bin/env python3
"""
Pre-commit hook to monitor SST3 size limits (advisory).
Provides visibility into token usage - warnings only, not blocking (Quality First: Issue #132).
"""

import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import json

# Import shared configuration
from sst3_limits import LIMITS, count_tokens

# In-memory cache so each markdown file is read ONCE per process
# (was being read 2× before — once in check_component_sizes, again in check_total_size)
_FILE_CONTENT_CACHE: Dict[Path, str] = {}


def _read_md(path: Path) -> str:
    """Read markdown file once, return cached content thereafter."""
    if path in _FILE_CONTENT_CACHE:
        return _FILE_CONTENT_CACHE[path]
    try:
        content = path.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        content = ""
    _FILE_CONTENT_CACHE[path] = content
    return content

# Warning thresholds (percentage of cap)
THRESHOLDS = {
    'yellow': 85,   # Review recommended
    'orange': 90,   # Pruning strongly recommended
    'red': 95,      # Pruning required before next addition
    'error': 100,   # Cannot commit
}

def count_lines(text: str) -> int:
    """Count lines in text."""
    return text.count('\n') + 1

def get_status_emoji(percentage: float) -> str:
    """Get status emoji based on usage percentage."""
    if percentage >= THRESHOLDS['error']:
        return '[ERROR]'
    elif percentage >= THRESHOLDS['red']:
        return '[RED]'
    elif percentage >= THRESHOLDS['orange']:
        return '[ORANGE]'
    elif percentage >= THRESHOLDS['yellow']:
        return '[YELLOW]'
    else:
        return '[OK]'

def check_file_size(filepath: Path, limit: int, is_line_limit: bool = False) -> Optional[Dict]:
    """Check if a file exceeds its size limit."""
    if not filepath.exists():
        return None

    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception:
        return None

    if is_line_limit:
        size = count_lines(content)
        unit = 'lines'
    else:
        size = count_tokens(content)
        unit = 'tokens'

    percentage = (size / limit) * 100
    status = get_status_emoji(percentage)

    return {
        'file': str(filepath),
        'size': size,
        'limit': limit,
        'percentage': percentage,
        'unit': unit,
        'status': status,
        'violation': percentage >= THRESHOLDS['error']
    }

def check_component_sizes(base_path: Path) -> List[Dict]:
    """Check component-level size limits."""
    results = []

    # Check each component directory
    components = ['workflow', 'standards', 'templates', 'reference']
    for component in components:
        component_path = base_path / 'SST3' / component
        if component_path.exists():
            total_tokens = 0
            for md_file in component_path.glob('*.md'):
                # Skip CLAUDE_TEMPLATE.md (template for other repos, not SST3 workflow)
                if md_file.name == 'CLAUDE_TEMPLATE.md':
                    continue
                content = _read_md(md_file)
                if content:
                    total_tokens += count_tokens(content)

            limit = LIMITS.get(f'SST3/{component}', 10000)
            percentage = (total_tokens / limit) * 100
            status = get_status_emoji(percentage)

            results.append({
                'component': f'SST3/{component}',
                'size': total_tokens,
                'limit': limit,
                'percentage': percentage,
                'status': status,
                'violation': percentage >= THRESHOLDS['error']
            })

    return results

def check_total_size(base_path: Path) -> Dict:
    """Check SST3 total size limit."""
    sst3_path = base_path / 'SST3'
    if not sst3_path.exists():
        return None

    total_tokens = 0
    file_count = 0

    for md_file in sst3_path.rglob('*.md'):
        # Skip CLAUDE_TEMPLATE.md (template for other repos, not SST3 workflow)
        if md_file.name == 'CLAUDE_TEMPLATE.md':
            continue

        # Skip tests/ directory - not counted in SST3 token budget (Issue #133)
        if 'tests' in md_file.parts:
            continue

        content = _read_md(md_file)
        if content:
            total_tokens += count_tokens(content)
            file_count += 1

    cap = LIMITS['SST3_TOTAL_CAP']
    target = LIMITS['SST3_TOTAL_TARGET']
    percentage = (total_tokens / cap) * 100
    target_percentage = (total_tokens / target) * 100
    status = get_status_emoji(percentage)

    return {
        'total_tokens': total_tokens,
        'file_count': file_count,
        'target': target,
        'cap': cap,
        'percentage': percentage,
        'target_percentage': target_percentage,
        'status': status,
        'violation': percentage >= THRESHOLDS['error']
    }

def generate_pruning_guidance(violations: List[Dict]) -> str:
    """Generate helpful pruning guidance for violations."""
    guidance = []

    for v in violations:
        if 'file' in v:
            excess = v['size'] - v['limit']
            guidance.append(f"  - {v['file']}: Reduce by {excess} {v['unit']}")
        elif 'component' in v:
            excess = v['size'] - v['limit']
            guidance.append(f"  - {v['component']}/: Reduce by {excess} tokens")
        elif 'total_tokens' in v:
            excess = v['total_tokens'] - v['cap']
            guidance.append(f"  - SST3 total: Reduce by {excess} tokens")

    return '\n'.join(guidance)

def main():
    """Main pre-commit hook function."""
    base_path = Path.cwd()
    violations = []
    warnings = []

    # Check SST3 total size
    total_result = check_total_size(base_path)
    if total_result:
        print(f"\n## SST3 Total Size Check")
        print(f"  Files: {total_result['file_count']}")
        print(f"  Tokens: {total_result['total_tokens']:,} / {total_result['cap']:,} cap ({total_result['percentage']:.1f}%) {total_result['status']}")
        print(f"  Target: {total_result['target']:,} ({total_result['target_percentage']:.1f}% of target)")

        if total_result['violation']:
            violations.append(total_result)
        elif total_result['percentage'] >= THRESHOLDS['orange']:
            warnings.append(total_result)

    # Check component sizes
    print(f"\n## Component Size Checks")
    component_results = check_component_sizes(base_path)
    for result in component_results:
        print(f"  {result['component']}: {result['size']:,} / {result['limit']:,} tokens ({result['percentage']:.1f}%) {result['status']}")

        if result['violation']:
            violations.append(result)
        elif result['percentage'] >= THRESHOLDS['orange']:
            warnings.append(result)

    # Check project-level files
    print(f"\n## Key File Checks")
    key_files = [
        ('CLAUDE.md', True),  # Line limit
    ]

    for filepath, is_line_limit in key_files:
        file_path = base_path / filepath
        limit = LIMITS.get(filepath)
        if limit:
            result = check_file_size(file_path, limit, is_line_limit)
            if result:
                unit_str = f"{result['unit']}"
                print(f"  {filepath}: {result['size']} / {result['limit']} {unit_str} ({result['percentage']:.1f}%) {result['status']}")

                if result['violation']:
                    violations.append(result)
                elif result['percentage'] >= THRESHOLDS['orange']:
                    warnings.append(result)

    # Report results
    print("\n" + "=" * 60)

    if violations:
        print("\n[WARNING] Size limits exceeded - Quality First: Review recommended, not blocking")
        print("\nViolations requiring immediate action:")
        print(generate_pruning_guidance(violations))
        print("\n[ADVISORY] Review token usage - quality decisions, not limits")
        print("   Run: python scripts/suggest-pruning.py")
        return 0  # Advisory only per Quality First philosophy (Issue #132)
    elif warnings:
        print("\n[WARNING] Approaching size limits!")
        print("\nComponents near capacity:")
        for w in warnings:
            if 'file' in w:
                print(f"  - {w['file']}: {w['percentage']:.1f}% of limit")
            elif 'component' in w:
                print(f"  - {w['component']}: {w['percentage']:.1f}% of limit")
            elif 'total_tokens' in w:
                print(f"  - SST3 total: {w['percentage']:.1f}% of limit")
        print("\n[RECOMMENDED] Review and prune before next addition")
        return 0
    else:
        print("\n[OK] All size limits OK")
        return 0

if __name__ == '__main__':
    sys.exit(main())
