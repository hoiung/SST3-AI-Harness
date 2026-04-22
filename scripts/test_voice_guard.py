#!/usr/bin/env python3
"""
hoiboy-uk voice guard tests (5 focused cases).
Run: pytest scripts/test_voice_guard.py -q
Issue: hoiung/hoiboy-uk#3
"""

from __future__ import annotations

import importlib.util
import sys
from datetime import date
from pathlib import Path

import pytest

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

import voice_rules as vr  # noqa: E402

_spec = importlib.util.spec_from_file_location("cvt", HERE / "check_voice_tells.py")
cvt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cvt)


# Self-healing test samples. Pulled dynamically from the live lists so
# tests do not drift when BANNED_WORDS or KEEP_LIST are amended. Filtered
# to simple single-word entries (no hyphens, no spaces) so test strings
# can be built without regex-escape or phrase-match edge cases.
_SIMPLE_BANNED = [w for w in vr.BANNED_WORDS if "-" not in w and " " not in w]
_SIMPLE_KEEP = [w for w in vr.KEEP_LIST if "-" not in w and " " not in w]

# Hard fail if the lists ever run out of simple samples — the tests below
# need at least 2 banned samples and 1 keep sample.
assert len(_SIMPLE_BANNED) >= 2, (
    f"BANNED_WORDS needs ≥2 single-word entries for tests, found {len(_SIMPLE_BANNED)}"
)
assert len(_SIMPLE_KEEP) >= 1, (
    f"KEEP_LIST needs ≥1 single-word entry for tests, found {len(_SIMPLE_KEEP)}"
)

BANNED_SAMPLE = _SIMPLE_BANNED[0]
BANNED_SAMPLE_2 = _SIMPLE_BANNED[1]
KEEP_SAMPLE = _SIMPLE_KEEP[0]


# 1. extract_voice_regions hard fails (state machine, vendored)
class TestRegions:
    def test_happy_path(self):
        r = cvt.extract_voice_regions(
            "<!-- iamhoi -->\nA\n<!-- iamhoi-skip -->\ndelve\n<!-- iamhoi-skipend -->\nB\n<!-- iamhoiend -->"
        )
        assert r == [(2, "A"), (6, "B")]

    def test_unclosed(self):
        with pytest.raises(ValueError, match="unclosed"):
            cvt.extract_voice_regions("<!-- iamhoi -->\nfoo")

    def test_late_exempt(self):
        with pytest.raises(ValueError, match="first non-blank"):
            cvt.extract_voice_regions("hello\n<!-- iamhoi-exempt -->")


# 2. Frontmatter date parser
class TestParseDate:
    def test_valid(self, tmp_path):
        f = tmp_path / "post.md"
        f.write_text("---\ntitle: foo\ndate: 2026-04-08\n---\nbody\n", encoding="utf-8")
        assert cvt.parse_post_date(f) == date(2026, 4, 8)

    def test_no_frontmatter_returns_none(self, tmp_path):
        f = tmp_path / "x.md"
        f.write_text("just body\n", encoding="utf-8")
        assert cvt.parse_post_date(f) is None

    def test_unterminated_frontmatter_hard_fail(self, tmp_path):
        f = tmp_path / "x.md"
        f.write_text("---\ntitle: x\ndate: 2026-04-08\n", encoding="utf-8")
        with pytest.raises(ValueError, match="unterminated"):
            cvt.parse_post_date(f)

    def test_malformed_date_hard_fail(self, tmp_path):
        f = tmp_path / "x.md"
        f.write_text("---\ndate: 2026/04/08\n---\n", encoding="utf-8")
        with pytest.raises(ValueError, match="malformed"):
            cvt.parse_post_date(f)


# 3. Cutoff filter — legacy posts skipped
class TestCutoffFilter:
    def test_legacy_post_skipped(self, tmp_path):
        legacy = tmp_path / "old.md"
        legacy.write_text(
            "---\ndate: 2014-06-01\n---\nbody\n", encoding="utf-8"
        )
        d = cvt.parse_post_date(legacy)
        assert d == date(2014, 6, 1)
        assert d < vr.HOIBOY_CUTOFF_DATE

    def test_new_post_kept(self, tmp_path):
        new = tmp_path / "new.md"
        new.write_text(
            "---\ndate: 2026-05-01\n---\nbody\n", encoding="utf-8"
        )
        d = cvt.parse_post_date(new)
        assert d >= vr.HOIBOY_CUTOFF_DATE


# 4. Banned word boundary parity with canonical
class TestParityWithCanonical:
    def test_banned_sample_matches_with_word_boundary(self):
        # Exact banned word matches.
        assert vr.BANNED_WORDS_PATTERN.search(BANNED_SAMPLE)
        # Same banned word with letters appended does NOT match — `\b` boundary.
        # Suffix "xxyy" chosen because it cannot form any other banned word.
        assert not vr.BANNED_WORDS_PATTERN.search(f"{BANNED_SAMPLE}xxyy")

    def test_keep_sample_not_matched(self):
        # KEEP_LIST words must never be matched by the BANNED_WORDS regex.
        # This is the lens-facing half of the overlap invariant (see
        # test_no_banned_keep_overlap for the set-theoretic half).
        assert not vr.BANNED_WORDS_PATTERN.search(KEEP_SAMPLE)

    def test_no_banned_keep_overlap(self):
        # Explicit pytest of the overlap invariant that voice_rules.py
        # enforces at import time. Duplicating it here makes the invariant
        # a discoverable, named test rather than a module-load crash that
        # readers might not know exists. Future regressions fail here with
        # a readable diagnostic instead of a cryptic import error.
        banned = {w.lower() for w in vr.BANNED_WORDS}
        keep = {w.lower() for w in vr.KEEP_LIST}
        overlap = banned & keep
        assert not overlap, (
            f"BANNED_WORDS and KEEP_LIST overlap on: {sorted(overlap)}. "
            "A word cannot be both banned and whitelisted."
        )

    def test_cutoff_constant(self):
        assert vr.HOIBOY_CUTOFF_DATE == date(2026, 4, 7)


# 5. Decision matrix - default skip
class TestDecisionMatrix:
    def test_default_skip(self, tmp_path):
        f = tmp_path / "anything.md"
        # Two live banned-word samples. Default behaviour without iamhoi
        # markers is SKIP, so scan_file returns an empty list even when
        # the content is full of banned words.
        f.write_text(
            f"{BANNED_SAMPLE} and {BANNED_SAMPLE_2} everywhere\n",
            encoding="utf-8",
        )
        assert cvt.scan_file(f, tmp_path) == []

    def test_marker_scans_only_tagged(self, tmp_path):
        f = tmp_path / "x.md"
        # Content structure: outside-markers → inside-markers → outside-markers.
        # Only the region between <!-- iamhoi --> and <!-- iamhoiend --> should
        # be scanned, so only BANNED_SAMPLE_2 (inside) triggers a finding.
        f.write_text(
            f"{BANNED_SAMPLE} outside\n"
            "<!-- iamhoi -->\n"
            f"{BANNED_SAMPLE_2} inside\n"
            "<!-- iamhoiend -->\n"
            f"{BANNED_SAMPLE} after\n",
            encoding="utf-8",
        )
        findings = cvt.scan_file(f, tmp_path)
        assert len(findings) == 1
        assert BANNED_SAMPLE_2 in findings[0].detail
