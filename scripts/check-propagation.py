#!/usr/bin/env python3
"""
Pre-commit hook to check CLAUDE template propagation.
Prevents forgotten cross-repo updates when CLAUDE_TEMPLATE.md or CLAUDE.md changes.

BEHAVIOR:
    - Validates SST3 sections in CLAUDE.md match CLAUDE_TEMPLATE.md (blocks if mismatch)
    - Detects changes to CLAUDE_TEMPLATE.md or CLAUDE.md in staged files
    - If CLAUDE.md only: Warns that CLAUDE_TEMPLATE.md might need updating
    - If CLAUDE_TEMPLATE.md: Runs dry-run propagation and offers to propagate now
    - Validation is blocking, warnings are non-blocking

USAGE:
    Called automatically by pre-commit when template files are staged.
    Can also be run manually: python SST3/scripts/check-propagation.py
"""

import subprocess
import sys
from pathlib import Path

from sst3_utils import get_staged_files, KNOWN_REPOS, SST3UtilError, BOUNDARY_MARKER, log_event  # F2.13

# Repositories to validate (relative to dotfiles parent directory).
# Sourced from sst3_utils.KNOWN_REPOS — single source of truth.
REPOS = KNOWN_REPOS


def check_template_changed():
    """
    Check if CLAUDE_TEMPLATE.md or CLAUDE.md is in staged files.

    Returns:
        Tuple of (template_changed: bool, dotfiles_claude_changed: bool)
    """
    try:
        staged = get_staged_files()
    except SST3UtilError as exc:
        print(f"[ERROR] check-propagation: {exc}", file=sys.stderr)
        sys.exit(1)
    template_changed = 'SST3/templates/CLAUDE_TEMPLATE.md' in staged
    dotfiles_claude_changed = 'CLAUDE.md' in staged
    return template_changed, dotfiles_claude_changed


def run_dry_run_propagation():
    """
    Run propagation script in dry-run mode to preview changes.

    Returns:
        Tuple of (success: bool, output: str)
    """
    script_dir = Path(__file__).parent.resolve()
    script = script_dir / 'propagate-template.py'

    try:
        result = subprocess.run(
            [sys.executable, str(script), '--all', '--dry-run'],
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0, result.stdout
    except subprocess.TimeoutExpired:
        return False, "[ERROR] Dry-run propagation timed out"
    except Exception as e:
        return False, f"[ERROR] Failed to run dry-run: {e}"


def ask_user(question, default='n'):
    """
    Ask user a yes/no/skip question.

    Args:
        question: Question to ask
        default: Default answer ('y' or 'n')

    Returns:
        True for yes, False for no, None for skip
    """
    if not sys.stdin.isatty():
        # F1.12 (#406 Phase 9): structured log when non-tty fallback fires.
        # The original commit kept a plain print(); audit caught it as a
        # missing observability point.
        log_event(
            "check-propagation.py",
            "ask_user_non_tty_default",
            level="info",
            question=question,
            default=default,
        )
        print(f"   (Non-interactive mode, using default: {default})")
        return default == 'y'

    prompt = f"{question} [y/N/skip]: " if default == 'n' else f"{question} [Y/n/skip]: "

    try:
        response = input(prompt).strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\n   (Skipping due to interrupt)")
        return None

    if response == 'skip':
        print("   Skipping propagation check this time.")
        return None

    return response in ['y', 'yes'] if default == 'n' else response not in ['n', 'no']


def extract_sst3_section(file_path):
    """
    Extract SST3 section from a CLAUDE file (everything above boundary marker).

    Args:
        file_path: Path to CLAUDE file

    Returns:
        List of lines in SST3 section, or None if file doesn't exist or no marker found
    """
    if not file_path.exists():
        return None

    try:
        content = file_path.read_text(encoding='utf-8')
        lines = content.splitlines()

        # Find boundary marker
        boundary_line = -1
        for i, line in enumerate(lines):
            if BOUNDARY_MARKER in line:
                boundary_line = i
                break

        if boundary_line == -1:
            return None

        # Return everything up to (but not including) the boundary marker line
        return lines[:boundary_line]

    except Exception as e:
        print(f"[ERROR] Failed to read {file_path}: {e}")
        return None


def validate_sst3_sections():
    """
    Validate that SST3 sections in all repos' CLAUDE.md match CLAUDE_TEMPLATE.md.

    Returns:
        Tuple of (valid: bool, mismatches: list of repo names)
    """
    script_dir = Path(__file__).parent.resolve()
    dotfiles_root = script_dir.parent.parent  # SST3/scripts -> SST3 -> dotfiles
    parent_dir = dotfiles_root.parent  # dotfiles -> DevProjects

    template_path = dotfiles_root / 'SST3' / 'templates' / 'CLAUDE_TEMPLATE.md'

    # Extract template SST3 section
    template_section = extract_sst3_section(template_path)
    if template_section is None:
        print(f"[ERROR] Cannot extract SST3 section from {template_path}")
        return False, []

    mismatches = []

    # Check each repo
    for repo in REPOS:
        claude_path = parent_dir / repo / 'CLAUDE.md'

        if not claude_path.exists():
            print(f"[WARNING] {claude_path} not found, skipping validation")
            continue

        repo_section = extract_sst3_section(claude_path)

        if repo_section is None:
            print(f"[ERROR] Cannot extract SST3 section from {claude_path}")
            mismatches.append(repo)
            continue

        # Compare sections
        if repo_section != template_section:
            mismatches.append(repo)

    return len(mismatches) == 0, mismatches


def propagate_now():
    """
    Run propagation script for real (non-dry-run mode).

    AP #16 (dotfiles#406 F1.11): subprocess cleanup in finally so any
    exception path (not just TimeoutExpired) reaps the child process.

    Returns:
        True if successful, False otherwise
    """
    script_dir = Path(__file__).parent.resolve()
    script = script_dir / 'propagate-template.py'

    proc = None
    try:
        proc = subprocess.Popen(
            [sys.executable, str(script), '--all'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        stdout, _ = proc.communicate(timeout=120)
        if stdout:
            print(stdout)
        return proc.returncode == 0
    except subprocess.TimeoutExpired:
        print("\n[ERROR] Propagation timed out")
        return False
    except (OSError, subprocess.SubprocessError) as exc:
        print(
            f"\n[ERROR] Failed to run propagation: "
            f"{type(exc).__name__}: {exc}"
        )
        return False
    finally:
        if proc and proc.poll() is None:
            proc.kill()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass


def main():
    """Main entry point for pre-commit hook."""
    # CRITICAL: Validate SST3 sections match across all repos FIRST
    # This catches rogue modifications to the SST3-managed section
    print("\n" + "="*60)
    print("CLAUDE Template Validation")
    print("="*60)
    print("\nValidating SST3 sections across all repositories...")

    valid, mismatches = validate_sst3_sections()

    if not valid:
        print("\n[ERROR] SST3 section mismatch detected!")
        print("\nThe following repositories have SST3 sections that don't match CLAUDE_TEMPLATE.md:")
        for repo in mismatches:
            print(f"   - {repo}")
        print("\n[CAUSE] Someone modified the SST3-managed section (above the boundary marker)")
        print("        instead of just the project-specific section.")
        print("\n[FIX] Run propagation to sync SST3 sections:")
        print("      cd dotfiles")
        print("      python SST3/scripts/propagate-template.py --all")
        print("\n      Then review and commit the changes in each repository.")
        print("\n" + "="*60 + "\n")
        sys.exit(1)  # BLOCK commit - this is a critical error

    print("[OK] All SST3 sections match CLAUDE_TEMPLATE.md")
    print("="*60)

    # Continue with normal propagation checks
    template_changed, claude_changed = check_template_changed()

    if not template_changed and not claude_changed:
        # No relevant files changed - validation passed, allow commit
        sys.exit(0)

    print("\n" + "="*60)
    print("CLAUDE Template Change Detected")
    print("="*60)

    # Case 1: CLAUDE.md changed but not CLAUDE_TEMPLATE.md
    if claude_changed and not template_changed:
        print("\n[WARNING] You're committing CLAUDE.md changes.")
        print("   Did you also update CLAUDE_TEMPLATE.md?")
        print("\n   REMINDER:")
        print("   - CLAUDE_TEMPLATE.md is the SST3 master template")
        print("   - CLAUDE.md is the dotfiles instance")
        print("\n   If this is a project-specific dotfiles change, ignore this warning.")
        print("   If this is an SST3 template update, update CLAUDE_TEMPLATE.md instead.")
        print("\n" + "="*60 + "\n")
        sys.exit(0)  # Don't block commit

    # Case 2: CLAUDE_TEMPLATE.md changed (may or may not include CLAUDE.md)
    if template_changed:
        print("\n[OK] CLAUDE_TEMPLATE.md changed - checking propagation...\n")

        success, output = run_dry_run_propagation()

        if not success:
            print("[ERROR] Dry-run propagation failed. Check the script.")
            print("\n" + output)
            print("\n[WARNING] Commit will proceed, but please fix propagation manually:")
            print("   python SST3/scripts/propagate-template.py --all")
            print("\n" + "="*60 + "\n")
            sys.exit(0)  # Don't block commit even on failure

        # Show dry-run output
        print(output)

        # Ask user if they want to propagate now
        print()
        response = ask_user("Propagate these changes to other repositories now?", default='n')

        if response is None:
            # Skip was selected
            print("\n[REMINDER] Run propagation manually later:")
            print("   python SST3/scripts/propagate-template.py --all")
            print("\n" + "="*60 + "\n")
            sys.exit(0)

        if response:
            print("\n[INFO] Propagating changes...\n")
            if propagate_now():
                print("\n[SUCCESS] Propagation complete!")
                print("\n   NEXT STEPS:")
                print("   1. Review the changes in each repository")
                print("   2. Stage updated CLAUDE.md files if satisfied")
                print("   3. Create separate commits in each repo")
                print("\n" + "="*60 + "\n")
            else:
                print("\n[ERROR] Propagation failed. Run manually:")
                print("   python SST3/scripts/propagate-template.py --all")
                print("\n" + "="*60 + "\n")
        else:
            print("\n[REMINDER] Run propagation manually later:")
            print("   python SST3/scripts/propagate-template.py --all")
            print("\n   IMPORTANT:")
            print("   - Other repositories are now out of sync")
            print("   - Propagate as soon as possible")
            print("\n" + "="*60 + "\n")

    # Exit 0 - warnings are non-blocking (validation already passed)
    sys.exit(0)


if __name__ == '__main__':
    main()
