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
    def test_facilitate_vs_face(self):
        # Uses `facilitate` (still banned) now that `deliverable` was
        # whitelisted 2026-04-22 per memory/feedback_if_i_type_it_i_use_it.md.
        # Same principle: word-boundary match on banned form, not partial.
        assert vr.BANNED_WORDS_PATTERN.search("facilitate")
        assert not vr.BANNED_WORDS_PATTERN.search("we face the problem")

    def test_cutoff_constant(self):
        assert vr.HOIBOY_CUTOFF_DATE == date(2026, 4, 7)


# 5. Decision matrix - default skip
class TestDecisionMatrix:
    def test_default_skip(self, tmp_path):
        f = tmp_path / "anything.md"
        # Uses `delve` + `facilitate` — both still banned. `leverage` was
        # whitelisted 2026-04-22 so it no longer proves a default-skip case.
        f.write_text("delve and facilitate everywhere\n", encoding="utf-8")
        assert cvt.scan_file(f, tmp_path) == []

    def test_marker_scans_only_tagged(self, tmp_path):
        f = tmp_path / "x.md"
        # Body inside iamhoi markers contains `facilitate` (still banned);
        # outside markers contains `delve` + `seamless` (ignored by default
        # SKIP). Swapped from `leverage`/`synergy` which are now whitelisted.
        f.write_text(
            "delve outside\n<!-- iamhoi -->\nfacilitate inside\n<!-- iamhoiend -->\nseamless after\n",
            encoding="utf-8",
        )
        findings = cvt.scan_file(f, tmp_path)
        assert len(findings) == 1
        assert "facilitate" in findings[0].detail
