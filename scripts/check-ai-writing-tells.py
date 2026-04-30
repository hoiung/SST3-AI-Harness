#!/usr/bin/env python3
"""
Marker-driven voice guard for Hoi-voice content (CV + blog modes).

Default = SKIP. A file is scanned only if mode-specific rules match.

Modes (selected via --mode):
  cv (default): scan WHOLE_FILE_SCAN_GLOBS_CV first (precedence over markers
      per dotfiles#433 em-dash slip post-mortem 2026-04-24), then iamhoi
      region scan, otherwise SKIP. No frontmatter date filter.
  blog: scan iamhoi regions first, then PUBLIC_FACING_GLOBS_BLOG legacy
      whitelist (currently empty), otherwise SKIP. With --check-only-new
      (default ON for blog mode) files in content/posts/ dated <
      HOIBOY_CUTOFF_DATE are skipped (legacy voice-sacred corpus).

Rules: imported from voice_rules.py (single source of truth).
Human-readable companion: cv-linkedin/VOICE_PROFILE.md Section 8 / 19.

Issue: hoiung/dotfiles#404 (canonical) + hoiung/hoiboy-uk#3 (mirror, since
       merged via hoiung/dotfiles#460 --mode unification, which also fixes
       the blog-priv research-file silent-skip bug).
Exit codes: 0 = clean, 1 = findings (block commit / fail CI)
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

try:
    from sst3_utils import fix_windows_console
except ImportError:  # consumer mirror without sst3_utils vendored
    def fix_windows_console() -> None:
        return None

from voice_rules import (
    BANNED_PHRASES_PATTERN,
    BANNED_WORDS_PATTERN,
    BOLD_BULLET_PATTERN,
    BOLD_BULLET_THRESHOLD_CV,
    BOLD_BULLET_THRESHOLD_DEFAULT,
    EM_DASH,
    Finding,
    FRONTMATTER_DATE_PATTERN,
    HOIBOY_CUTOFF_DATE,
    MARKER_CLOSE_HASH,
    MARKER_CLOSE_HTML,
    MARKER_EXEMPT_HASH,
    MARKER_EXEMPT_HTML,
    MARKER_OPEN_HASH,
    MARKER_OPEN_HTML,
    MARKER_SKIP_CLOSE_HASH,
    MARKER_SKIP_CLOSE_HTML,
    MARKER_SKIP_OPEN_HASH,
    MARKER_SKIP_OPEN_HTML,
    NEGATION_PATTERN,
    SMART_QUOTE_CHARS,
    UNICODE_ARROW_CHARS,
)

fix_windows_console()


# ---------------------------------------------------------------------------
# Mode-specific configuration
# ---------------------------------------------------------------------------

# CV mode: whole-file scan for recruiter-facing CVs (em-dash slip
# post-mortem #433 — CV Experience bullets sit outside the Summary
# iamhoi block, so region-only scanning let em-dashes through).
WHOLE_FILE_SCAN_GLOBS_CV: tuple[str, ...] = (
    "cv-linkedin/CV_AI_TRANSFORMATION.md",
    "cv-linkedin/CV_AI_TRANSFORMATION_FULL.md",
)

# CV mode: mixed-content scaffolding around voice copy-paste blocks;
# region scan fires automatically when markers exist.
REGION_SCAN_GLOBS_CV: tuple[str, ...] = (
    "cv-linkedin/LINKEDIN_UPDATE_GUIDE.md",
    "cv-linkedin/AI_SKILLS_AND_PORTFOLIO.md",
)

# CV mode: paths NEVER scanned (#405 Phase 7 — MASTER_PROFILE.md is
# the canonical voice corpus; treating it as exempt prevents iamhoi
# whitelist from sanitising thousands of authentic Hoi vocabulary uses).
EXEMPT_PATHS_CV: tuple[str, ...] = (
    "SST3/",
    "cv-linkedin/job-research/",
    "cv-linkedin/voice-corpus/",
    "cv-linkedin/voice-analysis-reports/",
    "cv-linkedin/MASTER_PROFILE.md",
    "cv-linkedin/METRIC_PROVENANCE.md",
    "cv-linkedin/VOICE_PROFILE.md",
    "cv-linkedin/PERSONA_CONTEXT.md",
    "cv-linkedin/INTERVIEW_PREP_BANK.md",
    "cv-linkedin/HIRER_PROFILE.md",
    ".claude/",
    "docs/",
)

# Blog mode: default file selection (run by CI on the whole content/
# + docs/research/ tree).
DEFAULT_PATHS_BLOG: tuple[str, ...] = (
    "content/posts",
    "content/_index.md",
    "content/about.md",
    "docs/research",
)

# Blog mode: whole-file scan whitelist. Currently empty — all hoiboy-uk
# content is marker-opt-in or cutoff-filtered.
PUBLIC_FACING_GLOBS_BLOG: tuple[str, ...] = ()

# Blog mode: paths NEVER scanned regardless of markers. The voice
# guard plan / profile / AI tells docs quote banned words verbatim
# in code fences and would trip the state machine.
EXEMPT_PATHS_BLOG: tuple[str, ...] = (
    "legacy/",
    ".github/",
    "node_modules/",
    "public/",
    "docs/research/11_VOICE_PROFILE.md",
    "docs/research/12_AI_WRITING_TELLS.md",
    "docs/research/13_VOICE_GUARD_PLAN.md",
)


def detect_repo_root(start: Path) -> Path:
    """Walk up from `start` looking for the nearest .git directory.

    Mirror-portable: works whether the script lives at SST3/scripts/
    (dotfiles canonical, parents[2] = repo root) or scripts/ (consumer
    mirror, parents[1] = repo root).
    """
    cur = start.resolve()
    if cur.is_file():
        cur = cur.parent
    while cur != cur.parent:
        if (cur / ".git").exists():
            return cur
        cur = cur.parent
    raise RuntimeError(f"could not detect repo root from {start}")


# ---------------------------------------------------------------------------
# Region extraction (single-pass state machine)
# ---------------------------------------------------------------------------
def extract_voice_regions(text: str) -> list[tuple[int, str]]:
    """
    Parse text line-by-line, return list of (lineno, line_text) tuples for
    every line inside <!-- iamhoi --> ... <!-- iamhoiend --> regions, with
    any <!-- iamhoi-skip --> ... <!-- iamhoi-skipend --> sub-regions excluded.
    Line numbers are 1-indexed and reference the original file (so checker
    findings cite the real line, even across skip-holes).

    Hard-fails (raises ValueError) on:
      - unclosed iamhoi marker
      - nested iamhoi marker
      - orphan iamhoi-skip
      - iamhoi-exempt after first non-blank line
      - multiple iamhoi-exempt markers
      - mixed HTML and `# ` syntax in one file

    Returns [] if file is exempt or has no markers.
    """
    lines = text.split("\n")

    # Detect syntax mixing.
    html_markers = (
        MARKER_OPEN_HTML, MARKER_CLOSE_HTML, MARKER_EXEMPT_HTML,
        MARKER_SKIP_OPEN_HTML, MARKER_SKIP_CLOSE_HTML,
    )
    hash_markers = (
        MARKER_OPEN_HASH, MARKER_CLOSE_HASH, MARKER_EXEMPT_HASH,
        MARKER_SKIP_OPEN_HASH, MARKER_SKIP_CLOSE_HASH,
    )
    has_html = any(m in text for m in html_markers)
    has_hash = any(
        any(line.strip() == m for line in lines) for m in hash_markers
    )
    if has_html and has_hash:
        raise ValueError(
            "mixed HTML <!-- iamhoi --> and # iamhoi syntax in one file (hard fail)"
        )

    if not has_html and not has_hash:
        return []

    if has_html:
        OPEN, CLOSE, EXEMPT = MARKER_OPEN_HTML, MARKER_CLOSE_HTML, MARKER_EXEMPT_HTML
        SKIP_OPEN, SKIP_CLOSE = MARKER_SKIP_OPEN_HTML, MARKER_SKIP_CLOSE_HTML
    else:
        OPEN, CLOSE, EXEMPT = MARKER_OPEN_HASH, MARKER_CLOSE_HASH, MARKER_EXEMPT_HASH
        SKIP_OPEN, SKIP_CLOSE = MARKER_SKIP_OPEN_HASH, MARKER_SKIP_CLOSE_HASH

    # Exempt validation: first non-blank line only, exactly once.
    exempt_lines = [i for i, line in enumerate(lines) if line.strip() == EXEMPT]
    if exempt_lines:
        if len(exempt_lines) > 1:
            raise ValueError(
                f"multiple iamhoi-exempt markers (lines {[n+1 for n in exempt_lines]}) (hard fail)"
            )
        first_nonblank = next((i for i, line in enumerate(lines) if line.strip()), None)
        if exempt_lines[0] != first_nonblank:
            raise ValueError(
                f"iamhoi-exempt must be the first non-blank line (found at line {exempt_lines[0]+1}) (hard fail)"
            )
        return []

    out: list[tuple[int, str]] = []
    in_region = False
    in_skip = False
    region_start = 0
    skip_start = 0

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped == OPEN:
            if in_region:
                raise ValueError(
                    f"nested iamhoi marker at line {i+1} (hard fail)"
                )
            in_region = True
            region_start = i + 1
            continue
        if stripped == CLOSE:
            if not in_region:
                raise ValueError(
                    f"iamhoiend without matching iamhoi at line {i+1} (hard fail)"
                )
            if in_skip:
                raise ValueError(
                    f"iamhoiend inside iamhoi-skip block at line {i+1} (hard fail)"
                )
            in_region = False
            continue
        if stripped == SKIP_OPEN:
            if not in_region:
                raise ValueError(
                    f"orphan iamhoi-skip at line {i+1} (must be inside an iamhoi block) (hard fail)"
                )
            if in_skip:
                raise ValueError(
                    f"nested iamhoi-skip at line {i+1} (hard fail)"
                )
            in_skip = True
            skip_start = i + 1
            continue
        if stripped == SKIP_CLOSE:
            if not in_skip:
                raise ValueError(
                    f"iamhoi-skipend without matching iamhoi-skip at line {i+1} (hard fail)"
                )
            in_skip = False
            continue
        if in_region and not in_skip:
            out.append((i + 1, line))

    if in_region:
        raise ValueError(
            f"unclosed iamhoi marker (opened at line {region_start}) (hard fail)"
        )
    if in_skip:
        raise ValueError(
            f"unclosed iamhoi-skip (opened at line {skip_start}) (hard fail)"
        )

    return out


# ---------------------------------------------------------------------------
# Per-line checks
# ---------------------------------------------------------------------------
def _check_lines(
    numbered_lines: list[tuple[int, str]], file: str
) -> list[Finding]:
    findings: list[Finding] = []
    for ln, line in numbered_lines:
        if EM_DASH in line:
            findings.append(Finding(file, ln, "EM_DASH", line.strip()[:100]))
        for m in BANNED_WORDS_PATTERN.finditer(line):
            findings.append(
                Finding(file, ln, "AI_WORD", f'"{m.group(0)}": {line.strip()[:80]}')
            )
        for m in BANNED_PHRASES_PATTERN.finditer(line):
            findings.append(
                Finding(file, ln, "AI_PHRASE", f'"{m.group(0)}": {line.strip()[:80]}')
            )
        for ch in SMART_QUOTE_CHARS:
            if ch in line:
                findings.append(
                    Finding(file, ln, "SMART_QUOTE", line.strip()[:100])
                )
                break
        for ch in UNICODE_ARROW_CHARS:
            if ch in line:
                findings.append(
                    Finding(file, ln, "UNICODE_ARROW", line.strip()[:100])
                )
                break
        if NEGATION_PATTERN.search(line):
            findings.append(
                Finding(file, ln, "NEGATION_FRAME", line.strip()[:100])
            )
    return findings


def _check_bold_bullets(text: str, file: str, is_cv: bool) -> list[Finding]:
    # Whole-file scan only. Marker regions are short prose and never need this
    # check; skipping them avoids 99% of false positives. Threshold imported
    # from voice_rules.py (single source) — fixes #460 AC 1.4 hardcoded literal.
    threshold = BOLD_BULLET_THRESHOLD_CV if is_cv else BOLD_BULLET_THRESHOLD_DEFAULT
    matches = BOLD_BULLET_PATTERN.findall(text)
    if len(matches) > threshold:
        return [Finding(
            file, 0, "BOLD_BULLET",
            f"{len(matches)} bold-first bullets (threshold: {threshold})",
        )]
    return []


# ---------------------------------------------------------------------------
# File scan dispatcher (mode-aware)
# ---------------------------------------------------------------------------
def is_exempt(file_path: Path, repo_root: Path, exempt_paths: tuple[str, ...]) -> bool:
    rel = str(file_path.relative_to(repo_root))
    return any(rel.startswith(p) for p in exempt_paths)


def is_whitelisted(file_path: Path, repo_root: Path, whitelist: tuple[str, ...]) -> bool:
    """Whole-file scan whitelist."""
    rel = str(file_path.relative_to(repo_root))
    return rel in whitelist


def scan_file(file_path: Path, repo_root: Path, mode: str) -> list[Finding]:
    """
    Mode-aware decision matrix (default = SKIP):

    CV mode (recruiter-facing CVs — whitelist takes precedence over markers
    so em-dashes in CV Experience bullets outside the Summary iamhoi block
    are caught — see #433 post-mortem):
      iamhoi-exempt path        -> SKIP
      whole-file-scan whitelist -> scan whole file
      iamhoi markers present    -> scan tagged regions only
      otherwise                 -> SKIP

    Blog mode (Hugo blog content — region-first matches the legacy
    hoiboy-uk variant's behaviour; whitelist is currently empty):
      iamhoi-exempt path        -> SKIP
      iamhoi markers present    -> scan tagged regions only
      whole-file-scan whitelist -> scan whole file (back-compat, empty for now)
      otherwise                 -> SKIP
    """
    if mode == "cv":
        exempt = EXEMPT_PATHS_CV
        whitelist = WHOLE_FILE_SCAN_GLOBS_CV
    else:
        exempt = EXEMPT_PATHS_BLOG
        whitelist = PUBLIC_FACING_GLOBS_BLOG

    if is_exempt(file_path, repo_root, exempt):
        return []

    try:
        # utf-8-sig transparently strips BOM. Normalise CRLF/CR to LF
        # so line offsets are stable on Windows-authored files.
        raw = file_path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError) as e:
        return [Finding(str(file_path), 0, "READ_ERROR", str(e))]
    text = raw.replace("\r\n", "\n").replace("\r", "\n")
    file_str = str(file_path)

    if mode == "cv":
        if is_whitelisted(file_path, repo_root, whitelist):
            is_cv = file_path.name.startswith("CV_AI_TRANSFORMATION")
            numbered = list(enumerate(text.split("\n"), 1))
            findings = _check_lines(numbered, file_str)
            findings.extend(_check_bold_bullets(text, file_str, is_cv))
            return findings
        try:
            regions = extract_voice_regions(text)
        except ValueError as e:
            return [Finding(file_str, 0, "MARKER_ERROR", str(e))]
        if regions:
            return _check_lines(regions, file_str)
        return []

    # blog mode: region-first, then legacy whitelist (currently empty).
    try:
        regions = extract_voice_regions(text)
    except ValueError as e:
        return [Finding(file_str, 0, "MARKER_ERROR", str(e))]
    if regions:
        return _check_lines(regions, file_str)
    if is_whitelisted(file_path, repo_root, whitelist):
        is_cv = "CV_AI_TRANSFORMATION" in file_str
        numbered = list(enumerate(text.split("\n"), 1))
        findings = _check_lines(numbered, file_str)
        findings.extend(_check_bold_bullets(text, file_str, is_cv))
        return findings
    return []


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
TYPE_LABELS = {
    "EM_DASH": "Em Dashes (AI punctuation tell)",
    "AI_WORD": "AI-Flagged Words",
    "AI_PHRASE": "AI-Flagged Phrases",
    "SMART_QUOTE": "Smart Quotes (use ASCII quotes)",
    "UNICODE_ARROW": "Unicode Arrows (use plain text)",
    "BOLD_BULLET": "Bold-First Bullet Pattern",
    "NEGATION_FRAME": "Negation Framing (\"It's not X, it's Y\")",
    "MARKER_ERROR": "Voice Guard Marker Error (hard fail)",
    "READ_ERROR": "File Read Error",
}


def parse_post_date(file_path: Path) -> date | None:
    """
    Parse the frontmatter `date:` field via stdlib regex (NOT PyYAML).
    Returns date or None if file has no frontmatter date field.
    Hard-fails (raises ValueError) on malformed `date:` lines.
    """
    try:
        text = file_path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError):
        return None
    # Look only inside the first YAML frontmatter block (between --- markers)
    # to avoid matching `date:` strings deeper in the body.
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        raise ValueError(f"{file_path}: unterminated frontmatter")
    front = text[3:end]
    if "date:" not in front:
        return None
    m = FRONTMATTER_DATE_PATTERN.search(front)
    if not m:
        raise ValueError(
            f"{file_path}: malformed frontmatter `date:` (must be YYYY-MM-DD)"
        )
    return date.fromisoformat(m.group(1))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Marker-driven voice guard (CV / blog modes).",
    )
    parser.add_argument(
        "--mode", choices=["cv", "blog"], default="cv",
        help="Scan mode: cv (recruiter-facing CV repos, default) or blog (Hugo blog).",
    )
    parser.add_argument(
        "--check-only-new", dest="check_only_new",
        action="store_true", default=None,
        help="(blog mode) Skip posts dated < HOIBOY_CUTOFF_DATE. Default ON in blog mode.",
    )
    parser.add_argument(
        "--no-check-only-new", dest="check_only_new", action="store_false",
        help="(blog mode) Disable cutoff filter; scan all dated posts (e.g. blog-priv research files).",
    )
    parser.add_argument("paths", nargs="*", help="Files / dirs to scan; uses mode defaults if empty.")
    args = parser.parse_args()

    # Default check_only_new = True in blog mode (back-compat with hoiboy-uk
    # pre-commit hook); ignored in cv mode.
    if args.check_only_new is None:
        args.check_only_new = (args.mode == "blog")

    repo_root = detect_repo_root(Path(__file__).resolve())
    files_to_scan: list[Path] = []

    if args.paths:
        for arg in args.paths:
            p = Path(arg).resolve()
            if p.is_dir():
                files_to_scan.extend(sorted(p.rglob("*.md")))
            elif p.exists() and p.suffix == ".md":
                files_to_scan.append(p)
    else:
        if args.mode == "cv":
            for glob_pattern in (*WHOLE_FILE_SCAN_GLOBS_CV, *REGION_SCAN_GLOBS_CV):
                for p in repo_root.glob(glob_pattern):
                    if p.exists():
                        files_to_scan.append(p)
        else:
            for rel in DEFAULT_PATHS_BLOG:
                p = repo_root / rel
                if p.is_dir():
                    files_to_scan.extend(sorted(p.rglob("*.md")))
                elif p.exists():
                    files_to_scan.append(p)

    # Cutoff-date filter (blog mode + check_only_new only).
    if args.mode == "blog" and args.check_only_new:
        kept: list[Path] = []
        for f in files_to_scan:
            try:
                rel = f.relative_to(repo_root)
            except ValueError:
                rel = f
            if str(rel).startswith("content/posts"):
                try:
                    d = parse_post_date(f)
                except ValueError as e:
                    print(f"[ERROR] {e}", file=sys.stderr)
                    return 1
                if d is not None and d < HOIBOY_CUTOFF_DATE:
                    continue
            kept.append(f)
        files_to_scan = kept

    if not files_to_scan:
        print("[OK] No files to scan")
        return 0

    all_findings: list[Finding] = []
    for f in files_to_scan:
        all_findings.extend(scan_file(f, repo_root, args.mode))

    if not all_findings:
        print(f"[OK] No voice tells found in {len(files_to_scan)} files")
        return 0

    print("=" * 60)
    print("VOICE GUARD: TELLS DETECTED")
    print("=" * 60)
    print()

    by_type: dict[str, list[Finding]] = {}
    for f in all_findings:
        by_type.setdefault(f.type, []).append(f)

    for tell_type, findings in by_type.items():
        label = TYPE_LABELS.get(tell_type, tell_type)
        print(f"[{label}] ({len(findings)} occurrences)")
        for f in findings[:10]:
            loc = f"{Path(f.file).name}:{f.line}" if f.line else Path(f.file).name
            print(f"  {loc}: {f.detail}")
        if len(findings) > 10:
            print(f"  ... and {len(findings) - 10} more")
        print()

    print(f"TOTAL: {len(all_findings)} tells in {len(files_to_scan)} files")
    print()
    print("Fix: cv-linkedin/VOICE_PROFILE.md Sections 8 + 19")
    print("Wrap quoted/example prose in <!-- iamhoi-skip --> ... <!-- iamhoi-skipend -->")
    return 1


if __name__ == "__main__":
    sys.exit(main())
