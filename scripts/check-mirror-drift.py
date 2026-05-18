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
except ImportError as exc:  # pragma: no cover — only hits if script is run standalone
    print(
        f"ERROR: cannot import sst3_mirror_utils (must be in same dir): {exc}",
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
    return parser.parse_args(argv)


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
            print(
                f"\n{len(blocking)} mirrored file(s) drifted {why} out of "
                f"{checked} checked. Run propagate-mirrors.py --apply to sync.",
                file=sys.stderr,
            )
            return smu.EXIT_DRIFT

        print(
            f"\n{len(unstaged)} mirrored file(s) drifted but NOT staged "
            f"(out of {checked} checked) — surfaced as warnings, commit "
            f"allowed. Run propagate-mirrors.py --apply to sync; push/CI "
            f"--strict still enforces repo-wide.",
            file=sys.stderr,
        )
        return smu.EXIT_OK

    scope = f"repo={args.repo}" if args.repo else "all mirrors"
    if not args.quiet:
        print(f"OK: {checked} files checked ({scope}), no drift.", file=sys.stderr)
    return smu.EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
