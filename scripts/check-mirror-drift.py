#!/usr/bin/env python3
"""Mirror-side drift check for vendored SST3 files (Issue #418).

Runs as a pre-commit hook in SST3-AI-Harness, hoiboy-uk, ebay-seller-tool.
For each manifest-listed file:
  - deterministic mode: verify `transform(canonical) == mirror`
  - divergent mode: verify `sha256(mirror) == recorded_hash`

Graceful skip: if `../dotfiles/` not present (mirror cloned standalone),
print SKIP to stderr and exit 0. Matches existing secret-rules-drift /
voice-rules-drift pattern.

Byte-identical across canonical (dotfiles/SST3/scripts/) and all 3 mirrors.
A `cmp -s` self-drift hook in each mirror enforces byte-identity.

Staged-aware gate (Issue #492): a drifted mirror only BLOCKS a commit when
that mirror file is actually in the staged set. Drift on a file the commit
does not touch is surfaced as a WARNING (visibility kept) and the commit
proceeds — an unrelated content commit is no longer frozen by mid-migration
plumbing. `--strict` forces the legacy block-all behaviour and is used at
push / CI time so the repo-wide invariant is still enforced where it belongs.

Exit codes:
  0 — clean, gracefully skipped, or only non-staged drift (warned)
  1 — drift detected in a STAGED mirror file (or any drift under --strict)
  2 — manifest / config error
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

try:
    import sst3_mirror_utils as smu
    from sst3_block_utils import find_boundary_lines, extract_managed_block, strip_marker_lines
except ImportError as exc:  # pragma: no cover — only hits if script is run standalone
    print(
        f"ERROR: cannot import sst3_mirror_utils / sst3_block_utils "
        f"(must be in same dir): {exc}",
        file=sys.stderr,
    )
    sys.exit(2)


def _staged_paths() -> set[str] | None:
    """Return repo-root-relative paths staged in the index.

    Scopes the drift gate (#492): a drifted mirror only blocks the commit
    when it is itself staged. Returns None if the staged set cannot be
    determined (no git / not a work tree) — the caller then fails safe to
    the strict block-all behaviour rather than silently weakening the gate.
    """
    try:
        out = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return {line.strip() for line in out.stdout.splitlines() if line.strip()}


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check vendored SST3 files for drift vs canonical dotfiles.",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="Override manifest path (default: auto-discover).",
    )
    parser.add_argument(
        "--repo",
        type=str,
        default=None,
        help="Scope check to one mirror repo (e.g. SST3-AI-Harness).",
    )
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="Scope check to one canonical file path.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print per-file status to stderr.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress success output (errors still printed).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help=(
            "Block on ANY drift regardless of staged set (legacy behaviour). "
            "Use at push / CI time for repo-wide enforcement."
        ),
    )
    parser.add_argument(
        "--managed-blocks",
        action="store_true",
        help=(
            "Check `managed_blocks[]` (paired-marker pre-commit blocks) "
            "instead of `vendored_files[]`. Issue #493 AC 1.7. Same "
            "staged-aware gate (#492) — drift on a non-staged target is a "
            "warning, drift on a staged target blocks (unless --strict)."
        ),
    )
    return parser.parse_args(argv)


def _check_managed_block_drift(
    manifest_path: Path,
    entry: dict,
    mirror: dict,
    canonical_text: str,
) -> tuple[bool, str]:
    """Return (has_drift, detail) for one managed_blocks entry × mirror.

    Drift = the bytes BETWEEN the marker lines in the target file do not
    match the transformed canonical (after substitute_repo_slug etc.) with
    the canonical's own marker lines stripped. Missing markers = drift
    (first-apply needed). Exactly-one-marker = drift (corruption signal).
    Issue #493 AC 1.7.
    """
    marker_start: str = entry["marker_start"]
    marker_end: str = entry["marker_end"]
    target_path = smu.resolve_mirror(manifest_path, mirror["repo"], mirror["path"])
    if not target_path.is_file():
        return True, f"{mirror['repo']}/{mirror['path']}: target file missing"

    target_text = target_path.read_text(encoding="utf-8")
    ctx = {
        "repo": mirror["repo"],
        "canonical": entry["canonical"],
        "path": mirror["path"],
    }
    transformed = smu.apply_transforms(
        canonical_text, mirror.get("transforms", []), ctx
    )
    # Strip the canonical template's own marker lines so we compare body-to-body.
    # Stage 5 DEDUP-1 (L1-F): uses public strip_marker_lines helper now (was
    # duplicated inline here + in propagate-block.py:79-92 pre-fix).
    expected_body = strip_marker_lines(transformed, marker_start, marker_end)
    expected_body_normalised = expected_body.strip("\n")

    try:
        start, end = find_boundary_lines(target_text, marker_start, marker_end)
    except ValueError as exc:
        return True, f"{mirror['repo']}/{mirror['path']}: marker error: {exc}"
    if start == -1 and end == -1:
        return True, (
            f"{mirror['repo']}/{mirror['path']}: managed-block markers absent "
            f"(first-apply needed — run propagate-block.py --apply)"
        )
    if start == -1 or end == -1:
        return True, (
            f"{mirror['repo']}/{mirror['path']}: corrupted file — found one "
            f"marker but not both (start={start} end={end})"
        )

    actual_body = extract_managed_block(target_text, marker_start, marker_end) or ""
    actual_body_normalised = actual_body.strip("\n")
    if actual_body_normalised != expected_body_normalised:
        return True, (
            f"{mirror['repo']}/{mirror['path']}: managed-block content drifts "
            f"from canonical (run propagate-block.py --apply to sync)"
        )
    return False, ""


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    # Locate manifest. Graceful skip if dotfiles not present.
    try:
        manifest_path = args.manifest if args.manifest else smu.find_manifest()
    except smu.ManifestError as exc:
        print(
            f"SKIP: dotfiles not found — drift check skipped ({exc})",
            file=sys.stderr,
        )
        return smu.EXIT_OK

    try:
        manifest = smu.load_manifest(manifest_path)
    except smu.ManifestError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return smu.EXIT_CONFIG

    # Staged-aware gate (#492). When not --strict, a drifted mirror only
    # blocks the commit if its path is in the staged set. None == cannot
    # determine staged set -> fail safe to block-all (do not weaken the gate).
    staged = None if args.strict else _staged_paths()

    checked = 0
    drifted: list[tuple[str, str]] = []  # (mirror_path, detail)
    canonical_cache: dict[str, str] = {}

    # --managed-blocks: iterate managed_blocks[] instead of vendored_files[].
    # Issue #493 AC 1.7 — same staged-aware semantics as vendored mode.
    if args.managed_blocks:
        for entry, mirror in smu.iter_managed_block_entries(
            manifest, repo_filter=args.repo, file_filter=args.file
        ):
            checked += 1
            canonical_rel = entry["canonical"]
            canonical_text = canonical_cache.get(canonical_rel)
            if canonical_text is None:
                canonical_path = smu.resolve_canonical(manifest_path, canonical_rel)
                if not canonical_path.is_file():
                    print(
                        f"ERROR: canonical block template missing: {canonical_path}",
                        file=sys.stderr,
                    )
                    return smu.EXIT_CONFIG
                canonical_text = canonical_path.read_text(encoding="utf-8")
                canonical_cache[canonical_rel] = canonical_text
            try:
                has_drift, detail = _check_managed_block_drift(
                    manifest_path, entry, mirror, canonical_text
                )
            except smu.ManifestError as exc:
                print(f"ERROR: {exc}", file=sys.stderr)
                return smu.EXIT_CONFIG
            if has_drift:
                drifted.append((mirror["path"], detail))
            elif args.verbose:
                print(f"OK: {mirror['repo']}/{mirror['path']}", file=sys.stderr)

        # Reuse the existing emit-and-exit block below.
        return _emit_and_exit(drifted, checked, staged, args)

    for entry, mirror in smu.iter_mirror_entries(
        manifest, repo_filter=args.repo, file_filter=args.file
    ):
        try:
            text = canonical_cache.get(entry["canonical"])
            if text is None and not mirror.get("divergent"):
                canonical_path = smu.resolve_canonical(manifest_path, entry["canonical"])
                if canonical_path.is_file():
                    text = canonical_path.read_text(encoding="utf-8")
                    canonical_cache[entry["canonical"]] = text
            has_drift, detail = smu.check_mirror_drift(
                manifest_path, entry, mirror, canonical_text=text
            )
        except smu.ManifestError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return smu.EXIT_CONFIG
        checked += 1
        if has_drift:
            drifted.append((mirror["path"], detail))
        elif args.verbose:
            print(f"OK: {mirror['repo']}/{mirror['path']}", file=sys.stderr)

    return _emit_and_exit(drifted, checked, staged, args)


def _emit_and_exit(
    drifted: list[tuple[str, str]],
    checked: int,
    staged: set[str] | None,
    args,
) -> int:
    """Shared staged-aware emit-and-exit logic for both vendored_files
    and managed_blocks modes (AC 1.7 — preserves #492 staged gate)."""
    if drifted:
        if args.strict or staged is None:
            blocking = drifted
            unstaged: list[tuple[str, str]] = []
        else:
            blocking = [(p, d) for (p, d) in drifted if p in staged]
            unstaged = [(p, d) for (p, d) in drifted if p not in staged]

        for _, detail in unstaged:
            print(f"WARNING: {detail}", file=sys.stderr)
        for _, detail in blocking:
            print(f"ERROR: {detail}", file=sys.stderr)

        if blocking:
            why = "(--strict block-all)" if args.strict else "and STAGED"
            sync_hint = (
                "Run propagate-block.py --apply to sync."
                if args.managed_blocks
                else "Run propagate-mirrors.py --apply to sync."
            )
            print(
                f"\n{len(blocking)} mirrored file(s) drifted {why} out of "
                f"{checked} checked. {sync_hint}",
                file=sys.stderr,
            )
            return smu.EXIT_DRIFT

        print(
            f"\n{len(unstaged)} mirrored file(s) drifted but NOT staged "
            f"(out of {checked} checked) — surfaced as warnings, commit "
            f"allowed. Run propagate-{'block' if args.managed_blocks else 'mirrors'}.py --apply to sync; push/CI "
            f"--strict still enforces repo-wide.",
            file=sys.stderr,
        )
        return smu.EXIT_OK

    scope = f"repo={args.repo}" if args.repo else "all mirrors"
    mode = "managed-blocks" if args.managed_blocks else "vendored"
    if not args.quiet:
        print(
            f"OK: {checked} {mode} file(s) checked ({scope}), no drift.",
            file=sys.stderr,
        )
    return smu.EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
