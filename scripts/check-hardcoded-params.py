#!/usr/bin/env python3
"""
Hardcoded Parameters Detection Script

Scans codebase for hardcoded magic values that should be in config files.
Exit codes:
  0: No violations found (PASS)
  1: Violations detected (FAIL)
  3: Script/configuration error

Usage:
  python check-hardcoded-params.py <path>
  python check-hardcoded-params.py --allowlist .hardcoded-allowlist <path>
"""

import sys
import re
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Set

from sst3_utils import fix_windows_console, should_ignore_path, collect_source_files  # F1.25 D3 (#406 Phase 9)
fix_windows_console()

# Patterns that indicate hardcoded values (by file type)
HARDCODED_PATTERNS = {
    "python": [
        # Numeric magic values in assignments (not UPPER_CASE)
        {
            "pattern": r"^\s*([a-z_][a-z0-9_]*)\s*=\s*(\d+\.?\d*)\s*(?:#|$)",
            "severity": "error",
            "message": "Hardcoded numeric value",
            "example_fix": "Move to config YAML or use UPPER_CASE constant name"
        },
        # Inline hex colors
        {
            "pattern": r"['\"]#[0-9A-Fa-f]{6}['\"]",
            "severity": "error",
            "message": "Hardcoded hex color",
            "example_fix": "Move to component YAML colors array or CSS variables"
        },
        # Hardcoded URLs (not in comments)
        {
            "pattern": r"^\s*[a-z_][a-z0-9_]*\s*=\s*['\"]https?://[^'\"]+['\"]",
            "severity": "error",
            "message": "Hardcoded URL",
            "example_fix": "Move to .env file or config"
        },
    ],
    "javascript": [
        # Inline hex colors in JSX/JS (not CSS variable)
        {
            "pattern": r"color:\s*['\"]#[0-9A-Fa-f]{6}['\"]",
            "severity": "error",
            "message": "Hardcoded color (should use CSS variable)",
            "example_fix": "Use var(--color-name) instead"
        },
        # backgroundColor with hex
        {
            "pattern": r"backgroundColor:\s*['\"]#[0-9A-Fa-f]{6}['\"]",
            "severity": "error",
            "message": "Hardcoded backgroundColor (should use CSS variable)",
            "example_fix": "Use var(--color-name) instead"
        },
        # rgb/rgba colors inline
        {
            "pattern": r"color:\s*['\"]rgba?\([^)]+\)['\"]",
            "severity": "error",
            "message": "Hardcoded rgb color (should use CSS variable)",
            "example_fix": "Use var(--color-name) instead"
        },
        # Hardcoded pixel values in style objects (except 0)
        {
            "pattern": r"(padding|margin|fontSize|width|height):\s*['\"](\d+)px['\"]",
            "severity": "warning",
            "message": "Hardcoded pixel value (consider CSS variable for consistency)",
            "example_fix": "Use var(--spacing-*) or var(--font-size-*)"
        },
    ],
    "css": [
        # Hex colors in property values (not CSS variable definitions)
        # CSS variable definitions are allowed via ALLOW_PATTERNS
        {
            "pattern": r"^\s*[a-z][a-z-]*:\s*#[0-9A-Fa-f]{6}",
            "severity": "error",
            "message": "Hardcoded color (should use CSS variable)",
            "example_fix": "Use var(--color-name) instead"
        },
    ]
}

# Patterns that ALLOW hardcoding (exceptions)
ALLOW_PATTERNS = [
    # UPPER_CASE constants (intentional)
    r"^\s*[A-Z][A-Z0-9_]+\s*=",
    # Line numbers in error messages
    r"line\s*[:\s]\s*\d+",
    r"Line\s+\d+",
    # Array indices
    r"\[\s*\d+\s*\]",
    # Loop counters
    r"range\s*\(\s*\d+",
    r"for\s+\w+\s+in\s+range",
    # CSS variable definitions (defining, not using)
    r"--[\w-]+:\s*#[0-9A-Fa-f]{6}",
    r"--[\w-]+:\s*\d+px",
    # Common constants that are acceptable
    r"=\s*0\s*[#\n]",  # Zero initialization
    r"=\s*1\s*[#\n]",  # One (boolean-like)
    r"=\s*-1\s*[#\n]", # Negative one (not found sentinel)
    r"=\s*None\s*[#\n]",
    r"=\s*True\s*[#\n]",
    r"=\s*False\s*[#\n]",
    # Type annotations
    r":\s*int\s*=",
    r":\s*float\s*=",
    r":\s*str\s*=",
    # YAML files (config files are where values SHOULD be)
    r"\.ya?ml$",
    # String format specifiers
    r":\.\d+f",
    r":\d+d",
    # Comments explaining why value is hardcoded
    r"#\s*(?:intentional|hardcoded|constant)",
]

# Files/directories to always ignore
IGNORE_PATTERNS = [
    "*/node_modules/*",
    "*/.venv/*",
    "*/venv/*",
    "*/__pycache__/*",
    "*.min.js",
    "*.min.css",
    "*/dist/*",
    "*/build/*",
    "*/.git/*",
    "*/archive/*",
    "check-hardcoded-params.py",  # This script
    "*/tests/*",
    "*/test_*.py",
    "*_test.py",
    "*.test.js",
    "*.test.jsx",
    "*.test.ts",
    "*.test.tsx",
    "*.spec.js",
    "*.spec.ts",
    # Config files where hardcoded values are expected
    "*/variables.css",
    "**/config/*.py",
    "**/config/*.yaml",
    "**/config/*.yml",
    "*.config.js",
    "*.config.ts",
    ".env*",
]


def load_allowlist(allowlist_path: str) -> Set[str]:
    """Load project-specific allowlist file."""
    allowlist = set()
    if allowlist_path and Path(allowlist_path).exists():
        with open(allowlist_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    allowlist.add(line)
    return allowlist


def should_ignore(file_path: Path, allowlist: Set[str]) -> bool:
    """Check if file should be ignored.

    Path-pattern matching delegates to sst3_utils.should_ignore_path
    (Phase 7 dedup, dotfiles#405). The line-format allowlist matching
    after this stays specific to check-hardcoded-params.
    """
    if should_ignore_path(file_path, IGNORE_PATTERNS):
        return True
    file_str = str(file_path).replace('\\', '/')

    # Check project allowlist (file:line format)
    for allowed in allowlist:
        if ':' in allowed:
            allowed_file, _ = allowed.rsplit(':', 1)
            if file_str.endswith(allowed_file) or allowed_file in file_str:
                return False  # Don't ignore file, but line might be allowed
        else:
            if file_str.endswith(allowed) or allowed in file_str:
                return True

    return False


def is_line_allowed(file_path: Path, line_num: int, line: str, allowlist: Set[str]) -> bool:
    """Check if specific line is allowed via patterns or allowlist."""
    file_str = str(file_path).replace('\\', '/')

    # Check global allow patterns
    for pattern in ALLOW_PATTERNS:
        if re.search(pattern, line, re.IGNORECASE):
            return True

    # Check project allowlist (file:line format)
    for allowed in allowlist:
        if ':' in allowed:
            allowed_file, allowed_line = allowed.rsplit(':', 1)
            if (file_str.endswith(allowed_file) or allowed_file in file_str):
                if allowed_line.isdigit() and int(allowed_line) == line_num:
                    return True

    return False


def detect_hardcoded(file_path: Path, allowlist: Set[str]) -> List[Tuple[int, str, str, str, str]]:
    """
    Scan file for hardcoded values.
    Returns: List of (line_number, line_content, severity, message, fix_hint)
    """
    findings = []

    # Determine file type
    ext = file_path.suffix.lower()
    type_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.jsx': 'javascript',
        '.ts': 'javascript',
        '.tsx': 'javascript',
        '.css': 'css',
    }

    file_type = type_map.get(ext)
    if not file_type:
        return findings

    patterns = HARDCODED_PATTERNS.get(file_type, [])

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, start=1):
                # Skip if line is allowed
                if is_line_allowed(file_path, line_num, line, allowlist):
                    continue

                for pattern_def in patterns:
                    if re.search(pattern_def['pattern'], line, re.IGNORECASE):
                        findings.append((
                            line_num,
                            line.strip(),
                            pattern_def['severity'],
                            pattern_def['message'],
                            pattern_def['example_fix']
                        ))
                        break  # Only report first match per line

    except Exception as e:
        print(f"Warning: Could not read {file_path}: {e}", file=sys.stderr)

    return findings


def find_config_system_doc(scan_path: Path) -> str:
    """Find CONFIG_SYSTEM.md relative to scan path."""
    # Try common locations
    candidates = [
        scan_path / "docs/architecture/CONFIG_SYSTEM.md",
        scan_path.parent / "docs/architecture/CONFIG_SYSTEM.md",
        Path("docs/architecture/CONFIG_SYSTEM.md"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return "docs/architecture/CONFIG_SYSTEM.md"


def main():
    parser = argparse.ArgumentParser(description='Detect hardcoded parameters in codebase')
    parser.add_argument('path', help='Path to scan (file or directory)')
    parser.add_argument('--allowlist', help='Project-specific allowlist file (.hardcoded-allowlist)')
    parser.add_argument('--severity', choices=['error', 'warning'], default='error',
                        help='Minimum severity to fail on (default: error)')

    args = parser.parse_args()

    scan_path = Path(args.path)
    if not scan_path.exists():
        print(f"Error: Path does not exist: {args.path}", file=sys.stderr)
        sys.exit(3)

    # Load allowlist
    allowlist_file = args.allowlist
    if not allowlist_file:
        # Try to find .hardcoded-allowlist in scan path
        default_allowlist = scan_path / ".hardcoded-allowlist"
        if default_allowlist.exists():
            allowlist_file = str(default_allowlist)

    allowlist = load_allowlist(allowlist_file)

    # Collect files via shared sst3_utils helper (F1.25 D3 dedup, #406 Phase 9).
    # Was: 6 separate rglob calls, one per extension.
    if scan_path.is_file():
        files_to_scan = [scan_path]
    else:
        files_to_scan = collect_source_files(
            scan_path,
            extensions=['.py', '.js', '.jsx', '.ts', '.tsx', '.css'],
            ignore_patterns=IGNORE_PATTERNS,
        )

    # Scan files
    all_findings = {}
    severity_order = {'error': 2, 'warning': 1}
    fail_threshold = severity_order[args.severity]

    for file_path in files_to_scan:
        if should_ignore(file_path, allowlist):
            continue

        findings = detect_hardcoded(file_path, allowlist)
        if findings:
            all_findings[file_path] = findings

    # Report findings
    if all_findings:
        config_doc = find_config_system_doc(scan_path)

        print("\n" + "=" * 60)
        print("HARDCODED PARAMETERS DETECTED")
        print("=" * 60 + "\n")

        for file_path, findings in sorted(all_findings.items()):
            rel_path = file_path.relative_to(scan_path) if file_path.is_relative_to(scan_path) else file_path
            for line_num, line, severity, message, fix_hint in findings:
                severity_icon = "[ERROR]" if severity == "error" else "[WARNING]"
                print(f"{severity_icon} {message}")
                print(f"  File: {rel_path}")
                print(f"  Line {line_num}: {line[:80]}{'...' if len(line) > 80 else ''}")
                print(f"  Fix: {fix_hint}")
                print()

        print("-" * 60)
        print(f"See: {config_doc}")
        print("-" * 60)
        print("\nTo allowlist a specific line, add to .hardcoded-allowlist:")
        print("  <relative-path>:<line-number>")
        print("\nTo use UPPER_CASE constant name (intentional hardcoding):")
        print("  MAX_RETRIES = 3  # UPPER_CASE = intentional constant")
        print()

        # Determine exit code based on severity
        max_severity = max(severity_order[f[2]] for findings in all_findings.values() for f in findings)
        if max_severity >= fail_threshold:
            total = sum(len(f) for f in all_findings.values())
            print(f"FAIL: {total} hardcoded parameter(s) found")
            sys.exit(1)
        else:
            print(f"PASS: Only warnings found (below {args.severity} threshold)")
            sys.exit(0)
    else:
        print("PASS: No hardcoded parameters detected")
        sys.exit(0)


if __name__ == '__main__':
    main()
