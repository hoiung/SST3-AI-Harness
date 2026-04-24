#!/usr/bin/env python3
"""Shared utilities for SST3 mirror drift detection and propagation (Issue #418).

Byte-identical across:
  - dotfiles/SST3/scripts/sst3_mirror_utils.py (canonical)
  - SST3-AI-Harness/scripts/sst3_mirror_utils.py (vendored)
  - hoiboy-uk/scripts/sst3_mirror_utils.py (vendored)
  - ebay-seller-tool/scripts/sst3_mirror_utils.py (vendored)

A `cmp -s` self-drift hook in each mirror enforces byte-identity.

Consumed by:
  - SST3/scripts/check-mirror-drift.py (mirror-side pre-commit hook)
  - SST3/scripts/propagate-mirrors.py (canonical-side validator + propagator)

Design notes:
  - Two drift modes per manifest entry:
      (1) `transforms: [...]` — deterministic. apply(canonical) == mirror.
      (2) `divergent: true` + `mirror_sha256: "..."` — hash-pinned. Mirror
          content is hand-authored; drift-check verifies the mirror hash
          only. Used for structural rewrites that cannot round-trip from
          canonical (e.g. evidence scrub, voice rule rewrite).
  - Transforms are pure `(text: str, ctx: dict) -> str`, idempotent.
  - Registry is a module-level dict — no factories, no classes.
  - Python 3.10+, stdlib only. No pyyaml (mirror repos may lack it).
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable, Iterable

TransformFn = Callable[[str, dict], str]

MANIFEST_VERSION = 1
MANIFEST_FILENAME = "drift-manifest.json"
EXIT_OK = 0
EXIT_DRIFT = 1
EXIT_CONFIG = 2


# -----------------------------------------------------------------------------
# Transform implementations (pure, idempotent)
# -----------------------------------------------------------------------------

_PATH_SCRUB_RE = re.compile(r"\.\./dotfiles/SST3/([a-zA-Z0-9_\-]+)/")
_SST3_SELF_RE = re.compile(r"\bSST3/([a-zA-Z0-9_\-]+)/")
_ISSUE_URL_LINKED = re.compile(
    r"\[Issue #(\d+)\]\(https://github\.com/hoiung/dotfiles/issues/\d+\)"
)
_ISSUE_URL_PAREN = re.compile(
    r"\(\[Issue #(\d+)\]\(https://github\.com/hoiung/dotfiles/issues/\d+\)\)"
)
_ISSUE_URL_BARE = re.compile(r"https://github\.com/hoiung/dotfiles/issues/(\d+)")
_REPO_REF_RE = re.compile(r"\bhoiung/(dotfiles|hoiboy-uk|ebay-seller-tool|SST3-AI-Harness)\b")
_AUTO_PB_RE = re.compile(r"\bauto_pb_swing_trader\b")
_TRADEBOOK_RE = re.compile(r"\btradebook_GAS\b")
_USER_QUOTE_RE = re.compile(r"^User quote:\s*\*\".*?\"\*\s*$", re.MULTILINE)
_TRADING_TERM_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bpipeline\s*/\s*backtest\s*/\s*SL1\s*/\s*SL2\s*/"), "pipeline / data-processing /"),
    (re.compile(r"\bSL1\s*/\s*SL2\s*/\s*backtest\b"), "data-processing"),
    (re.compile(r"\bbacktest\s*/\s*SL1\s*/\s*SL2\b"), "data-processing"),
]
_PRIVATE_PATH_RE = re.compile(r"logs/sample_\d+_validation\.log")
# Strict start-of-line match — only lines of the form `# [identifier]` (optional trailing whitespace).
# Data lines containing `[` (e.g. `ERROR_[42]`) do NOT match and are preserved as data. (#441 Phase 2 defensive regex.)
_BLOCKLIST_SECTION_HEADER_RE = re.compile(r"^# \[([a-zA-Z0-9_-]+)\]\s*$")


def path_scrub(text: str, ctx: dict) -> str:
    """Rewrite `../dotfiles/SST3/<subdir>/` cross-repo refs for mirror context.

    In mirrors, SST3 content is at `<mirror>/<subdir>/` (no `SST3/` prefix),
    so `../dotfiles/SST3/ralph/foo.md` → `../ralph/foo.md` (the sibling's
    `ralph/foo.md`) from the perspective of a mirror script.

    `SST3/<subdir>/` (in-repo refs in dotfiles) → `<subdir>/` in mirrors.
    """
    out = _PATH_SCRUB_RE.sub(r"../\1/", text)
    out = _SST3_SELF_RE.sub(r"\1/", out)
    return out


def issue_url_scrub(text: str, ctx: dict) -> str:
    """Strip full GitHub URLs to private dotfiles issues; keep issue number."""
    out = _ISSUE_URL_PAREN.sub(r"(Issue #\1)", text)
    out = _ISSUE_URL_LINKED.sub(r"Issue #\1", out)
    out = _ISSUE_URL_BARE.sub(r"Issue #\1", out)
    return out


def repo_ref_scrub(text: str, ctx: dict) -> str:
    """Strip `hoiung/` org prefix from repo refs (e.g. `hoiung/dotfiles` → `dotfiles`)."""
    return _REPO_REF_RE.sub(r"\1", text)


def project_name_scrub(text: str, ctx: dict) -> str:
    """Replace private project names with generic placeholders."""
    out = _AUTO_PB_RE.sub("project-a", text)
    out = _TRADEBOOK_RE.sub("project-b", out)
    return out


def trading_term_scrub(text: str, ctx: dict) -> str:
    """Genericize trading-pipeline terminology."""
    out = text
    for pat, repl in _TRADING_TERM_PATTERNS:
        out = pat.sub(repl, out)
    return out


def private_path_scrub(text: str, ctx: dict) -> str:
    """Genericize log paths and private filesystem refs.

    Conservative: only scrubs obviously-private log path patterns observed in
    canonical content. Not a general sanitizer.
    """
    return _PRIVATE_PATH_RE.sub("log file path", text)


def user_quote_scrub(text: str, ctx: dict) -> str:
    """Remove `User quote: *"..."*` inline attribution blocks."""
    return _USER_QUOTE_RE.sub("", text)


def blocklist_subset(text: str, ctx: dict) -> str:
    """Filter canonical blocklist to repo-specific subset via ctx['repo'].

    Canonical file uses section headers `# [<tag>]` on their own line to mark
    per-repo sections. Two relevant tags:
      - `[shared]` — emitted to every mirror
      - `[<ctx['repo']>]` — emitted to that repo only

    Lines BEFORE any section header (preamble: GENERATED header, comments) are
    passed through to every mirror. Lines inside a non-matching section are
    dropped.

    Section-header detection uses strict regex `^# \\[([a-zA-Z0-9_-]+)\\]\\s*$`.
    Data lines that happen to contain `[` (e.g. `ERROR_[42]`) do NOT match and
    are preserved as data.

    ctx['repo'] is guaranteed non-empty by _validate_mirror (see the non-empty-string
    check for the 'repo' key in that function).

    Pure filter. Idempotent: applying twice yields the same result.
    """
    target = ctx.get("repo", "")
    out_lines: list[str] = []
    current_section: str | None = None  # None = preamble

    for line in text.splitlines(keepends=False):
        m = _BLOCKLIST_SECTION_HEADER_RE.match(line)
        if m:
            current_section = m.group(1)
            if current_section in ("shared", target):
                out_lines.append(line)
            continue
        if current_section is None or current_section in ("shared", target):
            out_lines.append(line)

    result = "\n".join(out_lines)
    if text.endswith("\n") and not result.endswith("\n"):
        result += "\n"
    return result


TRANSFORMS: dict[str, TransformFn] = {
    "blocklist_subset": blocklist_subset,
    "issue_url_scrub": issue_url_scrub,
    "path_scrub": path_scrub,
    "private_path_scrub": private_path_scrub,
    "project_name_scrub": project_name_scrub,
    "repo_ref_scrub": repo_ref_scrub,
    "trading_term_scrub": trading_term_scrub,
    "user_quote_scrub": user_quote_scrub,
}


def apply_transforms(text: str, transform_names: list[str], ctx: dict) -> str:
    """Apply named transforms to `text` left-to-right.

    Raises ManifestError on unknown transform name.
    """
    out = text
    for name in transform_names:
        fn = TRANSFORMS.get(name)
        if fn is None:
            raise ManifestError(
                f"unknown transform '{name}'. Registry: {sorted(TRANSFORMS.keys())}"
            )
        out = fn(out, ctx)
    return out


# -----------------------------------------------------------------------------
# Manifest schema + loader
# -----------------------------------------------------------------------------


class ManifestError(RuntimeError):
    """Raised on manifest schema / loader failures. Caller exits with EXIT_CONFIG."""


def find_manifest(start: Path | None = None) -> Path:
    """Locate `drift-manifest.json` from an invocation site.

    Search order:
      1. `<start>/../drift-manifest.json` — canonical (script in dotfiles/SST3/scripts/,
         manifest at dotfiles/SST3/drift-manifest.json)
      2. `<start>/../../dotfiles/SST3/drift-manifest.json` — mirror (script in
         <mirror>/scripts/, canonical at sibling ../dotfiles/ under DevProjects/)

    Raises ManifestError if not found in either location.
    """
    start = (start or Path(__file__).resolve().parent)
    candidates = [
        start.parent / MANIFEST_FILENAME,  # canonical: dotfiles/SST3/drift-manifest.json
        start.parent.parent / "dotfiles" / "SST3" / MANIFEST_FILENAME,  # mirror -> sibling
    ]
    for p in candidates:
        if p.is_file():
            return p
    raise ManifestError(
        f"{MANIFEST_FILENAME} not found near {start}. Searched: {[str(c) for c in candidates]}"
    )


def load_manifest(path: Path) -> dict[str, Any]:
    """Read + validate manifest JSON. Returns parsed dict.

    Raises ManifestError on JSON parse failure or schema violation.
    """
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ManifestError(f"cannot read manifest {path}: {exc}") from exc
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ManifestError(f"manifest JSON parse failed ({path}): {exc}") from exc
    validate_manifest(data)
    return data


def validate_manifest(data: Any) -> None:
    """Validate manifest schema. Raises ManifestError with field-level detail on failure."""
    if not isinstance(data, dict):
        raise ManifestError(f"manifest root must be object, got {type(data).__name__}")
    version = data.get("version")
    if version != MANIFEST_VERSION:
        raise ManifestError(
            f"unsupported manifest version {version!r} (expected {MANIFEST_VERSION})"
        )
    for key in ("canonical_root", "vendored_files"):
        if key not in data:
            raise ManifestError(f"manifest missing required field '{key}'")
    if not isinstance(data["canonical_root"], str):
        raise ManifestError("canonical_root must be string")
    if not isinstance(data["vendored_files"], list):
        raise ManifestError("vendored_files must be list")
    seen_canonicals: set[str] = set()
    for i, entry in enumerate(data["vendored_files"]):
        _validate_entry(entry, i, seen_canonicals)


def _validate_entry(entry: Any, index: int, seen: set[str]) -> None:
    prefix = f"vendored_files[{index}]"
    if not isinstance(entry, dict):
        raise ManifestError(f"{prefix} must be object")
    canonical = entry.get("canonical")
    if not isinstance(canonical, str) or not canonical:
        raise ManifestError(f"{prefix}.canonical must be non-empty string")
    if canonical in seen:
        raise ManifestError(f"{prefix}.canonical duplicate: {canonical}")
    seen.add(canonical)
    mirrors = entry.get("mirrors")
    if not isinstance(mirrors, list) or not mirrors:
        raise ManifestError(f"{prefix}.mirrors must be non-empty list")
    for j, mirror in enumerate(mirrors):
        _validate_mirror(mirror, f"{prefix}.mirrors[{j}]")


def _validate_mirror(mirror: Any, prefix: str) -> None:
    if not isinstance(mirror, dict):
        raise ManifestError(f"{prefix} must be object")
    for key in ("repo", "path"):
        val = mirror.get(key)
        if not isinstance(val, str) or not val:
            raise ManifestError(f"{prefix}.{key} must be non-empty string")
    divergent = mirror.get("divergent", False)
    if divergent:
        sha = mirror.get("mirror_sha256")
        if (
            not isinstance(sha, str)
            or len(sha) != 64
            or not all(c in "0123456789abcdef" for c in sha)
        ):
            raise ManifestError(
                f"{prefix} has divergent=true but mirror_sha256 missing or malformed "
                f"(expected 64-char lowercase hex sha256)"
            )
    else:
        transforms = mirror.get("transforms")
        if not isinstance(transforms, list):
            raise ManifestError(f"{prefix}.transforms must be list (use [] for byte-identical)")
        for name in transforms:
            if name not in TRANSFORMS:
                raise ManifestError(
                    f"{prefix}.transforms references unknown transform '{name}'. "
                    f"Registry: {sorted(TRANSFORMS.keys())}"
                )


# -----------------------------------------------------------------------------
# Path resolution
# -----------------------------------------------------------------------------


def resolve_dotfiles_root(manifest_path: Path) -> Path:
    """Return the dotfiles repo root, given the manifest path."""
    # manifest lives at <dotfiles>/SST3/drift-manifest.json
    return manifest_path.parent.parent


def resolve_canonical(manifest_path: Path, canonical_rel: str) -> Path:
    """Resolve a manifest `canonical` field to an absolute path."""
    return resolve_dotfiles_root(manifest_path) / canonical_rel


def resolve_mirror(manifest_path: Path, mirror_repo: str, mirror_rel: str) -> Path:
    """Resolve a manifest mirror entry to an absolute path.

    Mirror repos live as siblings of `dotfiles/` under `DevProjects/`.
    """
    devprojects = resolve_dotfiles_root(manifest_path).parent
    return devprojects / mirror_repo / mirror_rel


# -----------------------------------------------------------------------------
# Iteration helpers
# -----------------------------------------------------------------------------


def iter_mirror_entries(
    manifest: dict[str, Any],
    *,
    repo_filter: str | None = None,
    file_filter: str | None = None,
) -> Iterable[tuple[dict[str, Any], dict[str, Any]]]:
    """Yield (entry, mirror) pairs matching filters."""
    for entry in manifest["vendored_files"]:
        if file_filter and entry["canonical"] != file_filter:
            continue
        for mirror in entry["mirrors"]:
            if repo_filter and mirror["repo"] != repo_filter:
                continue
            yield entry, mirror


def sha256_of(path: Path) -> str:
    """Return hex sha256 of file contents. Raises OSError on read failure."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# -----------------------------------------------------------------------------
# Drift comparison
# -----------------------------------------------------------------------------


def check_mirror_drift(
    manifest_path: Path,
    entry: dict[str, Any],
    mirror: dict[str, Any],
    *,
    canonical_text: str | None = None,
) -> tuple[bool, str]:
    """Return (has_drift, detail). detail is an actionable error string if drift else ''.

    Raises ManifestError if canonical file missing.

    `canonical_text` lets callers pre-read the canonical file once and share it
    across multiple mirror entries for the same canonical. Omit to read on
    demand (safe default).
    """
    canonical_path = resolve_canonical(manifest_path, entry["canonical"])
    mirror_path = resolve_mirror(manifest_path, mirror["repo"], mirror["path"])

    if not canonical_path.is_file():
        raise ManifestError(
            f"manifest references missing canonical file '{entry['canonical']}' "
            f"(resolved to {canonical_path}). Check manifest or restore file."
        )
    if not mirror_path.is_file():
        return True, (
            f"mirror file missing: {mirror_path} "
            f"(manifest expects {mirror['repo']}/{mirror['path']})"
        )

    if mirror.get("divergent"):
        expected_sha = mirror["mirror_sha256"]
        actual_sha = sha256_of(mirror_path)
        if actual_sha != expected_sha:
            return True, (
                f"{mirror['repo']}/{mirror['path']} sha256 {actual_sha[:12]}… "
                f"(expected {expected_sha[:12]}…) — divergent mirror drifted. "
                f"If intentional, run: python SST3/scripts/propagate-mirrors.py "
                f"--apply --repo {mirror['repo']} --file {entry['canonical']}"
            )
        return False, ""

    # deterministic transform mode
    if canonical_text is None:
        canonical_text = canonical_path.read_text(encoding="utf-8")
    transforms = mirror.get("transforms", [])
    ctx = {"repo": mirror["repo"], "canonical": entry["canonical"], "path": mirror["path"]}
    expected = apply_transforms(canonical_text, transforms, ctx)
    actual = mirror_path.read_text(encoding="utf-8")
    if actual != expected:
        return True, (
            f"{mirror['repo']}/{mirror['path']} has drifted from canonical "
            f"{entry['canonical']} after transforms {transforms}. "
            f"Run: python ../dotfiles/SST3/scripts/propagate-mirrors.py "
            f"--apply --repo {mirror['repo']} --file {entry['canonical']}"
        )
    return False, ""


# -----------------------------------------------------------------------------
# Self-test of transform idempotency (used by tests + smoke checks)
# -----------------------------------------------------------------------------


def assert_idempotent() -> None:
    """Smoke-check: each transform is idempotent on a sample text.

    Intended to run at test time. Raises AssertionError on failure. Cheap
    enough to call from scripts at startup if paranoid, but not required.
    """
    sample = (
        "See ../dotfiles/SST3/ralph/foo.md and SST3/scripts/bar.py. "
        "[Issue #141](https://github.com/hoiung/dotfiles/issues/141) applies. "  # secret-allow
        "hoiung/dotfiles#404 relates. "
        "auto_pb_swing_trader and tradebook_GAS. "
        "pipeline / backtest / SL1 / SL2 / orchestration. "
        'User quote: *"example"*\n'
        "logs/sample_1234_validation.log for reference.\n"
        "# [shared]\n"
        "shared-entry-1\n"
        "# [other-repo]\n"
        "should-not-appear-in-test-subset\n"
        "# [test]\n"
        "test-specific-entry\n"
    )
    ctx = {"repo": "test", "canonical": "test", "path": "test"}
    for name, fn in TRANSFORMS.items():
        once = fn(sample, ctx)
        twice = fn(once, ctx)
        assert once == twice, f"transform {name} not idempotent"


if __name__ == "__main__":  # pragma: no cover
    # CLI self-test
    try:
        assert_idempotent()
        print("OK: transform idempotency check passed", file=sys.stderr)
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
