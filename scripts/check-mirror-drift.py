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

Exit codes:
  0 — clean (or gracefully skipped)
  1 — drift detected
  2 — manifest / config error
"""

from __future__ import annotations

import argparse
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

    checked = 0
    drifted: list[str] = []
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
            drifted.append(detail)
            print(f"ERROR: {detail}", file=sys.stderr)
        elif args.verbose:
            print(f"OK: {mirror['repo']}/{mirror['path']}", file=sys.stderr)

    if drifted:
        print(
            f"\n{len(drifted)} file(s) drifted out of {checked} checked. "
            f"Run propagate-mirrors.py --apply to sync.",
            file=sys.stderr,
        )
        return smu.EXIT_DRIFT

    scope = f"repo={args.repo}" if args.repo else "all mirrors"
    if not args.quiet:
        print(f"OK: {checked} files checked ({scope}), no drift.", file=sys.stderr)
    return smu.EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
