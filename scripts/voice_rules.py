#!/usr/bin/env python3
"""
Single source of truth for Hoi-voice guard rules.

Canonical Python copy of the rules described in the human-readable companion
`cv-linkedin/VOICE_PROFILE.md` Section 8 (anti-vocabulary) and Section 19
(banned phrases / AI tells Hoi never makes).

This module is consumed by:
  - dotfiles/SST3/scripts/check-ai-writing-tells.py  (canonical hook)
  - hoiboy-uk/scripts/check_voice_tells.py           (vendored byte-identical)
  - hoiboy-uk/scripts/voice_rules.py                 (vendored byte-identical)

Drift between canonical and vendored copies is enforced by a `cmp -s` bash
pre-commit hook in hoiboy-uk. There is no parsed mirror of VOICE_PROFILE.md;
the markdown is documentation, this file is the executable canonical.

Issue: hoiung/dotfiles#404
"""

from dataclasses import dataclass
from datetime import date
import re

# ---------------------------------------------------------------------------
# Cutoff date — hoiboy-uk legacy/new boundary
# ---------------------------------------------------------------------------
# Posts dated < this date are voice-sacred legacy and exempt from scanning.
# Posts dated >= this date are eligible (default still SKIP unless tagged).
HOIBOY_CUTOFF_DATE: date = date(2026, 4, 7)

# ---------------------------------------------------------------------------
# Markers (greenfield convention; HTML-comment form invisible in render)
# ---------------------------------------------------------------------------
MARKER_OPEN_HTML = "<!-- iamhoi -->"
MARKER_CLOSE_HTML = "<!-- iamhoiend -->"
MARKER_EXEMPT_HTML = "<!-- iamhoi-exempt -->"
MARKER_SKIP_OPEN_HTML = "<!-- iamhoi-skip -->"
MARKER_SKIP_CLOSE_HTML = "<!-- iamhoi-skipend -->"

MARKER_OPEN_HASH = "# iamhoi"
MARKER_CLOSE_HASH = "# iamhoiend"
MARKER_EXEMPT_HASH = "# iamhoi-exempt"
MARKER_SKIP_OPEN_HASH = "# iamhoi-skip"
MARKER_SKIP_CLOSE_HASH = "# iamhoi-skipend"

# ---------------------------------------------------------------------------
# Single characters / small char sets
# ---------------------------------------------------------------------------
EM_DASH: str = "\u2014"
SMART_QUOTE_CHARS: tuple[str, ...] = ("\u201c", "\u201d", "\u2018", "\u2019")
UNICODE_ARROW_CHARS: tuple[str, ...] = ("\u2192", "\u21d2", "\u2190", "\u21d0")

# ---------------------------------------------------------------------------
# KEEP list — authentic Hoi vocabulary (NEVER add to BANNED_WORDS)
# ---------------------------------------------------------------------------
# These words are used sincerely by Hoi 50+ times across his pre-AI corpus.
# Documented in cv-linkedin/VOICE_PROFILE.md Section 8.
KEEP_LIST: tuple[str, ...] = (
    "passion",
    "passionate",
    "journey",
    "deeply",
    "truly",
    "navigate",
    "back to basics",
    "attention to detail",
    "fundamentals",
    "fall in love",
    # align* family — Hoi's natural vocabulary for project timeline /
    # expectation management. Whitelisted 2026-04-22 per meta-rule
    # "if I type it, I use it" (see memory/feedback_if_i_type_it_i_use_it.md).
    "align",
    "alignment",
    "aligned",
    "aligning",
    "aligns",
    "alignments",
    # Additional whitelist 2026-04-22 — Hoi confirmed these are his natural
    # vocabulary in the same conversation (enterprise/project words he uses
    # in emails, chats, prep). Same meta-rule as align*.
    "synergy", "synergies",
    "leverage", "leveraging", "leveraged",
    "robust",
    "landscape",
    "dynamic",
    "deliverable", "deliverables",
    "bandwidth",
    "actionable",
)

# ---------------------------------------------------------------------------
# Banned words — full Section 8 anti-vocabulary list (~60 entries)
# ---------------------------------------------------------------------------
# Multi-word entries are matched as whole phrases (the `\b...\b` regex around
# escaped strings handles spaces correctly). Inflections are listed explicitly
# for fail-fast behaviour rather than relying on stemming.
BANNED_WORDS: tuple[str, ...] = (
    # Single-word AI/CV-speak
    "delve", "delving", "delved",
    "spearhead", "spearheading", "spearheaded",
    "stakeholder", "stakeholders",
    "seamless", "seamlessly",
    "cutting-edge",
    "innovative",
    "impactful",
    "facilitate", "facilitating", "facilitated",
    "furthermore",
    "moreover",
    "pivotal",
    "tapestry",
    "realm",
    "underscore", "underscores", "underscoring",
    "meticulous", "meticulously",
    "beacon",
    "testament",
    "holistic", "holistically",
    "ecosystem",
    "iterate", "iterating",
    "unpack", "unpacking",
    "utilize", "utilizing", "utilized", "utilise", "utilising", "utilised",
    "commendable",
    "noteworthy",
    "invaluable",
    "resonate", "resonates", "resonating",
    "crucial",
    # Multi-word AI/CV-speak phrases
    "low-hanging fruit",
    "touch base",
    "circle back",
    "moving forward",
    "at scale",
    "gain traction",
    "reach out",
    "results-driven",
    "detail-oriented",
    "proven track record",
    "strategic initiative",
    "drive measurable impact",
    "committed to excellence",
    "dedicated team player",
    "cross-functional collaboration",
)

# Build-time guarantee: KEEP_LIST and BANNED_WORDS never overlap.
_keep_lower = {w.lower() for w in KEEP_LIST}
_banned_lower = {w.lower() for w in BANNED_WORDS}
_overlap = _keep_lower & _banned_lower
if _overlap:
    raise RuntimeError(
        f"voice_rules.py: KEEP_LIST and BANNED_WORDS overlap: {sorted(_overlap)}"
    )

# ---------------------------------------------------------------------------
# Banned phrases — VOICE_PROFILE Section 19 (case-insensitive)
# ---------------------------------------------------------------------------
BANNED_PHRASES: tuple[str, ...] = (
    "It's worth noting that",
    "It is worth noting that",
    "It's important to remember",
    "It is important to remember",
    "Throughout my career, I have",
    "I am excited to explore opportunities",
    "I am writing to express my interest",
)

# ---------------------------------------------------------------------------
# Compiled regex patterns (compiled once at module import)
# ---------------------------------------------------------------------------
# Banned words: single case-insensitive alternation, word-boundary anchored.
# Sorted longest-first so multi-word phrases match before their substrings.
_words_sorted = sorted(BANNED_WORDS, key=len, reverse=True)
BANNED_WORDS_PATTERN: re.Pattern[str] = re.compile(
    r"\b(?:" + "|".join(re.escape(w) for w in _words_sorted) + r")\b",
    re.IGNORECASE,
)

# Banned phrases: single case-insensitive alternation.
BANNED_PHRASES_PATTERN: re.Pattern[str] = re.compile(
    "(?:" + "|".join(re.escape(p) for p in BANNED_PHRASES) + ")",
    re.IGNORECASE,
)

# Bold-first bullet pattern: "- **Word:** description" or "* **Word:** description"
BOLD_BULLET_PATTERN: re.Pattern[str] = re.compile(
    r"^[\s]*[-*]\s+\*\*[^*]+\*\*:\s",
    re.MULTILINE,
)

# Negation framing: "It's not X, it's Y"
NEGATION_PATTERN: re.Pattern[str] = re.compile(
    r"[Ii]t'?s not .{3,30}, it'?s",
    re.IGNORECASE,
)

# Bold-first bullet thresholds. CV documents legitimately use bold-first
# bullets in Core Competencies sections; non-CV docs should not.
BOLD_BULLET_THRESHOLD_CV: int = 20
BOLD_BULLET_THRESHOLD_DEFAULT: int = 3

# Frontmatter date: stdlib regex, NOT PyYAML.
FRONTMATTER_DATE_PATTERN: re.Pattern[str] = re.compile(
    r"^date:\s*(\d{4}-\d{2}-\d{2})\s*$",
    re.MULTILINE,
)


# ---------------------------------------------------------------------------
# Finding dataclass — used by all checkers
# ---------------------------------------------------------------------------
@dataclass(frozen=True, slots=True)
class Finding:
    file: str
    line: int
    type: str
    detail: str


__all__ = [
    "HOIBOY_CUTOFF_DATE",
    "MARKER_OPEN_HTML", "MARKER_CLOSE_HTML", "MARKER_EXEMPT_HTML",
    "MARKER_SKIP_OPEN_HTML", "MARKER_SKIP_CLOSE_HTML",
    "MARKER_OPEN_HASH", "MARKER_CLOSE_HASH", "MARKER_EXEMPT_HASH",
    "MARKER_SKIP_OPEN_HASH", "MARKER_SKIP_CLOSE_HASH",
    "EM_DASH", "SMART_QUOTE_CHARS", "UNICODE_ARROW_CHARS",
    "KEEP_LIST", "BANNED_WORDS", "BANNED_PHRASES",
    "BANNED_WORDS_PATTERN", "BANNED_PHRASES_PATTERN",
    "BOLD_BULLET_PATTERN", "NEGATION_PATTERN", "FRONTMATTER_DATE_PATTERN",
    "BOLD_BULLET_THRESHOLD_CV", "BOLD_BULLET_THRESHOLD_DEFAULT",
    "Finding",
]
