#!/usr/bin/env python3
"""Comprehensive quality audit of entire SST3 system.

Per dotfiles#405 Phase 7: replaced 25+ subprocess.run() spawns with in-process
function calls. quality-check.py now imported as a module via importlib (its
filename has a hyphen so dynamic import is required). Each call wrapped in
try/except with structured logging per AP #12 — failures show file path +
exception, never silent.
"""

import importlib.util
import sys
import traceback
from pathlib import Path


def get_sst3_root() -> Path:
    """Find SST3 root directory."""
    return Path(__file__).parent.parent


def _load_quality_check():
    """Dynamic import of quality-check.py (hyphen prevents normal import)."""
    spec = importlib.util.spec_from_file_location(
        "quality_check", Path(__file__).parent / "quality-check.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_quality_check_inprocess(file_path: Path, qc_module) -> tuple[bool, str]:
    """Run quality-check.py validate_quality() in-process. Wrap in try/except."""
    try:
        results = qc_module.validate_quality(str(file_path))
    except Exception as exc:
        # AP #12: log failure context — file + exception type + message
        print(
            f"[ERROR] quality-check failed for {file_path}: "
            f"{type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        traceback.print_exc(file=sys.stderr)
        return False, ""

    passed = sum(1 for _, (status, _) in results.items() if status)
    total = len(results)
    pct = 100 * passed / max(total, 1)
    summary = f"{passed}/{total} ({pct:.0f}%)"
    return passed == total, summary


def audit_all_markdown(qc_module) -> int:
    """Audit all markdown files in SST3."""
    sst3_root = get_sst3_root()

    print("# SST3 Comprehensive Quality Audit\n")

    directories = ['workflow', 'templates', 'standards', 'reference']
    results: dict[str, bool] = {}

    for directory in directories:
        dir_path = sst3_root / directory
        if not dir_path.exists():
            continue

        print(f"## {directory}/\n")

        for md_file in dir_path.glob('*.md'):
            passed, summary = run_quality_check_inprocess(md_file, qc_module)
            results[str(md_file)] = passed

            symbol = "[OK]" if passed else "[!!]"
            print(f"{symbol} {md_file.name}: {summary}")

        print()

    total = len(results)
    passed = sum(results.values())

    print("\n## Audit Summary")
    print(f"Files checked: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Pass rate: {100*passed/max(total,1):.1f}%")

    if passed == total:
        print("\n[OK] All files pass quality validation")
        return 0
    elif passed >= total * 0.9:
        print("\n[!] Most files pass - review failures")
        return 0
    else:
        print("\n[!!] Multiple quality failures - action required")
        return 1


def main():
    print("\nRunning comprehensive quality audit...\n")

    qc_module = _load_quality_check()
    exit_code = audit_all_markdown(qc_module)

    # Size limits check is small + isolated; in-process import would couple
    # check-size-limits.py main() to this script's exit handling. Keep as
    # subprocess for that one — it's a single call, not 25+.
    import subprocess
    print("\n" + "=" * 60)
    print("\n# Size Limits Check\n")

    sst3_root = get_sst3_root()
    check_script = sst3_root / "scripts" / "check-size-limits.py"

    result = subprocess.run(
        [sys.executable, str(check_script)],
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    if result.returncode != 0 and result.stderr:
        print(result.stderr, file=sys.stderr)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
