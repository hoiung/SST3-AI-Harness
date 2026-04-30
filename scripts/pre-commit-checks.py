#!/usr/bin/env python3
"""
SST3 Pre-Commit Validation Wrapper
Integrates all checks into automated pre-commit workflow.

This script runs:
- check-size-limits.py (block if ERROR)
- Python syntax validation
- JSON/YAML validation for templates

Exit codes:
  0 = Success (commit allowed, may have warnings)
  1 = Error (commit blocked)
"""

import sys
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Tuple, List

from sst3_utils import log_event  # F7.2 structured timing emission

# CONCURRENCY AUDIT (dotfiles#405 Phase 7):
# - check_size_limits: read-only IO (markdown files), writes to local stdout buffer
# - check_observability: read-only IO (Python files), writes to local stdout buffer
# - validate_python_syntax: read-only IO (Python files), writes to local stdout buffer
# Shared mutable state: NONE. No env vars, no temp files, no global counters,
# no shared cwd. Each call captures stdout/stderr into a local Tuple[int, str, str].
# Stdout interleaving is impossible because subprocess.run uses capture_output=True.
# ThreadPoolExecutor(max_workers=3) is safe — IO-bound, GIL releases on subprocess.

def run_command(cmd: List[str], description: str) -> Tuple[int, str, str]:
    """Run a command and capture output. Logs failures to sst3-events.jsonl per AP #12.

    F1.3 (#406 Phase 9): the original implementation swallowed exceptions into
    a 3-tuple `(1, "", error)`. Now logs a structured event for every failure
    so the metrics file records WHY a hook blocked, not just THAT it did.
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        log_event(
            "pre-commit-checks.py",
            "run_command_timeout",
            level="error",
            description=description,
            cmd=" ".join(str(c) for c in cmd),
            timeout_s=30,
        )
        return 1, "", f"{description} timed out after 30s"
    except (OSError, subprocess.SubprocessError) as e:
        log_event(
            "pre-commit-checks.py",
            "run_command_error",
            level="error",
            description=description,
            cmd=" ".join(str(c) for c in cmd),
            error_class=type(e).__name__,
            error_msg=str(e),
        )
        return 1, "", f"{description} failed: {type(e).__name__}: {e}"

def check_size_limits(base_path: Path) -> Tuple[bool, str]:
    """Run check-size-limits.py."""
    script = base_path / 'SST3' / 'scripts' / 'check-size-limits.py'
    if not script.exists():
        return True, "check-size-limits.py not found (skipping)"

    returncode, stdout, stderr = run_command(
        [sys.executable, str(script)],
        "Size limits check"
    )

    # Returncode 1 = ERROR level (block commit)
    # Returncode 0 = OK or WARNING (allow commit)
    if returncode == 1:
        return False, f"[BLOCKED] Token budget exceeded:\n{stdout}\n{stderr}"
    else:
        return True, f"Token budget check: {'PASSED' if returncode == 0 else 'WARNING'}\n{stdout}"

def check_observability(base_path: Path) -> Tuple[bool, str]:
    """Run check-debug-code.py — AP #12 enforcement for observability gaps.

    Detects print() / empty except / silent return None / bare pass patterns
    that violate STANDARDS.md "Observability" + "Fail Fast, No Silent Fallbacks".
    """
    script = base_path / 'SST3' / 'scripts' / 'check-debug-code.py'
    if not script.exists():
        return True, "check-debug-code.py not found (skipping observability check)"

    # Scope to SST3/scripts/ — the AP #12 enforcement target.
    # Statusline.js, markitdown, mcp-server logs are intentional output channels
    # (console.log IS the product), not hidden debug code.
    scan_target = base_path / 'SST3' / 'scripts'

    returncode, stdout, stderr = run_command(
        [sys.executable, str(script), str(scan_target)],
        "Observability/debug-code check"
    )

    # check-debug-code.py: 0=clean, 1=violations, 2=argparse error, 3=config error
    if returncode != 0:
        return False, f"[BLOCKED] Observability check failed (rc={returncode}, AP #12):\n{stdout}\n{stderr}"
    return True, f"Observability check: PASSED\n{stdout}"


def validate_python_syntax(base_path: Path) -> Tuple[bool, str]:
    """Validate Python syntax for SST3 scripts (in-process, dotfiles#406 F1.4).

    Replaced N× py_compile subprocess fork loop with in-process ast.parse —
    eliminates ~25 cold-Python forks per pre-commit run. Single biggest
    pre-commit speedup target per the audit.
    """
    import ast
    scripts_dir = base_path / 'SST3' / 'scripts'
    if not scripts_dir.exists():
        return True, "SST3/scripts not found (skipping)"

    errors = []
    for py_file in scripts_dir.glob('*.py'):
        try:
            source = py_file.read_text(encoding='utf-8', errors='replace')
            ast.parse(source, filename=str(py_file))
        except SyntaxError as e:
            errors.append(f"  - {py_file.name}: line {e.lineno}: {e.msg}")
        except OSError as e:
            errors.append(f"  - {py_file.name}: read failed: {e}")

    if errors:
        return False, f"[BLOCKED] Python syntax errors:\n" + "\n".join(errors)
    else:
        return True, f"Python syntax validation: PASSED ({len(list(scripts_dir.glob('*.py')))} files)"

def main():
    """Main pre-commit validation."""
    # Find repository root
    base_path = Path.cwd()
    while not (base_path / 'SST3').exists() and base_path.parent != base_path:
        base_path = base_path.parent

    if not (base_path / 'SST3').exists():
        print("Error: SST3 directory not found", file=sys.stderr)
        return 1

    print("=" * 70)
    print("SST3 PRE-COMMIT VALIDATION")
    print("=" * 70)

    all_passed = True
    warnings = []

    # Run checks in parallel (3 IO-bound subprocess invocations).
    # Concurrency audit above explains why this is safe.
    checks = [
        ("Token Budget", check_size_limits),
        ("Python Syntax", validate_python_syntax),
        ("Observability (AP #12)", check_observability),
    ]

    results: dict[str, Tuple[bool, str]] = {}
    durations: dict[str, int] = {}
    overall_start = time.monotonic()
    with ThreadPoolExecutor(max_workers=3) as executor:
        future_starts: dict = {}
        futures = {}
        for check_name, check_func in checks:
            f = executor.submit(check_func, base_path)
            futures[f] = check_name
            future_starts[f] = time.monotonic()
        for future in futures:
            check_name = futures[future]
            try:
                results[check_name] = future.result(timeout=60)
                passed = results[check_name][0]
            except Exception as exc:
                results[check_name] = (
                    False,
                    f"[ERROR] {check_name} raised {type(exc).__name__}: {exc}",
                )
                passed = False
            durations[check_name] = int((time.monotonic() - future_starts[future]) * 1000)
            # F7.2: structured timing per hook
            log_event(
                "pre-commit-checks.py",
                "hook_run",
                level="info" if passed else "error",
                check=check_name,
                duration_ms=durations[check_name],
                exit_code=0 if passed else 1,
            )
    log_event(
        "pre-commit-checks.py",
        "hook_run_total",
        level="info",
        duration_ms=int((time.monotonic() - overall_start) * 1000),
        check_count=len(checks),
    )

    # Print results in original order so output is deterministic
    for check_name, _ in checks:
        passed, message = results[check_name]
        print(f"\n[{check_name}]")
        print(message)
        if not passed:
            all_passed = False
        elif "[WARNING]" in message:
            warnings.append(check_name)

    # Summary
    print("\n" + "=" * 70)
    if not all_passed:
        print("[COMMIT BLOCKED]")
        print("Fix the errors above before committing.")
        print("To bypass (emergencies only): git commit --no-verify")
        return 1
    elif warnings:
        print(f"[COMMIT ALLOWED WITH WARNINGS]")
        print(f"Warnings in: {', '.join(warnings)}")
        print("Consider addressing warnings before next commit.")
        return 0
    else:
        print("[ALL CHECKS PASSED]")
        print("Commit allowed.")
        return 0

if __name__ == '__main__':
    sys.exit(main())
