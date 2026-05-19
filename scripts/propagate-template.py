#!/usr/bin/env python3
"""
Propagate SST3 template updates to project repositories.
Safely updates SST3 section while preserving project-specific config.

USAGE:
    # Propagate to single repo
    python propagate-template.py --repo ../<consumer-public-2>

    # Propagate to all configured repos
    python propagate-template.py --all

    # Dry run (show what would change)
    python propagate-template.py --repo ../<consumer-public-2> --dry-run

    # Override CLAUDE.md target filename / boundary marker / template path /
    # project section heading (defaults equal to pre-refactor values; do
    # NOT touch unless you know what you're doing — Issue #493 AC 1.4).
    python propagate-template.py --all --target-claude CLAUDE.md \\
        --marker '<!-- ⚠️ DO NOT MODIFY OR DELETE ANYTHING ABOVE THIS LINE ⚠️ -->'

SAFETY:
    - Extracts SST3 section from CLAUDE_TEMPLATE.md (everything above boundary)
    - Extracts project-specific section from target CLAUDE.md (everything below boundary)
    - Merges sections safely
    - Verifies project content not lost

BOUNDARY MARKER:
    Single source of truth: sst3_utils.BOUNDARY_MARKER (#406 F2.13).
    Boundary-line scanning + atomic write delegated to sst3_block_utils
    (Issue #493 AC 1.3 / 1.4 zero-behavioural-change refactor — shared
    core with the new propagate-block.py).
    Everything above this marker is managed by dotfiles SST3.
    Everything below is project-specific configuration.
"""

import argparse
import sys
from pathlib import Path

from sst3_block_utils import atomic_write, find_boundary_lines
from sst3_utils import BOUNDARY_MARKER  # F2.13: single source of truth

# Number of lines in the boundary block
# ---
# <!-- ====... -->
# <!-- ⚠️ ... -->  <-- This is the marker line
# <!-- ====... -->
# <!-- All content ABOVE... -->
# <!-- Modifications require... -->
# <!-- Project-specific... -->
# <!-- ====... -->
# (That's 7 lines total, but we need to include the blank line after)
BOUNDARY_BLOCK_LINES = 8  # Including the newline after boundary

DEFAULT_TARGET_CLAUDE = "CLAUDE.md"
DEFAULT_TEMPLATE_RELPATH = "SST3/templates/CLAUDE_TEMPLATE.md"
DEFAULT_SECTION_HEADER = "# Project-Specific Configuration"


def find_boundary_line(content: str, marker: str = BOUNDARY_MARKER) -> int:
    """Return line number (0-indexed) of the boundary marker, -1 if absent.

    Thin wrapper around ``sst3_block_utils.find_boundary_lines`` (single-marker
    mode) — kept so the existing call-sites do not need to know about the
    paired-marker variant. Issue #493 AC 1.4 zero-behaviour-change refactor.
    """
    return find_boundary_lines(content, marker)[0]


def extract_sst3_section(
    template_path: Path,
    marker: str = BOUNDARY_MARKER,
) -> tuple[list[str], int]:
    """
    Extract SST3 section from CLAUDE_TEMPLATE.md.

    Args:
        template_path: Path to CLAUDE_TEMPLATE.md
        marker: Boundary marker line content (default = sst3_utils.BOUNDARY_MARKER).

    Returns:
        Tuple of (SST3 section lines with newlines, boundary line number)

    Raises:
        ValueError: If boundary marker not found in template
    """
    content = template_path.read_text(encoding='utf-8')
    lines = content.splitlines(keepends=True)
    boundary_line = find_boundary_line(content, marker)

    if boundary_line == -1:
        raise ValueError(f"Boundary marker not found in template: {template_path}")

    # Find and exclude the TEMPLATE METADATA comment block
    # Look specifically for "TEMPLATE METADATA" to avoid excluding boundary markers
    comment_start = -1
    comment_end = -1
    for i, line in enumerate(lines):
        if 'TEMPLATE METADATA' in line:
            # Find the opening <!-- before this line
            for j in range(i, -1, -1):
                if lines[j].strip().startswith('<!--'):
                    comment_start = j
                    break
        if comment_start != -1 and line.strip() == '-->':
            comment_end = i
            break

    # Build SST3 section excluding the comment block
    sst3_end_line = boundary_line + 5  # End of boundary block

    if comment_start != -1 and comment_end != -1:
        # Take lines before comment, skip comment block, then take rest
        sst3_section = lines[:comment_start] + lines[comment_end + 2:sst3_end_line + 1]
    else:
        # No comment block found, take everything (fallback)
        sst3_section = lines[:sst3_end_line + 1]

    return sst3_section, boundary_line


def extract_project_section(
    target_path: Path,
    content: str | None = None,
    marker: str = BOUNDARY_MARKER,
) -> tuple[list[str], int]:
    """
    Extract project-specific section from target CLAUDE.md.

    Args:
        target_path: Path to target repository's CLAUDE.md
        content: Pre-loaded file content (optional). If provided, avoids
                 re-reading the file. Use this when caller already has the
                 content (e.g. propagate_to_repo loads original_content first).
        marker: Boundary marker line content (default = sst3_utils.BOUNDARY_MARKER).

    Returns:
        Tuple of (project section lines with newlines, boundary line number)

    Raises:
        ValueError: If boundary marker not found in target file
    """
    if content is None:
        content = target_path.read_text(encoding='utf-8')
    lines = content.splitlines(keepends=True)
    boundary_line = find_boundary_line(content, marker)

    if boundary_line == -1:
        raise ValueError(f"Boundary marker not found in target: {target_path}")

    # Extract everything after the boundary block
    # The project section starts after the 7-line boundary block
    project_start_line = boundary_line + 5  # After boundary block
    project_section = lines[project_start_line + 1:]  # +1 to skip the boundary end

    return project_section, boundary_line


def merge_sections(sst3_section: list[str], project_section: list[str]) -> str:
    """
    Merge SST3 and project sections into complete CLAUDE.md with EXACTLY ONE
    blank-line separator. Idempotent: applying merge to already-merged content
    yields identical bytes (no trailing-blank accretion across re-applies).

    dotfiles#495 PI-4 fix (Stage 5 follow-up): pre-fix the
    `if not merged[-1].endswith('\\n\\n')` check was always True because
    each list element is a single readlines() line ending in '\\n', never
    '\\n\\n'. The append fired on every invocation. Furthermore the project
    section is extracted as everything AFTER the boundary marker, so a
    blank line inserted in apply N showed up as a LEADING blank in
    project_section on apply N+1, causing per-apply accretion.

    Idempotent algorithm:
      1. Strip trailing blank lines from sst3_section.
      2. Ensure the last sst3 content line ends with '\\n' (defensive).
      3. Strip leading blank lines from project_section.
      4. Concatenate with exactly one '\\n' separator.

    Args:
        sst3_section: Lines from template (with newlines)
        project_section: Lines from project (with newlines)

    Returns:
        Merged content as string
    """
    sst3_trimmed = list(sst3_section)
    while sst3_trimmed and sst3_trimmed[-1] == '\n':
        sst3_trimmed.pop()
    if sst3_trimmed and not sst3_trimmed[-1].endswith('\n'):
        sst3_trimmed[-1] = sst3_trimmed[-1] + '\n'

    project_trimmed = list(project_section)
    while project_trimmed and project_trimmed[0] == '\n':
        project_trimmed.pop(0)

    merged = sst3_trimmed + ['\n'] + project_trimmed
    return ''.join(merged)


def verify_project_section(
    project_section: list[str],
    target_path: Path,
    section_header: str = DEFAULT_SECTION_HEADER,
) -> bool:
    """
    Verify project section is not empty and has reasonable content.

    Args:
        project_section: Project-specific lines
        target_path: Path to target file (for error messages)
        section_header: Expected H1 heading in the project section.

    Returns:
        True if valid, False otherwise
    """
    project_content = ''.join(project_section).strip()

    if len(project_content) < 100:
        print(f"[WARN] Project section seems too small ({len(project_content)} chars)")
        print(f"   File: {target_path}")
        return False

    # Check for project-specific heading
    if section_header not in project_content:
        print(f"[WARN] Project section missing expected heading: {section_header}")
        print(f"   File: {target_path}")
        return False

    return True


def propagate_to_repo(
    template_path: Path,
    target_repo: Path,
    dry_run: bool = False,
    target_claude_name: str = DEFAULT_TARGET_CLAUDE,
    marker: str = BOUNDARY_MARKER,
    section_header: str = DEFAULT_SECTION_HEADER,
) -> tuple[bool, bool]:
    """
    Propagate template to single repository.

    Args:
        template_path: Path to CLAUDE_TEMPLATE.md
        target_repo: Path to target repository
        dry_run: If True, only show what would change
        target_claude_name: Filename of the per-repo CLAUDE doc.
        marker: Boundary marker line content.
        section_header: Expected project section heading (verify gate).

    Returns:
        (success, actual_drift) per dotfiles#495 AC 3.1 — `actual_drift` is
        True when `(original_content != merged)` (i.e. this repo's CLAUDE.md
        would actually change). In dry-run mode `actual_drift` drives the
        `<N> would update` stdout/stderr marker via main(); in apply mode the
        flag still tracks whether a real change was written.
    """
    target_claude = target_repo / target_claude_name

    if not target_claude.exists():
        print(f"[ERROR] {target_claude} not found")
        return False, False

    print(f"\n{'='*60}")
    print(f"[*] Processing: {target_repo.name}")
    print(f"{'='*60}")

    try:
        # Extract sections
        print("   Extracting SST3 section from template...")
        sst3_section, sst3_boundary = extract_sst3_section(template_path, marker)

        print("   Extracting project section from target...")
        # Read once, pass content to extract_project_section to avoid duplicate read
        original_content = target_claude.read_text(encoding='utf-8')
        project_section, project_boundary = extract_project_section(
            target_claude, original_content, marker
        )

        # Verify project section
        print("   Verifying project section integrity...")
        if not verify_project_section(project_section, target_claude, section_header):
            response = input("   Continue anyway? (y/N): ")
            if response.lower() != 'y':
                print("   [SKIP] Skipped due to verification failure")
                return False, False

        # Merge
        print("   Merging sections...")
        merged = merge_sections(sst3_section, project_section)

        # AC 3.1 (dotfiles#495 FRAG-3): compute actual drift flag — True iff
        # this repo's CLAUDE.md would actually change post-merge.
        actual_drift = original_content != merged

        # Calculate statistics (use cached content)
        original_lines = len(original_content.splitlines())
        merged_lines = len(merged.splitlines())
        sst3_lines = len(sst3_section)
        project_lines = len(project_section)

        print(f"\n   [STATS] Statistics:")
        print(f"      SST3 section:    {sst3_lines} lines (template boundary at line {sst3_boundary})")
        print(f"      Project section: {project_lines} lines (target boundary at line {project_boundary})")
        print(f"      Original total:  {original_lines} lines")
        print(f"      Merged total:    {merged_lines} lines")
        print(f"      Difference:      {merged_lines - original_lines:+d} lines")
        print(f"      Drift (would change): {actual_drift}")

        if dry_run:
            print(f"\n   [OK] Dry run complete - no files modified")
            if actual_drift:
                print(f"      Would update: {target_claude}")
            else:
                print(f"      No change needed: {target_claude} already in sync")
            return True, actual_drift

        # Atomic write merged content (Issue #493 AC 1.4 — delegated to
        # sst3_block_utils.atomic_write for AP #9 single-source).
        print(f"\n   [WRITE] Writing merged content...")
        atomic_write(target_claude, merged)

        print(f"\n   [SUCCESS] Updated: {target_claude}")
        print(f"\n   [NEXT] Next steps:")
        print(f"      1. Review changes: git diff {target_claude_name}")
        print(f"      2. Test configuration: claude chat (verify no errors)")
        print(f"      3. If satisfied: git add {target_claude_name} && git commit")
        print(f"      4. If issues: git checkout {target_claude_name}")

        return True, actual_drift

    except Exception as e:
        print(f"   [ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False, False


def main():
    """Main entry point for script."""
    parser = argparse.ArgumentParser(
        description="Propagate SST3 template updates to project repositories",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Propagate to single repo
    python propagate-template.py --repo ../<consumer-public-2>

    # Dry run first (recommended)
    python propagate-template.py --repo ../<consumer-public-2> --dry-run

    # Propagate to all configured repos
    python propagate-template.py --all

Safety features:
    - Verifies project content not lost
    - Dry run mode to preview changes
    - Shows detailed statistics and diff
        """
    )
    parser.add_argument('--repo', type=Path, help='Target repository path (relative or absolute)')
    parser.add_argument('--all', action='store_true', help='Propagate to all configured repos')
    parser.add_argument('--dry-run', action='store_true', help='Show what would change without modifying files')
    # Issue #493 AC 1.4 — formerly hard-coded values are now CLI args with
    # defaults equal to the pre-refactor behaviour (zero-change refactor).
    parser.add_argument(
        '--target-claude',
        default=DEFAULT_TARGET_CLAUDE,
        help=f'Per-repo CLAUDE doc filename (default: {DEFAULT_TARGET_CLAUDE})',
    )
    parser.add_argument(
        '--marker',
        default=BOUNDARY_MARKER,
        help='Boundary marker line content (default: sst3_utils.BOUNDARY_MARKER)',
    )
    parser.add_argument(
        '--template',
        type=Path,
        default=None,
        help=(
            'Path to source template (default: '
            f'<repo-root>/{DEFAULT_TEMPLATE_RELPATH})'
        ),
    )
    parser.add_argument(
        '--section-header',
        default=DEFAULT_SECTION_HEADER,
        help=f'Expected project section heading (default: "{DEFAULT_SECTION_HEADER}")',
    )
    args = parser.parse_args()

    # Find template (script is in dotfiles/SST3/scripts/)
    script_dir = Path(__file__).parent.resolve()
    sys.path.insert(0, str(script_dir))
    import sst3_mirror_utils as _smu  # noqa: E402

    # #488 Fix-A (Option A) — split the two roots the prior P1 attempt conflated:
    #   * CANONICAL source root  = the tree this script lives in
    #     (`script_dir.parent.parent`). Run from a worktree it is the WORKTREE
    #     (carries the in-flight #488 template edits); run from the merged main
    #     clone it is the main clone (carries them post-merge). Deterministic
    #     path math — no git subprocess, immune to the pre-commit-sandbox env
    #     quirk that silently broke the P1 `--git-common-dir` approach.
    #   * SIBLING base (`devprojects`) = parent of the MAIN clone, derived by
    #     `sst3_mirror_utils.resolve_main_clone_root` (single source of the
    #     env-immune `/.claude/worktrees/` strip — AP #9 dedupe). KNOWN_REPOS
    #     consumers + the dotfiles self-row are siblings of the MAIN clone,
    #     NEVER of a linked worktree (the silent --all no-op the P1 comment
    #     warned about is fixed here without the fragile git call).
    template_src_root = script_dir.parent.parent
    manifest_path = template_src_root / "SST3" / _smu.MANIFEST_FILENAME
    main_clone = _smu.resolve_main_clone_root(manifest_path)

    # AC 2.3 (dotfiles#495 FRAG-1): worktree-aware self-row destination — when
    # run from a linked worktree, the dotfiles self-row CLAUDE.md target is
    # the WORKTREE's CLAUDE.md (in-flight worktree-branch edits land
    # naturally; no post-merge cross-clone `--apply` required). When run from
    # the main clone, this resolves identically to main_clone. The helper
    # `_smu.resolve_self_row_destination` delegates to `resolve_dotfiles_root`
    # for the worktree+dotfiles case and to `resolve_mirror` otherwise; the
    # `.parent` strips the trailing `CLAUDE.md` so we end up with the
    # directory containing it (consumed by `propagate_to_repo` as `repo`).
    dotfiles_self_row_root = _smu.resolve_self_row_destination(
        manifest_path, "dotfiles", "CLAUDE.md"
    ).parent.resolve()
    template = args.template if args.template else (
        template_src_root / "SST3" / "templates" / "CLAUDE_TEMPLATE.md"
    )

    if not template.exists():
        print(f"[ERROR] Template not found: {template}")
        print(f"   Expected location: dotfiles/{DEFAULT_TEMPLATE_RELPATH}")
        sys.exit(1)

    print(f"[TEMPLATE] Using: {template}")

    # Auto-discover sibling repositories under DevProjects/ that:
    #   (a) contain a CLAUDE.md, AND
    #   (b) are listed in sst3_utils.KNOWN_REPOS
    # The KNOWN_REPOS filter (added #460 Stage 5 — angle K finding) prevents
    # special-case repos (intentionally minimal, NO boundary marker, harness-
    # run staging only) from being processed. Without the filter, propagate-
    # to-repo logs "Boundary marker not found" but main() still exits 0,
    # masking partial failure.
    from sst3_utils import KNOWN_REPOS  # noqa: E402

    # Siblings live under the MAIN clone's parent (NEVER a linked worktree's).
    devprojects = main_clone.parent
    discovered = sorted([
        d for d in devprojects.iterdir()
        if d.is_dir() and (d / args.target_claude).exists() and d.name in KNOWN_REPOS
    ])
    # Ensure the dotfiles self-row (per AC 2.3, worktree-aware — see
    # `dotfiles_self_row_root` above) is first.
    if main_clone in discovered:
        discovered.remove(main_clone)
    all_repos = [dotfiles_self_row_root] + discovered

    # Print discovered repos so the user can verify the list before propagation runs
    print(f"\n[DISCOVERED] {len(all_repos)} repos (KNOWN_REPOS ∩ {args.target_claude} present):")
    for r in all_repos:
        print(f"  - {r.name}")

    if args.all:
        print(f"\n[START] Propagating to {len(all_repos)} repositories...")
        success_count = 0
        drift_count = 0
        for repo in all_repos:
            success, drifted = propagate_to_repo(
                template,
                repo,
                args.dry_run,
                target_claude_name=args.target_claude,
                marker=args.marker,
                section_header=args.section_header,
            )
            if success:
                success_count += 1
            if drifted:
                drift_count += 1

        print(f"\n{'='*60}")
        print(f"[SUMMARY] {success_count}/{len(all_repos)} repositories updated successfully")
        print(f"{'='*60}")
        # AC 3.2 (dotfiles#495 FRAG-3): emit machine-parseable summary line
        # to stderr after the --all --dry-run loop completes. Format matches
        # propagate-mirrors.py:213 family — chosen wording: "<N> would update"
        # (no "file(s) checked" prefix because propagate-template iterates
        # repos not files). leader-stage5-drain-check.sh D5 (AC 3.3) parses
        # this marker; downstream gates (Verification Loop / Ralph Review)
        # likewise.
        if args.dry_run:
            # Flush stdout BEFORE writing the stderr marker. Python's stdout
            # is block-buffered when writing to a pipe (e.g. drain-check D5's
            # subprocess capture); without an explicit flush, the buffered
            # stdout tail ("[OK] Dry run complete...") can land on the same
            # line as the stderr marker once the buffer eventually flushes
            # — garbling drain-check.sh's `^[0-9]+ would update$` anchor.
            # Stage 5 L1-C HIGH defect (Ralph caught the same class of bug);
            # belt-and-suspenders with drain-check.sh:356 `2>&1 1>/dev/null`.
            sys.stdout.flush()
            print(f"{drift_count} would update", file=sys.stderr)
        # Exit non-zero on partial failure so callers (Stage 4 Verification
        # Loop, pre-commit hooks) catch the gap. Previous default exit-0
        # silently masked errors (#460 Stage 5 — angle K finding).
        if success_count != len(all_repos):
            sys.exit(1)

    elif args.repo:
        # Resolve relative path from current working directory
        target_repo = Path(args.repo).resolve()
        if not target_repo.exists():
            print(f"[ERROR] Repository not found: {target_repo}")
            sys.exit(1)

        success, drifted = propagate_to_repo(
            template,
            target_repo,
            args.dry_run,
            target_claude_name=args.target_claude,
            marker=args.marker,
            section_header=args.section_header,
        )
        if args.dry_run:
            sys.stdout.flush()  # see --all branch comment above (Stage 5 L1-C)
            print(f"{1 if drifted else 0} would update", file=sys.stderr)
        sys.exit(0 if success else 1)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
