#!/usr/bin/env python3
"""
Word-count ceiling guard for hoiboy.uk new posts.

Blocks commit / fails CI if a new post (date >= HOIBOY_CUTOFF_DATE) exceeds
WORDCOUNT_CEILING words after markup stripping. Legacy posts
(date < HOIBOY_CUTOFF_DATE) are silently skipped (voice-sacred corpus,
e.g. woodsmoke-bushcraft-course at 11,858 words).

Ceiling set from 14_BLOG_CRAFT.md line 17 rule: drafts >3000 words must be
split or cut back. Negative example on file: sst3-ai-harness-reshapeable-knife
(5,143 words, 15 Apr 2026). Exactly 3000 passes; strictly greater fails.

Strip sequence is deliberate: Hugo shortcodes, iamhoi markers, code blocks,
and URLs inflate naive wc counts on long technical posts. Counting only the
prose readers actually read is the point of the ceiling.

Issue: hoiung/hoiboy-uk#10
Exit codes: 0 = pass (silent), 1 = fail (block commit / fail CI)
"""

from __future__ import annotations

import re
import sys
from datetime import date, datetime
from pathlib import Path

import yaml

from voice_rules import HOIBOY_CUTOFF_DATE

WORDCOUNT_CEILING: int = 3000

# Grandfathered posts: already published before this hook existed.
# Intentionally NOT a frontmatter opt-out. Any future addition requires
# a code review. The live negative example referenced in
# docs/research/14_BLOG_CRAFT.md line 17 is sst3-ai-harness-reshapeable-knife.
# Grandfather list captures the full set of pre-hook sprawl cases so CI
# on main stays green; future drafts (date >= 2026-04-07) without a slug
# here must stay <= WORDCOUNT_CEILING.
GRANDFATHERED_SLUGS: frozenset[str] = frozenset({
    "sst3-ai-harness-reshapeable-knife",
    "every-book-ive-read-in-20-years",
    "scaling-without-quality",
})

_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_FENCED_CODE_RE = re.compile(r"```.*?```", re.DOTALL)
_INLINE_CODE_RE = re.compile(r"`[^`]*`")
_SHORTCODE_ANGLE_RE = re.compile(r"\{\{<.*?>\}\}", re.DOTALL)
_SHORTCODE_PERCENT_RE = re.compile(r"\{\{%.*?%\}\}", re.DOTALL)
_REF_LINK_DEF_RE = re.compile(r"^\s*\[[^\]]+\]:\s+\S+\s*$", re.MULTILINE)
_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\([^)]+\)")
_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_WORD_RE = re.compile(r"\w+")


def strip_markup(text: str) -> str:
    """Apply the 9-step strip sequence before tokenisation."""
    text = _FRONTMATTER_RE.sub("", text, count=1)
    text = _HTML_COMMENT_RE.sub("", text)
    text = _FENCED_CODE_RE.sub("", text)
    text = _INLINE_CODE_RE.sub("", text)
    text = _SHORTCODE_ANGLE_RE.sub("", text)
    text = _SHORTCODE_PERCENT_RE.sub("", text)
    text = _REF_LINK_DEF_RE.sub("", text)
    text = _IMAGE_RE.sub(r"\1", text)
    text = _LINK_RE.sub(r"\1", text)
    text = _HTML_TAG_RE.sub("", text)
    return text


def count_words(markdown: str) -> int:
    stripped = strip_markup(markdown)
    return len(_WORD_RE.findall(stripped))


def parse_post_date(text: str, path: Path) -> date:
    """
    Parse the frontmatter `date:` field via PyYAML.
    Fails loudly on malformed frontmatter, missing date, or bad date type.
    """
    match = _FRONTMATTER_RE.match(text)
    if match is None:
        raise ValueError(f"Invalid frontmatter in {path}: no YAML block found")
    try:
        data = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid frontmatter in {path}: {exc}") from exc
    if not isinstance(data, dict) or "date" not in data:
        raise ValueError(f"Missing 'date' field in frontmatter: {path}")
    raw = data["date"]
    # datetime is a subclass of date; coerce first so timestamp strings
    # like `date: 2026-04-21T09:00:00Z` do not crash the later cmp.
    if isinstance(raw, datetime):
        return raw.date()
    if isinstance(raw, date):
        return raw
    if isinstance(raw, str):
        try:
            return date.fromisoformat(raw)
        except ValueError as exc:
            raise ValueError(
                f"Invalid 'date' value in frontmatter ({path}): {raw!r}: {exc}"
            ) from exc
    raise ValueError(
        f"Invalid 'date' type in frontmatter ({path}): expected date or YYYY-MM-DD string, got {type(raw).__name__}"
    )


def check_file(path: Path) -> int:
    if not path.exists():
        print(f"ERROR: File not found: {path}", file=sys.stderr)
        return 1
    try:
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        print(f"ERROR: Encoding error in {path}: {exc}", file=sys.stderr)
        return 1

    try:
        post_date = parse_post_date(text, path)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if post_date < HOIBOY_CUTOFF_DATE:
        return 0

    if path.parent.name in GRANDFATHERED_SLUGS:
        return 0

    words = count_words(text)
    if words <= WORDCOUNT_CEILING:
        return 0

    excess = words - WORDCOUNT_CEILING
    print(
        f"ERROR: {path} exceeds word-count ceiling\n"
        f"  Current: {words} words\n"
        f"  Ceiling: {WORDCOUNT_CEILING} words\n"
        f"  Excess: {excess} words\n"
        f"  Remediation: trim the draft or split into two posts. "
        f"See docs/research/14_BLOG_CRAFT.md line 17.",
        file=sys.stderr,
    )
    return 1


def main(argv: list[str]) -> int:
    if not argv:
        return 0
    rc = 0
    for arg in argv:
        rc |= check_file(Path(arg))
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
