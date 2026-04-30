#!/usr/bin/env python3
"""
Debug Code Detection Script

Scans codebase for common debug code patterns that should not be committed.
Exit codes:
  0: No debug code found (PASS)
  1: Debug code detected (FAIL)
  3: Configuration error

Usage:
  python check-debug-code.py <path>
  python check-debug-code.py --config custom-patterns.yaml <path>
"""

import sys
import re
import yaml
import argparse
from pathlib import Path
from typing import List, Dict, Tuple

from sst3_utils import fix_windows_console, should_ignore_path, collect_source_files

fix_windows_console()

DEFAULT_CONFIG = {
    "patterns": {
        "javascript": [
            {"pattern": r"console\.(log|debug|warn|error|info)\(", "severity": "error", "message": "console.* statement"},
            {"pattern": r"\bdebugger\b", "severity": "error", "message": "debugger statement"},
        ],
        "python": [
            {"pattern": r"\bprint\s*\((?!.*# pylint: disable)", "severity": "warning", "message": "print() for debugging (use structured logger — AP #12)"},
            {"pattern": r"\bpdb\.set_trace\(\)", "severity": "error", "message": "pdb.set_trace()"},
            {"pattern": r"\bbreakpoint\(\)", "severity": "error", "message": "breakpoint()"},
            # AP #12 observability — only the unambiguous single-line silent-swallow forms.
            # The bare `except FOO:` pattern was removed (#406 F1.6) because regexes
            # can't see across lines and a multi-line `except FOO:\n    body` would
            # false-positive. The patterns below are unambiguous: each contains the
            # silencing token (`pass`, `continue`, `return None`, bare `return`)
            # ON THE SAME LINE as the except.
            {"pattern": r"except[\s\w,()]*:\s*pass\b", "severity": "error", "message": "except: pass on one line — AP #12 silent swallow"},
            {"pattern": r"except[\s\w,()]*:\s*continue\b", "severity": "warning", "message": "except: continue — AP #12 silent skip"},
            {"pattern": r"except[\s\w,()]*:\s*return\s+None\b", "severity": "error", "message": "except: return None — AP #12 silent failure"},
            {"pattern": r"except[\s\w,()]*:\s*return\s*$", "severity": "error", "message": "except: bare return — AP #12 silent failure"},
        ],
        "common": [
            {"pattern": r"DEBUG\s*=\s*True", "severity": "warning", "message": "DEBUG flag set to True"},
            {"pattern": r"isDev\s*&&", "severity": "warning", "message": "isDev flag in code"},
            {"pattern": r"^#.*TODO:.*debug", "severity": "info", "message": "Debug TODO comment", "flags": "i"},
        ]
    },
    "ignore_patterns": [
        "*/node_modules/*",
        "*/.venv/*",
        "*/venv/*",
        "*/__pycache__/*",
        "*.min.js",
        "*/dist/*",
        "*/build/*",
        "*/archive/*",
        "archive/*",
    ],
    "allowed_files": [
        "check-debug-code.py",  # This script itself
        "*/test_*.py",          # Test files can have print for test output
        "*/tests/*.py",
        "*_test.py",
        # Verified Intentional #9 (#406): SST3/scripts/*.py are CLI tools that
        # legitimately use print() for user-facing output. Carved out so the
        # warning doesn't fire on hook scripts. Was previously in
        # debug-patterns.yaml; now lives here in the canonical DEFAULT_CONFIG.
        "SST3/scripts/*.py",
        "*/SST3/scripts/*.py",
        "claude/statusline.js",  # CLI tool uses console.log for output
    ]
}

def load_config(config_path: str = None) -> Dict:
    """Load configuration from YAML file or use default.

    Single source of truth is DEFAULT_CONFIG above (dotfiles#406 F1.2).
    The legacy debug-patterns.yaml was deleted because it lacked AP #12
    patterns (empty except, except: pass, return None) and silently
    overrode the in-code config. --config still works for explicit overrides.
    """
    if config_path and Path(config_path).exists():
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except yaml.YAMLError as exc:
            print(
                f"[ERROR] check-debug-code: failed to parse {config_path}: "
                f"{type(exc).__name__}: {exc}",
                file=sys.stderr,
            )
            sys.exit(3)
    return DEFAULT_CONFIG

def should_ignore(file_path: Path, ignore_patterns: List[str], allowed_files: List[str]) -> bool:
    """Thin wrapper. Delegates to sst3_utils.should_ignore_path (Phase 7 dedup, dotfiles#405)."""
    return should_ignore_path(file_path, ignore_patterns, allowed_files)

def detect_debug_code(file_path: Path, patterns: Dict) -> List[Tuple[int, str, str, str]]:
    """
    Scan file for debug code patterns.
    Returns: List of (line_number, pattern_match, severity, message)
    """
    findings = []

    # Determine file type
    ext = file_path.suffix.lower()
    type_map = {
        '.js': 'javascript',
        '.jsx': 'javascript',
        '.ts': 'javascript',
        '.tsx': 'javascript',
        '.py': 'python'
    }

    file_type = type_map.get(ext)
    if not file_type:
        return findings  # Skip unsupported file types

    # Get patterns for this file type + common patterns
    relevant_patterns = patterns.get(file_type, []) + patterns.get('common', [])

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, start=1):
                for pattern_def in relevant_patterns:
                    pattern = pattern_def['pattern']
                    flags = re.IGNORECASE if pattern_def.get('flags') == 'i' else 0

                    if re.search(pattern, line, flags):
                        findings.append((
                            line_num,
                            line.strip(),
                            pattern_def['severity'],
                            pattern_def['message']
                        ))
    except Exception as e:
        print(f"Warning: Could not read {file_path}: {e}", file=sys.stderr)

    return findings

def main():
    parser = argparse.ArgumentParser(description='Detect debug code in codebase')
    parser.add_argument('path', help='Path to scan (file or directory)')
    parser.add_argument('--config', help='Custom pattern configuration YAML file')
    parser.add_argument('--severity', choices=['error', 'warning', 'info'], default='error',
                        help='Minimum severity to fail on (default: error)')

    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)

    # Validate path
    scan_path = Path(args.path)
    if not scan_path.exists():
        print(f"Error: Path does not exist: {args.path}", file=sys.stderr)
        sys.exit(3)

    # Collect files to scan via shared sst3_utils helper (Phase 7 dedup)
    if scan_path.is_file():
        files_to_scan = [scan_path]
    else:
        files_to_scan = collect_source_files(
            scan_path,
            extensions=['.js', '.jsx', '.ts', '.tsx', '.py'],
            ignore_patterns=config['ignore_patterns'],
            allowed_files=config['allowed_files'],
        )

    # Scan files
    all_findings = {}
    severity_order = {'error': 3, 'warning': 2, 'info': 1}
    fail_threshold = severity_order[args.severity]

    for file_path in files_to_scan:
        # collect_source_files already filtered, but keep belt-and-braces
        # for the file-input path which bypasses the filter.
        if should_ignore(file_path, config['ignore_patterns'], config['allowed_files']):
            continue

        findings = detect_debug_code(file_path, config['patterns'])
        if findings:
            all_findings[file_path] = findings

    # Report findings
    if all_findings:
        print("Debug code detected:\n")

        for file_path, findings in sorted(all_findings.items()):
            print(f"{file_path}:")
            for line_num, line, severity, message in findings:
                severity_marker = "[ERROR]" if severity == "error" else "[WARNING]" if severity == "warning" else "[INFO]"
                print(f"  {severity_marker} Line {line_num}: {message}")
                print(f"     {line}")
            print()

        # Determine exit code based on severity
        max_severity = max(severity_order[f[2]] for findings in all_findings.values() for f in findings)
        if max_severity >= fail_threshold:
            print(f"FAIL: Debug code found with severity >= {args.severity}")
            sys.exit(1)
        else:
            print(f"PASS: Only {args.severity}-level issues found below threshold")
            sys.exit(0)
    else:
        print("PASS: No debug code detected")
        sys.exit(0)

if __name__ == '__main__':
    main()
