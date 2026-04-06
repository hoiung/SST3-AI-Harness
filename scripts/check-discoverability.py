#!/usr/bin/env python3
"""
Multi-Repo Discoverability Validator for SST3 (Issue #119)

CRITICAL USER REQUIREMENT:
"All discoverability starts at the beginning of the process, which is CLAUDE.md in each repo!"

Purpose:
- Validate EVERY SST3 feature is discoverable from CLAUDE.md in EVERY repo
- Trace complete discovery chain: CLAUDE.md → WORKFLOW.md → stages → feature
- Block PR if ANY feature is not discoverable from ANY repo
- Make SST3 truly self-sustaining across all repositories

Discovery Chain (MANDATORY for every feature):
  Step 0: CLAUDE.md in repo (ENTRY POINT - MANDATORY)
     ↓ (must reference SST3)
  Step 1: ../dotfiles/SST3/workflow/WORKFLOW.md
     ↓ (must reference stages)
  Step 2: stage-X-*.md
     ↓ (must reference feature)
  Step 3: Feature file (scripts/*.py, reference/*.md, templates/*)

  Result: ✅ DISCOVERABLE (3-4 steps from CLAUDE.md)

Usage:
  python SST3/scripts/check-discoverability.py [--verbose] [--repo REPO_NAME]

Exit codes:
  0: All features discoverable from all repos (100% × 3 repos)
  1: Some features not discoverable (BLOCKS PR)
"""

import argparse
import functools
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


@functools.lru_cache(maxsize=128)
def _read_file_cached(path_str: str) -> str:
    """Read file once per process. Bounded cache to prevent memory leak.

    AP #12 fail-loud: any read error is logged to stderr unconditionally
    (not via verbose-gated self.log) before returning empty string. Caller
    distinguishes missing-file from read-error by checking stat() separately.
    """
    try:
        return Path(path_str).read_text(encoding='utf-8')
    except Exception as exc:
        print(
            f"[WARN] _read_file_cached failed for {path_str}: "
            f"{type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return ""


class DiscoverabilityChecker:
    """Validates multi-repo discoverability starting from CLAUDE.md entry points."""

    def __init__(self, verbose: bool = False):
        """
        Initialize multi-repo checker.

        Args:
            verbose: Enable verbose output
        """
        self.verbose = verbose
        self.devprojects_root = Path(__file__).resolve().parents[3]  # Go up to DevProjects
        self.dotfiles_root = self.devprojects_root / "dotfiles"
        self.sst3_root = self.dotfiles_root / "SST3"

        # Track results
        self.repos: List[Dict[str, Path]] = []
        self.features: List[Path] = []
        self.results: Dict[str, Dict[str, Optional[List[str]]]] = {}
        self.errors: List[str] = []
        self.warnings: List[str] = []

        # Exclusions (intentionally invisible)
        self.exclusions = {
            "CLAUDE_TEMPLATE.md",  # Template for other repos
            ".sst3-local",         # Project-specific
            "archive",             # Archived files
            "temp",                # Temporary files
            "__pycache__",         # Python cache
            ".git",                # Git files
            "test.txt",            # Test files
        }

    def log(self, message: str):
        """Log verbose output."""
        if self.verbose:
            print(f"  [DEBUG] {message}")

    def _is_excluded(self, file_path: Path) -> bool:
        """Check if file should be excluded from validation"""
        parts = file_path.parts
        return any(excl in parts for excl in self.exclusions)

    def discover_repos(self) -> List[Dict[str, Path]]:
        """
        Discover all repos with CLAUDE.md in DevProjects.

        Returns:
            List of dicts with 'name' and 'claude_md' path
        """
        self.log("Scanning for repositories with CLAUDE.md...")
        repos = []

        # Search for all CLAUDE.md files in DevProjects
        for claude_md in self.devprojects_root.glob("*/CLAUDE.md"):
            repo_name = claude_md.parent.name
            repos.append({
                'name': repo_name,
                'claude_md': claude_md,
                'root': claude_md.parent
            })
            self.log(f"Found repo: {repo_name} at {claude_md.parent}")

        # Sort by name for consistent output
        repos.sort(key=lambda x: x['name'])
        return repos

    def validate_entry_point(self, repo: Dict[str, Path]) -> Tuple[bool, Optional[int]]:
        """
        Validate CLAUDE.md → SST3 reference chain.

        Returns:
            (success, line_number or None)
        """
        claude_md = repo['claude_md']

        if not claude_md.exists():
            self.errors.append(f"{repo['name']}: CLAUDE.md not found!")
            return False, None

        # Check if CLAUDE.md references SST3
        content = claude_md.read_text(encoding='utf-8')

        # Look for SST3 references (multiple patterns)
        patterns = [
            r'SST3/workflow/WORKFLOW\.md',
            r'\.\./dotfiles/SST3/workflow/WORKFLOW\.md',
            r'SST3/standards/STANDARDS\.md',
            r'\.\./dotfiles/SST3/standards/STANDARDS\.md',
        ]

        for i, line in enumerate(content.split('\n'), 1):
            for pattern in patterns:
                if re.search(pattern, line):
                    self.log(f"{repo['name']}: Found SST3 reference at line {i}")
                    return True, i

        self.errors.append(f"{repo['name']}: CLAUDE.md doesn't reference SST3!")
        return False, None

    def discover_sst3_features(self) -> List[Path]:
        """
        Discover all SST3 features (scripts, reference docs, templates, workflow).

        Returns:
            List of feature file paths
        """
        self.log("Discovering SST3 features...")
        features = []

        # Collect features from different SST3 categories
        categories = {
            'scripts': self.sst3_root / 'scripts',
            'reference': self.sst3_root / 'reference',
            'templates': self.sst3_root / 'templates',
            'workflow': self.sst3_root / 'workflow',
            'standards': self.sst3_root / 'standards',
        }

        for category, path in categories.items():
            if not path.exists():
                continue

            # Get all files in category
            for file in path.iterdir():
                # Skip directories, __pycache__, and temp files
                if file.is_dir() or file.name.startswith('__') or file.suffix in ['.pyc', '.swp']:
                    continue

                # Skip CLAUDE_TEMPLATE.md (it's a template, not a feature)
                if file.name == 'CLAUDE_TEMPLATE.md':
                    continue

                # Skip temp/test files
                if file.name.startswith('temp-') or file.name == 'temp.md' or file.name == 'test.txt':
                    continue

                features.append(file)
                self.log(f"Found feature: {file.relative_to(self.dotfiles_root)}")

        # Sort by relative path for consistent output
        features.sort(key=lambda x: str(x.relative_to(self.dotfiles_root)))
        return features

    def trace_discovery_path(self, repo: Dict[str, Path], feature: Path) -> Optional[List[str]]:
        """
        Trace discovery path from CLAUDE.md to feature.

        Returns:
            List of steps in discovery chain, or None if not discoverable
        """
        # Calculate relative path for feature
        feature_rel = feature.relative_to(self.dotfiles_root)
        feature_str = str(feature_rel).replace('\\', '/')

        # For dotfiles repo, use direct paths
        # For other repos, use ../dotfiles/ prefix
        if repo['name'] == 'dotfiles':
            sst3_prefix = 'SST3/'
            workflow_path = 'SST3/workflow/WORKFLOW.md'
        else:
            sst3_prefix = '../dotfiles/SST3/'
            workflow_path = '../dotfiles/SST3/workflow/WORKFLOW.md'

        # Step 0: CLAUDE.md exists (already validated)
        path = [f"{repo['name']}/CLAUDE.md"]

        # Step 1: CLAUDE.md → WORKFLOW.md
        claude_md = repo['claude_md']
        if not self._file_references(claude_md, workflow_path):
            # Check if references any SST3 file (alternative path)
            if not self._file_references(claude_md, sst3_prefix):
                return None
        path.append("WORKFLOW.md")

        # Step 2: WORKFLOW.md → stage-X → feature
        workflow_md = self.sst3_root / 'workflow' / 'WORKFLOW.md'

        # Check if feature is directly referenced in WORKFLOW.md
        if self._file_references(workflow_md, feature_str):
            path.append(feature_str)
            return path

        # Step 3: Find stage file that references this feature
        stage_files = list((self.sst3_root / 'workflow').glob('stage-*.md'))
        stage_files.append(self.sst3_root / 'workflow' / 'WORKFLOW.md')

        for stage_file in stage_files:
            if self._file_references(stage_file, feature_str):
                path.append(stage_file.name)
                path.append(feature_str)
                return path

        # Check in STANDARDS.md
        standards_md = self.sst3_root / 'standards' / 'STANDARDS.md'
        if self._file_references(standards_md, feature_str):
            path.append('STANDARDS.md')
            path.append(feature_str)
            return path

        # Check in ANTI-PATTERNS.md
        antipatterns_md = self.sst3_root / 'standards' / 'ANTI-PATTERNS.md'
        if antipatterns_md.exists() and self._file_references(antipatterns_md, feature_str):
            path.append('ANTI-PATTERNS.md')
            path.append(feature_str)
            return path

        # Not discoverable
        return None

    def _file_references(self, file: Path, target: str) -> bool:
        """
        Check if file references target path. Uses bounded lru_cache so each
        file is only read once per process invocation (was being read N times
        per feature × repos before, causing redundant IO).

        AP #12 fail-loud: distinguishes read failure from empty file by checking
        file size before treating empty content as benign.
        """
        if not file.exists():
            return False
        content = _read_file_cached(str(file))
        if not content:
            # AP #12 fail-loud — unconditional stderr (not verbose-gated)
            try:
                if file.stat().st_size > 0:
                    print(
                        f"[WARN] check-discoverability: {file} is non-empty "
                        f"but cached read returned empty (see prior _read_file_cached error)",
                        file=sys.stderr,
                    )
            except OSError as exc:
                print(
                    f"[WARN] check-discoverability: stat() failed on {file}: {exc}",
                    file=sys.stderr,
                )
            return False
        target_normalized = target.replace('\\', '/')
        content_normalized = content.replace('\\', '/')
        return target_normalized in content_normalized

    def validate_all(self) -> bool:
        """
        Run complete multi-repo discoverability validation.

        Returns:
            True if all features discoverable from all repos, False otherwise
        """
        print("Multi-Repo Discoverability Check")
        print("=" * 50)
        print()

        # Step 1: Discover repos
        self.repos = self.discover_repos()
        print(f"Repositories Found: {len(self.repos)}")
        for repo in self.repos:
            print(f"  - {repo['name']}/CLAUDE.md [OK]")
        print()

        # Step 2: Validate entry points
        print("Validating Entry Points:")
        print("-" * 50)
        entry_point_valid = True
        for repo in self.repos:
            valid, line_num = self.validate_entry_point(repo)
            if valid and line_num:
                # Determine path based on repo
                if repo['name'] == 'dotfiles':
                    ref_path = "SST3/workflow/WORKFLOW.md"
                else:
                    ref_path = "../dotfiles/SST3/workflow/WORKFLOW.md"
                print(f"[OK] {repo['name']}/CLAUDE.md -> {ref_path} (line {line_num})")
            else:
                print(f"[FAIL] {repo['name']}/CLAUDE.md -> SST3 (NOT FOUND)")
                entry_point_valid = False
        print()

        # Step 3: Discover features
        self.features = self.discover_sst3_features()
        total_paths = len(self.features) * len(self.repos)
        print(f"Validating Features ({len(self.features)} items × {len(self.repos)} repos = {total_paths} paths):")
        print("-" * 50)
        print()

        # Step 4: Validate each feature from each repo
        valid_paths = 0
        invalid_features = []

        for feature in self.features:
            feature_rel = feature.relative_to(self.dotfiles_root)
            feature_str = str(feature_rel).replace('\\', '/')
            print(f"Feature: {feature_str}")

            # Track if feature discoverable from ANY repo
            discoverable_from_any = False

            for repo in self.repos:
                path = self.trace_discovery_path(repo, feature)

                if path:
                    steps = len(path) - 1  # Don't count starting point
                    path_str = " -> ".join(path)
                    print(f"  [OK] {repo['name']}: {path_str} ({steps} steps)")
                    valid_paths += 1
                    discoverable_from_any = True

                    # Store result
                    if feature_str not in self.results:
                        self.results[feature_str] = {}
                    self.results[feature_str][repo['name']] = path
                else:
                    print(f"  [FAIL] {repo['name']}: NOT FOUND in any markdown files")

                    # Store result
                    if feature_str not in self.results:
                        self.results[feature_str] = {}
                    self.results[feature_str][repo['name']] = None

            # If not discoverable from any repo, add to invalid list
            if not discoverable_from_any:
                invalid_features.append(feature_str)
                print(f"  -> ACTION: Add reference at decision point in workflow")

            print()

        # Step 5: Generate summary
        print("Summary by Repo:")
        print("-" * 50)
        all_repos_pass = True
        for repo in self.repos:
            repo_valid = sum(1 for f in self.results.values() if f.get(repo['name']))
            repo_total = len(self.features)
            percentage = (repo_valid / repo_total * 100) if repo_total > 0 else 0

            if repo_valid == repo_total:
                print(f"[OK] {repo['name']}: {repo_valid}/{repo_total} features discoverable ({percentage:.0f}%)")
            else:
                print(f"[FAIL] {repo['name']}: {repo_valid}/{repo_total} features discoverable ({percentage:.0f}%)")
                all_repos_pass = False
        print()

        # Overall summary
        percentage = (valid_paths / total_paths * 100) if total_paths > 0 else 0
        print(f"Overall: {valid_paths}/{total_paths} paths valid ({percentage:.0f}%)")

        # Final result
        if valid_paths == total_paths and entry_point_valid:
            print("Result: PASS (all features discoverable from all repos)")
            print()
            return True
        else:
            print(f"Result: FAIL ({len(invalid_features)} features not discoverable from any repo)")
            print()
            print("BLOCKING: Cannot merge PR until all features discoverable from all repos.")
            print()

            if invalid_features:
                print("Features requiring references:")
                for feat in invalid_features:
                    print(f"  - {feat}")

            return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Multi-Repo Discoverability Validator for SST3'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    parser.add_argument(
        '--repo',
        type=str,
        help='Check only specific repo (for debugging)'
    )

    args = parser.parse_args()

    checker = DiscoverabilityChecker(verbose=args.verbose)
    success = checker.validate_all()

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
