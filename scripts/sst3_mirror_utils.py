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
# #497 A.5: replace cross-repo `<private-repo>#<num>` references with `Issue #<num>`
# so the mirror does not enumerate private consumer repos via issue-shorthand.
# `auto_pb_swing_trader` + `tradebook_GAS` are operator-acknowledged-public
# project names per Stage 1 §3.10 — kept out of this transform (project_name_scrub
# handles the bare name elsewhere; URL forms still block via .secret-blocklist).
# Includes `apbst` (legacy private slug for auto_pb_swing_trader internal Issues).
_PRIVATE_REPO_ISSUE_RE = re.compile(
    r"\b(ebay-ops|job-hunter|brainstorm|blog-priv|lab-ops|consulting-ops|apbst)#(\d+)\b"
)
# Strict start-of-line match — only lines of the form `# [identifier]` (optional trailing whitespace).
# Data lines containing `[` (e.g. `ERROR_[42]`) do NOT match and are preserved as data. (#441 Phase 2 defensive regex.)
_BLOCKLIST_SECTION_HEADER_RE = re.compile(r"^# \[([a-zA-Z0-9_-]+)\]\s*$")


def path_scrub(text: str, ctx: dict) -> str:
    """Rewrite `../dotfiles/SST3/<subdir>/` cross-repo refs for mirror context.

    For depth-1 mirror sources (e.g. `standards/STANDARDS.md`):
    `../dotfiles/SST3/ralph/foo.md` → `../ralph/foo.md` (resolves to mirror `ralph/foo.md`).
    `SST3/<subdir>/` (in-repo refs in dotfiles) → `<subdir>/` in mirrors.
    """
    out = _PATH_SCRUB_RE.sub(r"../\1/", text)
    out = _SST3_SELF_RE.sub(r"\1/", out)
    return out


def path_scrub_depth2(text: str, ctx: dict) -> str:
    """Variant of path_scrub for depth-2 mirror sources (#498 Ralph T3).

    For depth-2 mirror sources (e.g. `standards/stage-4/foo.md`):
    `../dotfiles/SST3/ralph/x.md` → `../../ralph/x.md` (resolves to mirror `ralph/x.md`).

    `path_scrub` would emit `../ralph/x.md` which resolves to mirror
    `standards/ralph/x.md` (broken — `ralph/` is at mirror root, not nested under
    `standards/`). One extra `../` segment is required for depth-2 sources.
    """
    out = _PATH_SCRUB_RE.sub(r"../../\1/", text)
    out = _SST3_SELF_RE.sub(r"\1/", out)
    return out


def issue_url_scrub(text: str, ctx: dict) -> str:
    """Strip full GitHub URLs to private dotfiles issues; keep issue number."""
    out = _ISSUE_URL_PAREN.sub(r"(Issue #\1)", text)
    out = _ISSUE_URL_LINKED.sub(r"Issue #\1", out)
    out = _ISSUE_URL_BARE.sub(r"Issue #\1", out)
    return out


def private_repo_issue_scrub(text: str, ctx: dict) -> str:
    """Replace `<private-repo>#<num>` shorthand with `Issue #<num>` (#497 A.5.1).

    Mirrors should not enumerate private consumer repo names via cross-repo
    issue references like `ebay-ops#12` / `lab-ops#7` / `apbst#1346`. The
    operator-acknowledged-public project names (`auto_pb_swing_trader`,
    `tradebook_GAS`) are NOT scrubbed by this transform — `project_name_scrub`
    handles bare name occurrences, and URL-form references still block via
    .secret-blocklist defence-in-depth.

    Idempotent: applying twice yields the same output (the substitution
    deletes the `<repo>#` prefix, so the second pass finds no further matches).
    """
    return _PRIVATE_REPO_ISSUE_RE.sub(r"Issue #\2", text)


def repo_ref_scrub(text: str, ctx: dict) -> str:
    """Strip `hoiung/` org prefix from repo refs (e.g. `hoiung/dotfiles` → `dotfiles`)."""
    return _REPO_REF_RE.sub(r"\1", text)


# #497 Phase E — content-level scrubs mirroring `.filter-repo-replacements.txt`
# (the canonical mapping table used by Phase D's history rewrite). Single source
# of truth for both lanes: filter-repo rewrites past history; this transform
# scrubs runtime canonical→mirror propagation, so they produce identical mirror
# state. Order matters — longer/compound patterns first so substring shadowing
# does not fire (e.g. `Hoi-supplied` must precede `Hoi's` so the latter does
# not partially-match the former's residue).
_PRIVATE_TERM_PAIRS: list[tuple[str, str]] = [
    # Operator-identity scrubs (case-sensitive; the `iamhoi`/`iamhoiend` marker
    # names are lowercase + non-overlapping and remain unchanged).
    ("Hoi-supplied", "operator-supplied"),
    ("Hoi-voice", "operator-voice"),
    ("Hoi-flagged", "operator-flagged"),
    ("Hoi's", "the operator's"),
    ("Hoi flagged", "operator flagged"),
    ("Hoi raised", "operator raised"),
    ("Hoi rule", "operator rule"),
    ("Hoi 2026", "the operator 2026"),
    ("Joel Sing", "the operator"),
    # Private consumer repo names — same substitutions as filter-repo replacements.
    # `auto_pb_swing_trader` / `tradebook_GAS` are NOT scrubbed here (operator-
    # acknowledged public per Stage 1 §3.10 — handled by project_name_scrub when
    # additional anonymisation is desired). Substring replacement is intentional:
    # filter-repo rewrote history with the same substring rule, so canonical-with-
    # transform output matches the post-filter-repo mirror tree byte-for-byte.
    ("ebay-ops", "consumer-private-A"),
    ("job-hunter", "voice-doc-repo"),
    ("brainstorm", "idea-repo"),
    ("blog-priv", "voice-staging"),
    ("lab-ops", "lab-harness"),
    ("consulting-ops", "consultancy-ops"),
    ("bakeoff-priv", "private-bake-off"),
    ("apbst", "project-x"),
    # Personal cloud-drive paths + private hostnames + leak-tracking memory
    # filenames — same substring-replacement semantics as filter-repo. Order is
    # longest-first so `HU-<MODEL>` precedes any potential `NUC` collision.
    ("HU-<MODEL>", "node-<MODEL>"),
    ("My Drive", "UserHome"),
    ("Google Drive", "UserHome"),
    ("OneDrive", "UserHome"),
    ("auto_pb_v1", "generic-pipeline-v1"),
    ("feedback_public_artefact_leaks_in_issues.md", "internal-leak-pattern-doc"),
    ("secret_scan_leak_log.md", "internal-leak-log"),
    # NOTE: `NUC` and bare `Hoi` are intentionally absent from this literal-pair
    # list — they are 3-char tokens whose substring `replace` produces collateral
    # damage (`NUClear` → `nodelear`) and the literal table cannot catch bare-Hoi
    # phrases (`the Hoi quote`). They are handled by `_WORD_BOUNDED_TERM_PAIRS`
    # below with a word-boundary regex, applied AFTER this literal sweep so any
    # longer compound (`Hoi-supplied`, `Hoi flagged`, `HU-<MODEL>`) matches the
    # literal table first and never reaches the word-bounded fall-through.
    # Stage 5 #497 fix (S6+S7 finding).
    # #497 E.4.4 — Tier 3 Opus residue sweep follow-up. Bare-word `Hoi` and
    # capital-S `Hoi-Supplied` forms surfaced in canonical ANTI-PATTERNS.md
    # AP #25 body + scripts/check-ai-writing-tells.py comment + voice_rules.py
    # comments. Each pair below was confirmed by a literal grep against the
    # actual canonical files (not hypothetical patterns). Order: capital-S form
    # FIRST (otherwise `Hoi-supplied`'s substring `Hoi` would steal the match
    # at the capital-S site via the bare-word rule below).
    ("Hoi-Supplied", "operator-supplied"),
    ("by Hoi", "by the operator"),
    ("Hoi writes", "the operator writes"),
    ("Hoi never", "the operator never"),
    ("Hoi framed", "the operator framed"),
    ("Hoi did", "the operator did"),
    ("Hoi stated", "the operator stated"),
    ("Hoi confirmed", "the operator confirmed"),
    ("Hoi: ", "Operator: "),
    ("Hoi vocabulary", "operator vocabulary"),
    ("non-Hoi", "non-operator"),
    ("Hoi 50+", "the operator 50+"),
    ("feedback_hoi_handwrites_notes_no_forget.md", "internal-handwriting-memory"),
    ("feedback_nad9_is_production_not_lab.md", "internal-production-memory"),
]


# Word-boundary-anchored pairs — applied AFTER `_PRIVATE_TERM_PAIRS` literal
# sweep. These exist for 3-character tokens whose substring `replace` would
# create collateral damage. Stage 5 #497 fix (S6+S7 finding):
#   - `NUC` literal-replace produces `NUClear → nodelear`, `NUCleus → nodeleus`.
#   - bare `Hoi` cannot live in `_PRIVATE_TERM_PAIRS` as a literal (would hit
#     `Hoist`, `Hoity-toity`), yet phrases like `the Hoi quote`, `Hoi can
#     install`, `Hoi 'eyes and ears'` MUST be scrubbed before they propagate
#     to the public mirror — load-bearing privacy constraint.
# Ordering: compound forms (`Hoi-supplied`, `Hoi flagged`, `Hoi: `,
# `HU-<MODEL>`, ...) match the literal table above FIRST; this fall-through
# only catches genuinely bare uses.
_WORD_BOUNDED_TERM_PAIRS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bNUC\b"), "node"),
    (re.compile(r"\bHoi\b"), "operator"),
)


def private_term_scrub(text: str, ctx: dict) -> str:
    """Replace operator-identity + private-repo-name literals (#497 Phase E).

    Mirrors `.filter-repo-replacements.txt` used by Phase D's history rewrite,
    so canonical→mirror runtime propagation produces the same output as the
    filter-repo history rewrite. Pure substring replacement (matches the
    filter-repo `--replace-text` semantics byte-for-byte).

    Idempotent: each replacement consumes its input substring; second pass is
    a no-op because no replacement output equals any other pair's input key.

    **Known trade-off (operator-authorised, dotfiles#497 checkpoint comment
    issuecomment-4493556489)**: the `_PRIVATE_TERM_PAIRS` mapping table itself
    is visible in the vendored mirror copy of this file (mirror's
    `scripts/sst3_mirror_utils.py` byte-identical to canonical per manifest
    `transforms: []`). The mapping reveals the OLD→NEW correspondence
    (`Hoi-supplied → operator-supplied`, `job-hunter → voice-doc-repo`, etc.) —
    a bounded deanonymization-oracle. Operator-acknowledged trade-off: this
    bounded one-file exposure is preferred over the alternative of literal
    identifiers scattered through dozens of rule documents (orders-of-magnitude
    larger surface). The scrub still strips the literals from rule docs; only
    the substitution table itself remains visible.
    """
    out = text
    for old, new in _PRIVATE_TERM_PAIRS:
        out = out.replace(old, new)
    for pat, repl in _WORD_BOUNDED_TERM_PAIRS:
        out = pat.sub(repl, out)
    return out


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


def substitute_repo_slug(text: str, ctx: dict) -> str:
    """Replace the literal `<REPO_SLUG>` token with `ctx['repo']`.

    Used by managed-block propagation (Issue #493 AC 1.5): the canonical
    pre-commit block carries `--repo <REPO_SLUG>` in its hook entries; at
    propagate-time each mirror entry substitutes its own repo slug. The
    ctx['repo'] value is the same mirror['repo'] field that `iter_mirror_entries`
    yields, so reuses the existing transform contract.

    Idempotent: applying twice yields the same result (since `<REPO_SLUG>`
    is gone after the first pass, the second pass is a no-op).
    """
    target = ctx.get("repo", "")
    if not target:
        return text
    return text.replace("<REPO_SLUG>", target)


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
    "path_scrub_depth2": path_scrub_depth2,
    "private_path_scrub": private_path_scrub,
    "private_repo_issue_scrub": private_repo_issue_scrub,
    "private_term_scrub": private_term_scrub,
    "project_name_scrub": project_name_scrub,
    "repo_ref_scrub": repo_ref_scrub,
    "substitute_repo_slug": substitute_repo_slug,
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
    unmirrored = data.get("unmirrored_canonical_files", [])
    if not isinstance(unmirrored, list):
        raise ManifestError("unmirrored_canonical_files must be list")
    for i, entry in enumerate(unmirrored):
        _validate_unmirrored_entry(entry, i)

    # Issue #493 AC 1.6 — managed_blocks: boundary-marker propagation (paired-
    # marker YAML blocks). Optional top-level array; each entry pairs one
    # canonical block template with N mirror targets that get per-repo
    # transforms applied at propagate-time. Without this validator extension,
    # the new array would be silently ignored (unknown-key tolerance).
    managed_blocks = data.get("managed_blocks", [])
    if not isinstance(managed_blocks, list):
        raise ManifestError("managed_blocks must be list")
    seen_canonical_blocks: set[str] = set()
    for i, entry in enumerate(managed_blocks):
        _validate_managed_block_entry(entry, i, seen_canonical_blocks)


def _validate_managed_block_entry(
    entry: Any, index: int, seen: set[str]
) -> None:
    """Enforce `managed_blocks[i]` entry schema (Issue #493 AC 1.6).

    Each entry maps one canonical block template (e.g. the SST3 pre-commit
    block YAML at SST3/templates/pre-commit-managed-block.yaml) onto N
    consumer mirror targets. Required fields:

    * ``canonical``     — non-empty repo-rel path to the canonical block template.
    * ``target_file``   — non-empty repo-rel filename inside each mirror
                          that carries the boundary-marked block (e.g.
                          ``.pre-commit-config.yaml``).
    * ``marker_start``  — non-empty start-marker line content (line-anchored).
    * ``marker_end``    — non-empty end-marker line content (line-anchored).
    * ``mirrors``       — non-empty list of ``{repo, path, transforms?}`` entries
                          (same shape as ``vendored_files[*].mirrors[*]``).
    """
    prefix = f"managed_blocks[{index}]"
    if not isinstance(entry, dict):
        raise ManifestError(f"{prefix} must be object")
    canonical = entry.get("canonical")
    if not isinstance(canonical, str) or not canonical:
        raise ManifestError(f"{prefix}.canonical must be non-empty string")
    if canonical in seen:
        raise ManifestError(f"{prefix}.canonical duplicate: {canonical}")
    seen.add(canonical)
    for key in ("target_file", "marker_start", "marker_end"):
        val = entry.get(key)
        if not isinstance(val, str) or not val:
            raise ManifestError(f"{prefix}.{key} must be non-empty string")
    if entry["marker_start"] == entry["marker_end"]:
        raise ManifestError(
            f"{prefix}.marker_start and marker_end must differ (paired-marker contract)"
        )
    mirrors = entry.get("mirrors")
    if not isinstance(mirrors, list) or not mirrors:
        raise ManifestError(f"{prefix}.mirrors must be non-empty list")
    for j, mirror in enumerate(mirrors):
        _validate_managed_block_mirror(mirror, f"{prefix}.mirrors[{j}]")


def _validate_managed_block_mirror(mirror: Any, prefix: str) -> None:
    """Validate a single managed-block mirror entry.

    Same shape as ``vendored_files`` mirrors for ``repo`` + ``path``, but
    here ``path`` is the same as the parent entry's ``target_file`` in
    every case — kept as a separate field for parallelism with
    ``vendored_files[*].mirrors[*].path`` and to allow future divergence.
    """
    if not isinstance(mirror, dict):
        raise ManifestError(f"{prefix} must be object")
    for key in ("repo", "path"):
        val = mirror.get(key)
        if not isinstance(val, str) or not val:
            raise ManifestError(f"{prefix}.{key} must be non-empty string")
    transforms = mirror.get("transforms", [])
    if not isinstance(transforms, list):
        raise ManifestError(f"{prefix}.transforms must be list")
    for k, name in enumerate(transforms):
        if not isinstance(name, str) or not name:
            raise ManifestError(
                f"{prefix}.transforms[{k}] must be non-empty string"
            )
        if name not in TRANSFORMS:
            raise ManifestError(
                f"{prefix}.transforms[{k}] unknown transform '{name}'. "
                f"Registry: {sorted(TRANSFORMS.keys())}"
            )


def _validate_unmirrored_entry(entry: Any, index: int) -> None:
    """Enforce `unmirrored_canonical_files` entry schema.

    Accepts plain strings (canonical-path back-compat) OR objects
    `{path: non-empty str, reason: non-empty str}` documenting intentional
    per-repo divergence (#442 GAP 3.1 / 3.4a). Anything else raises.
    """
    prefix = f"unmirrored_canonical_files[{index}]"
    if isinstance(entry, str):
        if not entry:
            raise ManifestError(f"{prefix} string entry must be non-empty")
        return
    if not isinstance(entry, dict):
        raise ManifestError(
            f"{prefix} must be a string path or object with 'path' + 'reason' keys; "
            f"got {type(entry).__name__}"
        )
    path = entry.get("path")
    if not isinstance(path, str) or not path:
        raise ManifestError(f"{prefix}.path must be non-empty string")
    reason = entry.get("reason")
    if not isinstance(reason, str) or not reason:
        raise ManifestError(
            f"{prefix}.reason must be non-empty string "
            f"(documents why {path} is intentionally not mirrored)"
        )


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


_WORKTREE_SEG = "/.claude/worktrees/"


def resolve_dotfiles_root(manifest_path: Path) -> Path:
    """Return the CANONICAL root — the working tree that actually contains
    this manifest (and therefore the canonical files to read/validate).

    #488 Fix-A correction (Option A). The manifest is ALWAYS at
    `<root>/SST3/drift-manifest.json`, and `find_manifest()` resolves it
    relative to `__file__`, so when invoked from inside an `EnterWorktree`
    worktree this deterministically returns the WORKTREE root — exactly
    where the in-flight #488 canonical edits live. The prior P1 attempt used
    `git --git-common-dir` to return the MAIN clone instead; that was both
    (a) env-fragile — it silently fell back inside the pre-commit hook
    sandbox, yielding the bogus `<wt>/.claude/worktrees/SST3-AI-Harness`
    mirror path that hard-blocked every worktree vendored commit — and
    (b) conceptually wrong: reading canonical from main-clone@master means a
    worktree branch's edits are never the bytes validated/propagated. Pure
    deterministic path math here: no git subprocess, no environment
    sensitivity. The MAIN clone (for sibling mirror/consumer resolution) is
    a SEPARATE concern — see `resolve_main_clone_root`.
    """
    return manifest_path.resolve().parent.parent


def resolve_main_clone_root(manifest_path: Path) -> Path:
    """Return the MAIN clone root (the sibling-resolution base under
    `DevProjects/`), env-immune.

    Mirror repos (`SST3-AI-Harness`) and KNOWN_REPOS consumers live as
    siblings of the MAIN `dotfiles/` clone, NOT of a linked worktree. A
    linked worktree's manifest path contains the `/.claude/worktrees/<name>/`
    segment; the MAIN clone is the prefix before that segment. In the main
    clone itself there is no such segment and the canonical root already IS
    the main clone. Derived purely from path structure (no git subprocess —
    immune to the pre-commit-sandbox env quirk that broke the P1 attempt);
    a loud sanity check rejects an implausible result rather than silently
    returning a bogus path (Fail-Fast — the failure mode #488 forbids).
    """
    resolved = manifest_path.resolve()
    s = str(resolved)
    if _WORKTREE_SEG in s:
        main = Path(s.split(_WORKTREE_SEG, 1)[0])
    else:
        main = resolved.parent.parent
    if not (main / "SST3" / MANIFEST_FILENAME).is_file():
        raise ManifestError(
            f"resolve_main_clone_root: derived main clone {main} has no "
            f"SST3/{MANIFEST_FILENAME} (manifest={resolved}). Refusing to "
            f"return an unverified sibling-resolution base."
        )
    return main


def in_linked_worktree(manifest_path: Path) -> bool:
    """True iff invoked from an `EnterWorktree` linked worktree (canonical
    root differs from the main clone root)."""
    return (
        resolve_dotfiles_root(manifest_path).resolve()
        != resolve_main_clone_root(manifest_path).resolve()
    )


def resolve_canonical(manifest_path: Path, canonical_rel: str) -> Path:
    """Resolve a manifest `canonical` field to an absolute path (reads from
    the canonical root — the worktree when run from one, so #488 in-flight
    edits ARE the validated/propagated bytes)."""
    return resolve_dotfiles_root(manifest_path) / canonical_rel


def resolve_mirror(manifest_path: Path, mirror_repo: str, mirror_rel: str) -> Path:
    """Resolve a manifest mirror entry to an absolute path.

    Mirror repos live as siblings of the MAIN `dotfiles/` clone under
    `DevProjects/` — NEVER as siblings of a linked worktree.
    """
    devprojects = resolve_main_clone_root(manifest_path).parent
    return devprojects / mirror_repo / mirror_rel


def resolve_self_row_destination(
    manifest_path: Path, mirror_repo: str, mirror_rel: str
) -> Path:
    """Resolve a mirror destination with worktree-aware self-row routing
    (dotfiles#495 FRAG-1 / AC 2.1).

    When invoked from a LINKED WORKTREE AND the mirror's `repo` is `dotfiles`
    (the harness self-row), return the WORKTREE path (so an in-flight
    canonical edit lands in the worktree's solo branch, mergeable via Gate-2
    server-FF without a post-merge `--apply` from the main clone). Otherwise
    delegate to `resolve_mirror` (consumer-repo mirrors always resolve to
    main-clone siblings; main-clone invocations resolve the dotfiles self-row
    in the main clone exactly as before).

    Pure deterministic path math via the existing primitives:
    `resolve_dotfiles_root(manifest_path) / mirror_rel` for the worktree
    self-row case; `resolve_mirror(manifest_path, mirror_repo, mirror_rel)`
    for every other case.
    """
    if in_linked_worktree(manifest_path) and mirror_repo == "dotfiles":
        return resolve_dotfiles_root(manifest_path) / mirror_rel
    return resolve_mirror(manifest_path, mirror_repo, mirror_rel)


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


def iter_managed_block_entries(
    manifest: dict[str, Any],
    *,
    repo_filter: str | None = None,
    file_filter: str | None = None,
) -> Iterable[tuple[dict[str, Any], dict[str, Any]]]:
    """Yield (entry, mirror) pairs from `manifest['managed_blocks']` matching filters.

    Mirrors the shape of `iter_mirror_entries` so propagate-block.py can use
    the same loop pattern as propagate-mirrors.py. The `file_filter` matches
    against `entry['canonical']` (the source template path); `repo_filter`
    matches against `mirror['repo']`. Returns nothing if `managed_blocks` is
    absent or empty.

    Issue #493 AC 1.5.
    """
    for entry in manifest.get("managed_blocks", []):
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
    # dotfiles#495 FRAG-1: use worktree-aware resolution so the dotfiles
    # self-row mirror check looks at the WORKTREE's mirror file (synced via
    # --apply from the same worktree). Consumer-row mirrors are unchanged
    # (resolve_self_row_destination delegates to resolve_mirror for non-dotfiles).
    mirror_path = resolve_self_row_destination(
        manifest_path, mirror["repo"], mirror["path"]
    )

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
