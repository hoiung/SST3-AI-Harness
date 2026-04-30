#!/usr/bin/env python3
"""
[#406 Phase 9 — MANUAL UTILITY] Not wired into .pre-commit-config.yaml or CI by design. Invoke directly when needed (manual workflow tool, not a per-commit hook).

check-fallbacks.py - Detect silent fallback patterns in codebase

Part of SST3 workflow. Enforces STANDARDS.md "Fail Fast, No Silent Fallbacks" principle.

Usage:
    python check-fallbacks.py [OPTIONS] [PATH]

Exit codes:
    0 - No violations
    1 - Violations found
    2 - Error
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import List, Dict, Set, NamedTuple, Optional

from sst3_utils import collect_source_files  # F1.25 D2 dedup (#406 Phase 9)


class Violation(NamedTuple):
    """Represents a detected fallback violation."""
    file: str
    line: int
    pattern: str
    code: str
    severity: str


# Pattern definitions for each language
# Format: (regex_pattern, description, severity)
PATTERNS = {
    'python': [
        # Issue #900: FORBIDDEN error indicators (must use "ER" not these)
        (r'\bor\s+["\']N/A["\']', 'FORBIDDEN: "N/A" error indicator (use "ER")', 'error'),
        (r'\bor\s+["\']n/a["\']', 'FORBIDDEN: "n/a" error indicator (use "ER")', 'error'),
        (r'\bor\s+["\']-["\']', 'FORBIDDEN: "-" error indicator (use "ER")', 'error'),
        (r'\bor\s+["\']--["\']', 'FORBIDDEN: "--" error indicator (use "ER")', 'error'),
        (r'\belse\s+["\']N/A["\']', 'FORBIDDEN: "N/A" error indicator (use "ER")', 'error'),
        (r'\belse\s+["\']n/a["\']', 'FORBIDDEN: "n/a" error indicator (use "ER")', 'error'),
        (r'\belse\s+["\']-["\']', 'FORBIDDEN: "-" error indicator (use "ER")', 'error'),
        (r'\belse\s+["\']--["\']', 'FORBIDDEN: "--" error indicator (use "ER")', 'error'),
        (r'if\s+.*\s+else\s+0\.0\s*$', 'FORBIDDEN: else 0.0 masks errors (use None)', 'error'),
        (r'if\s+.*\s+else\s+0\s*$', 'FORBIDDEN: else 0 masks errors (use None)', 'error'),
        # Runtime fallbacks
        (r'\.get\s*\([^,)]+,\s*[^)]+\)', 'dict.get() with default', 'warning'),
        (r'getenv\s*\([^,)]+,\s*[^)]+\)', 'os.getenv() with default', 'warning'),
        (r'\bor\s+["\'][^"\']+["\']', 'or with string default', 'warning'),
        (r'\bor\s+\d+', 'or with numeric default', 'warning'),
        (r'\bor\s+\[\]', 'or with empty list default', 'warning'),
        (r'\bor\s+\{\}', 'or with empty dict default', 'warning'),
        (r'\bor\s+None\b', 'or with None default', 'info'),
        (r'\bor\s+False\b', 'or with False default', 'info'),
        (r'\bor\s+True\b', 'or with True default', 'info'),
        # Function/method default parameters (configuration values should come from YAML)
        (r'def\s+\w+\s*\([^)]*:\s*int\s*=\s*\d+', 'function param with int default', 'warning'),
        (r'def\s+\w+\s*\([^)]*:\s*float\s*=\s*[\d.]+', 'function param with float default', 'warning'),
        (r'def\s+\w+\s*\([^)]*:\s*str\s*=\s*["\']', 'function param with str default', 'warning'),
        (r'def\s+\w+\s*\([^)]*:\s*bool\s*=\s*(True|False)', 'function param with bool default', 'info'),
        (r'def\s+\w+\s*\([^)]*:\s*list\s*=\s*\[', 'function param with list default', 'warning'),
        (r'def\s+\w+\s*\([^)]*:\s*dict\s*=\s*\{', 'function param with dict default', 'warning'),
        # Untyped default parameters
        (r'def\s+\w+\s*\([^)]*\w+\s*=\s*\d+[,)]', 'untyped param with numeric default', 'warning'),
        (r'def\s+\w+\s*\([^)]*\w+\s*=\s*["\'][^"\']*["\'][,)]', 'untyped param with string default', 'warning'),
        # Class/module-level configuration constants (should come from YAML)
        # MIN/MAX bounds
        (r'^\s*(PERIOD_MIN|PERIOD_MAX|MIN_\w+|MAX_\w+)\s*=\s*\d+', 'class constant MIN/MAX bound', 'warning'),
        # DEFAULT_* constants
        (r'^\s*DEFAULT_\w+\s*=\s*[\d.]+', 'DEFAULT_* numeric constant', 'warning'),
        (r'^\s*DEFAULT_\w+\s*=\s*["\']', 'DEFAULT_* string constant', 'warning'),
        # Infrastructure config constants (rate limits, retries, delays)
        (r'^\s*(RATE_LIMIT|RETRY|TIMEOUT|DELAY)\w*\s*=\s*[\d.]+', 'infrastructure config constant', 'warning'),
        # Tolerance/threshold constants at module level
        (r'^[A-Z][A-Z_]*TOLERANCE\s*=\s*[\d.]+', 'module-level tolerance constant', 'warning'),
        (r'^[A-Z][A-Z_]*THRESHOLD\s*=\s*[\d.]+', 'module-level threshold constant', 'warning'),
        # Issue #900: Hardcoded indicator parameters in constructor/function CALLS
        # These should come from config, not be hardcoded in the call site
        (r'\(\s*period\s*=\s*\d+', 'hardcoded period= in call (should load from config)', 'warning'),
        (r'\(\s*fast\s*=\s*\d+', 'hardcoded fast= in call (should load from config)', 'warning'),
        (r'\(\s*slow\s*=\s*\d+', 'hardcoded slow= in call (should load from config)', 'warning'),
        (r',\s*signal\s*=\s*\d+', 'hardcoded signal= in call (should load from config)', 'warning'),
        (r'\(\s*atr_period\s*=\s*\d+', 'hardcoded atr_period= in call (should load from config)', 'warning'),
        (r'\(\s*rsi_period\s*=\s*\d+', 'hardcoded rsi_period= in call (should load from config)', 'warning'),
        (r'threshold\s*=\s*0\.\d+', 'hardcoded threshold in call (should load from config)', 'warning'),
        (r'tolerance\s*=\s*0\.\d+', 'hardcoded tolerance in call (should load from config)', 'warning'),
    ],
    'javascript': [
        # Issue #900: FORBIDDEN error indicators (must use "ER" not these)
        (r'\|\|\s*["\']N/A["\']', 'FORBIDDEN: "N/A" error indicator (use "ER")', 'error'),
        (r'\|\|\s*["\']-["\']', 'FORBIDDEN: "-" error indicator (use "ER")', 'error'),
        (r'\|\|\s*["\']--["\']', 'FORBIDDEN: "--" error indicator (use "ER")', 'error'),
        (r'\?\?\s*["\']N/A["\']', 'FORBIDDEN: "N/A" error indicator (use "ER")', 'error'),
        (r'\?\?\s*["\']-["\']', 'FORBIDDEN: "-" error indicator (use "ER")', 'error'),
        (r'\?\?\s*["\']--["\']', 'FORBIDDEN: "--" error indicator (use "ER")', 'error'),
        (r'\?\?\s*0\s*[;,)]', 'FORBIDDEN: ?? 0 masks errors (use "NaN" for data attrs)', 'error'),
        (r':\s*0\s*[,}]', 'FORBIDDEN: default 0 in object may mask errors', 'warning'),
        # Runtime fallbacks
        (r'\|\|\s*["\'][^"\']+["\']', '|| with string default', 'warning'),
        (r'\|\|\s*\d+', '|| with numeric default', 'warning'),
        (r'\|\|\s*\[\]', '|| with empty array default', 'warning'),
        (r'\|\|\s*\{\}', '|| with empty object default', 'warning'),
        (r'\?\?\s*["\'][^"\']+["\']', '?? with string default', 'warning'),
        (r'\?\?\s*\d+', '?? with numeric default', 'warning'),
        (r'\?\?\s*\[\]', '?? with empty array default', 'warning'),
        (r'\?\?\s*\{\}', '?? with empty object default', 'warning'),
    ],
}
# TypeScript uses identical patterns to JavaScript
PATTERNS['typescript'] = PATTERNS['javascript']

# File extension to language mapping
EXTENSION_MAP = {
    '.py': 'python',
    '.js': 'javascript',
    '.jsx': 'javascript',
    '.ts': 'typescript',
    '.tsx': 'typescript',
}

# Default exclusions
DEFAULT_EXCLUDE_DIRS = {
    'node_modules', '.git', '__pycache__', 'venv', 'env',
    'build', 'dist', '.pytest_cache', '.mypy_cache', 'coverage'
}

DEFAULT_EXCLUDE_PATTERNS = {
    '*.min.js', '*.bundle.js', '*.map', '*.pyc', '*.pyo'
}


class AllowlistEntry(NamedTuple):
    """Represents an allowlisted violation."""
    file: str
    line: int
    reason: str


def load_allowlist(allowlist_path: Path) -> Set[tuple]:
    """
    Load allowlist from file.

    Format: file:line # reason for allowing

    Returns:
        Set of (file, line) tuples that are allowed
    """
    allowlist = set()

    if not allowlist_path.exists():
        return allowlist

    try:
        with open(allowlist_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()

                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue

                # Parse format: file:line # reason
                if '#' in line:
                    location, reason = line.split('#', 1)
                    location = location.strip()
                    reason = reason.strip()
                else:
                    location = line
                    reason = "No reason provided"

                # Parse file:line
                if ':' not in location:
                    print(f"Warning: Invalid allowlist format at line {line_num}: {line}",
                          file=sys.stderr)
                    continue

                try:
                    file_path, line_str = location.rsplit(':', 1)
                    line_no = int(line_str)
                    allowlist.add((file_path.strip(), line_no))
                except (ValueError, AttributeError):
                    print(f"Warning: Invalid allowlist format at line {line_num}: {line}",
                          file=sys.stderr)
                    continue

    except Exception as e:
        print(f"Error reading allowlist: {e}", file=sys.stderr)

    return allowlist


def is_excluded(path: Path, exclude_patterns: Set[str], exclude_dirs: Set[str]) -> bool:
    """Check if path should be excluded based on patterns and directories."""

    # Check if any parent directory is excluded
    for part in path.parts:
        if part in exclude_dirs:
            return True

    # Check if filename matches exclude patterns
    for pattern in exclude_patterns:
        if path.match(pattern):
            return True

    return False


def scan_file(file_path: Path, language: str, min_severity: str) -> List[Violation]:
    """
    Scan a single file for fallback patterns.

    Args:
        file_path: Path to the file to scan
        language: Language type (python, javascript, typescript)
        min_severity: Minimum severity level to report

    Returns:
        List of violations found (deduplicated by line number)
    """
    violations = []
    seen_lines = set()  # Track (line_num) to avoid duplicates
    severity_levels = {'info': 0, 'warning': 1, 'error': 2}
    min_level = severity_levels.get(min_severity, 0)

    if language not in PATTERNS:
        return violations

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                # Skip comments
                stripped = line.strip()
                if language == 'python' and stripped.startswith('#'):
                    continue
                if language in ('javascript', 'typescript') and (
                    stripped.startswith('//') or stripped.startswith('/*')
                ):
                    continue

                # Check each pattern (first match wins per line)
                for pattern, description, severity in PATTERNS[language]:
                    if severity_levels.get(severity, 0) < min_level:
                        continue

                    if re.search(pattern, line):
                        # Deduplicate: only report first pattern match per line
                        if line_num not in seen_lines:
                            seen_lines.add(line_num)
                            violations.append(Violation(
                                file=str(file_path),
                                line=line_num,
                                pattern=description,
                                code=line.strip(),
                                severity=severity
                            ))
                        break  # Stop checking patterns for this line

    except Exception as e:
        print(f"Error scanning {file_path}: {e}", file=sys.stderr)

    return violations


def scan_directory(
    root_path: Path,
    exclude_patterns: Set[str],
    exclude_dirs: Set[str],
    min_severity: str
) -> List[Violation]:
    """
    Recursively scan directory for fallback patterns.

    F1.25 D2 dedup (#406 Phase 9): file-collection now delegates to
    sst3_utils.collect_source_files. The local is_excluded() filter is still
    applied as a second pass for the dir-name + file-glob exclude semantics
    that should_ignore_path doesn't exactly match.

    Args:
        root_path: Root directory to scan
        exclude_patterns: File patterns to exclude
        exclude_dirs: Directory names to exclude
        min_severity: Minimum severity level to report

    Returns:
        List of all violations found
    """
    all_violations = []
    extensions = list(EXTENSION_MAP.keys())
    candidates = collect_source_files(root_path, extensions=extensions)

    for file_path in candidates:
        if is_excluded(file_path, exclude_patterns, exclude_dirs):
            continue
        language = EXTENSION_MAP.get(file_path.suffix)
        if not language:
            continue
        violations = scan_file(file_path, language, min_severity)
        all_violations.extend(violations)

    return all_violations


def filter_allowlisted(
    violations: List[Violation],
    allowlist: Set[tuple]
) -> List[Violation]:
    """Filter out allowlisted violations."""
    if not allowlist:
        return violations

    filtered = []
    for v in violations:
        # Normalize path to forward slashes for cross-platform comparison
        # Allowlist uses forward slashes (POSIX-style) regardless of platform
        normalized_file = Path(v.file).as_posix()
        if (normalized_file, v.line) not in allowlist and (v.file, v.line) not in allowlist:
            filtered.append(v)

    return filtered


def print_violations(violations: List[Violation], output_json: bool = False):
    """Print violations in requested format."""

    if output_json:
        output = []
        for v in violations:
            output.append({
                'file': v.file,
                'line': v.line,
                'pattern': v.pattern,
                'code': v.code,
                'severity': v.severity
            })
        print(json.dumps(output, indent=2))
    else:
        # Group by file for readability
        by_file = {}
        for v in violations:
            if v.file not in by_file:
                by_file[v.file] = []
            by_file[v.file].append(v)

        # Print grouped violations
        for file_path in sorted(by_file.keys()):
            print(f"\n{file_path}:")
            for v in sorted(by_file[file_path], key=lambda x: x.line):
                print(f"  {v.line}: [{v.severity.upper()}] FALLBACK DETECTED: {v.pattern}")
                print(f"      {v.code}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Detect silent fallback patterns in codebase',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python check-fallbacks.py .
  python check-fallbacks.py --exclude-dir tests --exclude "*.test.py" src/
  python check-fallbacks.py --severity warning --json .

Allowlist format (.fallback-allowlist):
  path/to/file.py:42 # Legacy code, planned refactor in #123
  src/config.py:15 # Environment variable with safe default
        """
    )

    parser.add_argument(
        'path',
        nargs='?',
        default='.',
        help='Path to scan (default: current directory)'
    )

    parser.add_argument(
        '--exclude',
        action='append',
        default=[],
        metavar='PATTERN',
        help='Exclude files matching pattern (can repeat)'
    )

    parser.add_argument(
        '--exclude-dir',
        action='append',
        default=[],
        metavar='DIR',
        help='Exclude directory (can repeat)'
    )

    parser.add_argument(
        '--severity',
        choices=['info', 'warning', 'error'],
        default='info',
        help='Minimum severity to report (default: info)'
    )

    parser.add_argument(
        '--json',
        action='store_true',
        help='Output as JSON'
    )

    parser.add_argument(
        '--allowlist',
        type=str,
        default='.fallback-allowlist',
        help='Path to allowlist file (default: .fallback-allowlist)'
    )

    parser.add_argument(
        '--no-allowlist',
        action='store_true',
        help='Ignore allowlist file'
    )

    args = parser.parse_args()

    # Validate path
    scan_path = Path(args.path)
    if not scan_path.exists():
        print(f"Error: Path does not exist: {scan_path}", file=sys.stderr)
        return 2

    # Build exclusion sets
    exclude_patterns = DEFAULT_EXCLUDE_PATTERNS.copy()
    exclude_patterns.update(args.exclude)

    exclude_dirs = DEFAULT_EXCLUDE_DIRS.copy()
    exclude_dirs.update(args.exclude_dir)

    # Load allowlist
    allowlist = set()
    if not args.no_allowlist:
        allowlist_path = Path(args.allowlist)
        # Resolve relative to current working directory, not scan path
        if not allowlist_path.is_absolute():
            allowlist_path = Path.cwd() / allowlist_path
        allowlist = load_allowlist(allowlist_path)
        if allowlist:
            print(f"Loaded {len(allowlist)} allowlist entries from {allowlist_path}",
                  file=sys.stderr)

    # Scan for violations
    if scan_path.is_file():
        language = EXTENSION_MAP.get(scan_path.suffix)
        if not language:
            print(f"Error: Unsupported file type: {scan_path.suffix}", file=sys.stderr)
            return 2
        violations = scan_file(scan_path, language, args.severity)
    else:
        violations = scan_directory(
            scan_path,
            exclude_patterns,
            exclude_dirs,
            args.severity
        )

    # Filter allowlisted violations
    violations = filter_allowlisted(violations, allowlist)

    # Print results
    if violations:
        if not args.json:
            print(f"Found {len(violations)} fallback violation(s):\n", file=sys.stderr)
        print_violations(violations, args.json)
        return 1
    else:
        if not args.json:
            print("No fallback violations found.", file=sys.stderr)
        return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(2)
