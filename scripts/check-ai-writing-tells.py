#!/usr/bin/env python3
"""
Marker-driven voice guard for Hoi-voice content.

Default = SKIP. A file is scanned if:
  (a) it is in PUBLIC_FACING_GLOBS (whole-file scan; takes precedence over markers)
  (b) OR it contains <!-- iamhoi --> ... <!-- iamhoiend --> markers (region scan)

Anything else is silently skipped. Whitelisted files are scanned in full
regardless of iamhoi markers, because 100% of their content is Hoi-voice
and recruiter-facing.

Rules: imported from voice_rules.py (single source of truth).
Human-readable companion: cv-linkedin/VOICE_PROFILE.md Section 8 / 19.

Issue: hoiung/dotfiles#404
Exit codes: 0 = clean, 1 = findings (block commit / fail CI)
"""

from __future__ import annotations

import sys
from pathlib import Path

from sst3_utils import fix_windows_console
from voice_rules import (
    BANNED_PHRASES_PATTERN,
    BANNED_WORDS_PATTERN,
    BOLD_BULLET_PATTERN,
    BOLD_BULLET_THRESHOLD_CV,
    BOLD_BULLET_THRESHOLD_DEFAULT,
    EM_DASH,
    Finding,
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

# Whole-file scan: files where 100% of content is Hoi-voice, recruiter-
# facing. Takes precedence over iamhoi region scan. Per dotfiles#433
# em-dash slip post-mortem (2026-04-24): CV Experience bullets sit
# outside the Summary iamhoi block, so the original region-only scan
# let em-dashes through. These files get scanned in full.
WHOLE_FILE_SCAN_GLOBS: tuple[str, ...] = (
    "cv-linkedin/CV_AI_TRANSFORMATION.md",
    "cv-linkedin/CV_AI_TRANSFORMATION_FULL.md",
)

# Mixed content: metadata / instructional scaffolding around voice
# copy-paste blocks. Rely on iamhoi markers around the actual voice
# prose (the copy-paste blocks). Listed here for clarity only — the
# region scan fires automatically when markers exist.
REGION_SCAN_GLOBS: tuple[str, ...] = (
    "cv-linkedin/LINKEDIN_UPDATE_GUIDE.md",
    "cv-linkedin/AI_SKILLS_AND_PORTFOLIO.md",
)

# Internal AI-to-AI docs that should NEVER be scanned.
# Per dotfiles#405 Phase 7 — MASTER_PROFILE.md is the canonical voice corpus
# (Hoi's pre-AI writing). Treating it as exempt prevents the iamhoi region-tag
# whitelist from forcing voice-rule sanitisation across thousands of authentic
# Hoi vocabulary uses. Single source of truth: voice_rules.py KEEP_LIST +
# VOICE_PROFILE.md Section 8.
EXEMPT_PATHS: tuple[str, ...] = (
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
    # Whole-file scan only (legacy whitelist). Marker regions are short prose
    # and never need this check; skipping them avoids 99% of false positives.
    threshold = BOLD_BULLET_THRESHOLD_CV if is_cv else BOLD_BULLET_THRESHOLD_DEFAULT
    matches = BOLD_BULLET_PATTERN.findall(text)
    if len(matches) > threshold:
        return [Finding(
            file, 0, "BOLD_BULLET",
            f"{len(matches)} bold-first bullets (threshold: {threshold})",
        )]
    return []


# ---------------------------------------------------------------------------
# File scan dispatcher
# ---------------------------------------------------------------------------
def is_exempt(file_path: Path, repo_root: Path) -> bool:
    rel = str(file_path.relative_to(repo_root))
    return any(rel.startswith(p) for p in EXEMPT_PATHS)


def is_whitelisted(file_path: Path, repo_root: Path) -> bool:
    """Whole-file scan whitelist — 100% Hoi-voice recruiter-facing files."""
    rel = str(file_path.relative_to(repo_root))
    return rel in WHOLE_FILE_SCAN_GLOBS


def scan_file(file_path: Path, repo_root: Path) -> list[Finding]:
    """
    Decision matrix (default = SKIP):
      iamhoi-exempt path        -> SKIP
      whitelisted file          -> scan whole file (markers are doc-only here)
      iamhoi markers present    -> scan tagged regions only
      otherwise                 -> SKIP

    Whitelisted files (PUBLIC_FACING_GLOBS) take precedence over region
    scanning: the whole file is Hoi-voice content, so the whole file is
    scanned even if iamhoi markers exist elsewhere in the document.
    Previously the region branch short-circuited the whole-file scan,
    which let em-dashes slip through in CV Experience bullets that sit
    outside the Summary iamhoi block. See dotfiles#433 em-dash slip
    post-mortem (2026-04-24).
    """
    if is_exempt(file_path, repo_root):
        return []

    try:
        # utf-8-sig transparently strips BOM. Normalise CRLF/CR to LF
        # so line offsets are stable on Windows-authored files.
        raw = file_path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError) as e:
        return [Finding(str(file_path), 0, "READ_ERROR", str(e))]
    text = raw.replace("\r\n", "\n").replace("\r", "\n")

    file_str = str(file_path)

    if is_whitelisted(file_path, repo_root):
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


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    files_to_scan: list[Path] = []

    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            p = Path(arg).resolve()
            if p.is_dir():
                files_to_scan.extend(sorted(p.rglob("*.md")))
            elif p.exists() and p.suffix == ".md":
                files_to_scan.append(p)
    else:
        for glob_pattern in (*WHOLE_FILE_SCAN_GLOBS, *REGION_SCAN_GLOBS):
            for p in repo_root.glob(glob_pattern):
                if p.exists():
                    files_to_scan.append(p)

    if not files_to_scan:
        print("[OK] No files to scan")
        return 0

    all_findings: list[Finding] = []
    for f in files_to_scan:
        all_findings.extend(scan_file(f, repo_root))

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
