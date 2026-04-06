#!/usr/bin/env python3
"""
Propagate SST3 template updates to project repositories.
Safely updates SST3 section while preserving project-specific config.

USAGE:
    # Propagate to single repo
    python propagate-template.py --repo ../tradebook_GAS

    # Propagate to all configured repos
    python propagate-template.py --all

    # Dry run (show what would change)
    python propagate-template.py --repo ../tradebook_GAS --dry-run

SAFETY:
    - Extracts SST3 section from CLAUDE_TEMPLATE.md (everything above boundary)
    - Extracts project-specific section from target CLAUDE.md (everything below boundary)
    - Merges sections safely
    - Verifies project content not lost

BOUNDARY MARKER:
    Single source of truth: sst3_utils.BOUNDARY_MARKER (#406 F2.13).
    Everything above this marker is managed by dotfiles SST3.
    Everything below is project-specific configuration.
"""

import argparse
import sys
from pathlib import Path

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


def find_boundary_line(content: str) -> int:
    """
    Find the line number containing the boundary marker.

    Args:
        content: File content as string

    Returns:
        Line number (0-indexed) where boundary marker is found, or -1 if not found
    """
    lines = content.splitlines()
    for i, line in enumerate(lines):
        if BOUNDARY_MARKER in line:
            return i
    return -1


def extract_sst3_section(template_path: Path) -> tuple[list[str], int]:
    """
    Extract SST3 section from CLAUDE_TEMPLATE.md.

    Args:
        template_path: Path to CLAUDE_TEMPLATE.md

    Returns:
        Tuple of (SST3 section lines with newlines, boundary line number)

    Raises:
        ValueError: If boundary marker not found in template
    """
    content = template_path.read_text(encoding='utf-8')
    lines = content.splitlines(keepends=True)
    boundary_line = find_boundary_line(content)

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


def extract_project_section(target_path: Path, content: str | None = None) -> tuple[list[str], int]:
    """
    Extract project-specific section from target CLAUDE.md.

    Args:
        target_path: Path to target repository's CLAUDE.md
        content: Pre-loaded file content (optional). If provided, avoids
                 re-reading the file. Use this when caller already has the
                 content (e.g. propagate_to_repo loads original_content first).

    Returns:
        Tuple of (project section lines with newlines, boundary line number)

    Raises:
        ValueError: If boundary marker not found in target file
    """
    if content is None:
        content = target_path.read_text(encoding='utf-8')
    lines = content.splitlines(keepends=True)
    boundary_line = find_boundary_line(content)

    if boundary_line == -1:
        raise ValueError(f"Boundary marker not found in target: {target_path}")

    # Extract everything after the boundary block
    # The project section starts after the 7-line boundary block
    project_start_line = boundary_line + 5  # After boundary block
    project_section = lines[project_start_line + 1:]  # +1 to skip the boundary end

    return project_section, boundary_line


def merge_sections(sst3_section: list[str], project_section: list[str]) -> str:
    """
    Merge SST3 and project sections into complete CLAUDE.md.

    Args:
        sst3_section: Lines from template (with newlines)
        project_section: Lines from project (with newlines)

    Returns:
        Merged content as string
    """
    # Add a blank line between sections if not present
    merged = sst3_section.copy()
    if not merged[-1].endswith('\n\n'):
        merged.append('\n')
    merged.extend(project_section)

    return ''.join(merged)


def verify_project_section(project_section: list[str], target_path: Path) -> bool:
    """
    Verify project section is not empty and has reasonable content.

    Args:
        project_section: Project-specific lines
        target_path: Path to target file (for error messages)

    Returns:
        True if valid, False otherwise
    """
    project_content = ''.join(project_section).strip()

    if len(project_content) < 100:
        print(f"[WARN] Project section seems too small ({len(project_content)} chars)")
        print(f"   File: {target_path}")
        return False

    # Check for project-specific heading
    if "# Project-Specific Configuration" not in project_content:
        print(f"[WARN] Project section missing expected heading")
        print(f"   File: {target_path}")
        return False

    return True


def propagate_to_repo(template_path: Path, target_repo: Path, dry_run: bool = False) -> bool:
    """
    Propagate template to single repository.

    Args:
        template_path: Path to CLAUDE_TEMPLATE.md
        target_repo: Path to target repository
        dry_run: If True, only show what would change

    Returns:
        True if successful, False otherwise
    """
    target_claude = target_repo / "CLAUDE.md"

    if not target_claude.exists():
        print(f"[ERROR] {target_claude} not found")
        return False

    print(f"\n{'='*60}")
    print(f"[*] Processing: {target_repo.name}")
    print(f"{'='*60}")

    try:
        # Extract sections
        print("   Extracting SST3 section from template...")
        sst3_section, sst3_boundary = extract_sst3_section(template_path)

        print("   Extracting project section from target...")
        # Read once, pass content to extract_project_section to avoid duplicate read
        original_content = target_claude.read_text(encoding='utf-8')
        project_section, project_boundary = extract_project_section(target_claude, original_content)

        # Verify project section
        print("   Verifying project section integrity...")
        if not verify_project_section(project_section, target_claude):
            response = input("   Continue anyway? (y/N): ")
            if response.lower() != 'y':
                print("   [SKIP] Skipped due to verification failure")
                return False

        # Merge
        print("   Merging sections...")
        merged = merge_sections(sst3_section, project_section)

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

        if dry_run:
            print(f"\n   [OK] Dry run complete - no files modified")
            print(f"      Would update: {target_claude}")
            return True

        # Atomic write merged content
        print(f"\n   [WRITE] Writing merged content...")
        tmp = target_claude.with_suffix('.tmp')
        tmp.write_text(merged, encoding='utf-8')
        tmp.replace(target_claude)

        print(f"\n   [SUCCESS] Updated: {target_claude}")
        print(f"\n   [NEXT] Next steps:")
        print(f"      1. Review changes: git diff CLAUDE.md")
        print(f"      2. Test configuration: claude chat (verify no errors)")
        print(f"      3. If satisfied: git add CLAUDE.md && git commit")
        print(f"      4. If issues: git checkout CLAUDE.md")

        return True

    except Exception as e:
        print(f"   [ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point for script."""
    parser = argparse.ArgumentParser(
        description="Propagate SST3 template updates to project repositories",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Propagate to single repo
    python propagate-template.py --repo ../tradebook_GAS

    # Dry run first (recommended)
    python propagate-template.py --repo ../tradebook_GAS --dry-run

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
    args = parser.parse_args()

    # Find template (script is in dotfiles/SST3/scripts/)
    script_dir = Path(__file__).parent.resolve()
    dotfiles = script_dir.parent.parent
    template = dotfiles / "SST3" / "templates" / "CLAUDE_TEMPLATE.md"

    if not template.exists():
        print(f"[ERROR] Template not found: {template}")
        print(f"   Expected location: dotfiles/SST3/templates/CLAUDE_TEMPLATE.md")
        sys.exit(1)

    print(f"[TEMPLATE] Using: {template}")

    # Auto-discover all sibling repositories under DevProjects/ that contain a CLAUDE.md.
    # Replaces the hardcoded list so new repos are picked up automatically.
    devprojects = dotfiles.parent
    discovered = sorted([
        d for d in devprojects.iterdir()
        if d.is_dir() and (d / "CLAUDE.md").exists()
    ])
    # Ensure dotfiles is first (it owns the template + tracks its own CLAUDE.md)
    if dotfiles in discovered:
        discovered.remove(dotfiles)
    all_repos = [dotfiles] + discovered

    # Print discovered repos so the user can verify the list before propagation runs
    print(f"\n[DISCOVERED] {len(all_repos)} repos with CLAUDE.md:")
    for r in all_repos:
        print(f"  - {r.name}")

    if args.all:
        print(f"\n[START] Propagating to {len(all_repos)} repositories...")
        success_count = 0
        for repo in all_repos:
            if propagate_to_repo(template, repo, args.dry_run):
                success_count += 1

        print(f"\n{'='*60}")
        print(f"[SUMMARY] {success_count}/{len(all_repos)} repositories updated successfully")
        print(f"{'='*60}")

    elif args.repo:
        # Resolve relative path from current working directory
        target_repo = Path(args.repo).resolve()
        if not target_repo.exists():
            print(f"[ERROR] Repository not found: {target_repo}")
            sys.exit(1)

        success = propagate_to_repo(template, target_repo, args.dry_run)
        sys.exit(0 if success else 1)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
