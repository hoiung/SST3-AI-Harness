#!/usr/bin/env python3
"""
Voice guard unit tests (5 focused cases).

Run: pytest SST3/scripts/test_voice_guard.py -q
Issue: hoiung/dotfiles#404
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

_spec = importlib.util.spec_from_file_location(
    "cawt", HERE / "check-ai-writing-tells.py"
)
cawt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cawt)


# ---------------------------------------------------------------------------
# Test 1: extract_voice_regions — happy path + 5 hard fails
# ---------------------------------------------------------------------------
class TestExtractVoiceRegions:
    def test_happy_path_with_skip(self):
        text = (
            "<!-- iamhoi -->\n"
            "voice line A\n"
            "<!-- iamhoi-skip -->\n"
            "delve hidden\n"
            "<!-- iamhoi-skipend -->\n"
            "voice line B\n"
            "<!-- iamhoiend -->\n"
        )
        regions = cawt.extract_voice_regions(text)
        assert regions == [(2, "voice line A"), (6, "voice line B")]

    def test_no_markers_returns_empty(self):
        assert cawt.extract_voice_regions("plain text\nno markers") == []

    def test_exempt_first_line(self):
        assert cawt.extract_voice_regions(
            "<!-- iamhoi-exempt -->\nrest of file"
        ) == []

    def test_unclosed_marker_hard_fail(self):
        with pytest.raises(ValueError, match="unclosed"):
            cawt.extract_voice_regions("<!-- iamhoi -->\noops")

    def test_nested_marker_hard_fail(self):
        with pytest.raises(ValueError, match="nested"):
            cawt.extract_voice_regions(
                "<!-- iamhoi -->\n<!-- iamhoi -->\n<!-- iamhoiend -->"
            )

    def test_orphan_skip_hard_fail(self):
        with pytest.raises(ValueError, match="orphan"):
            cawt.extract_voice_regions(
                "<!-- iamhoi-skip -->\nfoo\n<!-- iamhoi-skipend -->"
            )

    def test_late_exempt_hard_fail(self):
        with pytest.raises(ValueError, match="first non-blank"):
            cawt.extract_voice_regions("hello\n<!-- iamhoi-exempt -->")

    def test_multiple_exempt_hard_fail(self):
        with pytest.raises(ValueError, match="multiple"):
            cawt.extract_voice_regions(
                "<!-- iamhoi-exempt -->\n<!-- iamhoi-exempt -->"
            )

    def test_mixed_syntax_hard_fail(self):
        with pytest.raises(ValueError, match="mixed"):
            cawt.extract_voice_regions(
                "<!-- iamhoi -->\n# iamhoi\n<!-- iamhoiend -->"
            )

    def test_hash_alias_works(self):
        regions = cawt.extract_voice_regions(
            "# iamhoi\nline one\nline two\n# iamhoiend\n"
        )
        assert regions == [(2, "line one"), (3, "line two")]


# ---------------------------------------------------------------------------
# Test 2: check_phrases — case-insensitive, boundary-aware
# ---------------------------------------------------------------------------
class TestPhrases:
    def test_case_insensitive(self):
        assert vr.BANNED_PHRASES_PATTERN.search("IT'S WORTH NOTING THAT")
        assert vr.BANNED_PHRASES_PATTERN.search("It's worth noting that")
        assert vr.BANNED_PHRASES_PATTERN.search("it's worth noting that the sky")

    def test_no_match_unrelated(self):
        assert not vr.BANNED_PHRASES_PATTERN.search("nothing matches here")


# ---------------------------------------------------------------------------
# Test 3: banned word boundary cases
# ---------------------------------------------------------------------------
class TestWordBoundary:
    def test_deliverable_matches(self):
        assert vr.BANNED_WORDS_PATTERN.search("a key deliverable today")

    def test_deliver_does_not_match(self):
        assert not vr.BANNED_WORDS_PATTERN.search("we deliver value")

    def test_leveraged_matches(self):
        assert vr.BANNED_WORDS_PATTERN.search("I leveraged the team")

    def test_leverage_matches(self):
        assert vr.BANNED_WORDS_PATTERN.search("leverage the budget")

    def test_keep_list_words_not_in_banned(self):
        for w in vr.KEEP_LIST:
            assert w.lower() not in {b.lower() for b in vr.BANNED_WORDS}


# ---------------------------------------------------------------------------
# Test 4: file selection decision matrix (all 4 rows)
# ---------------------------------------------------------------------------
class TestDecisionMatrix:
    def _scan(self, tmp_path: Path, name: str, content: str) -> list:
        f = tmp_path / name
        f.write_text(content, encoding="utf-8")
        return cawt.scan_file(f, tmp_path)

    def test_row1_exempt_first_line_skips(self, tmp_path):
        findings = self._scan(
            tmp_path, "any.md",
            "<!-- iamhoi-exempt -->\nthis has delve\n",
        )
        assert findings == []

    def test_row2_markers_scan_only_tagged(self, tmp_path):
        findings = self._scan(
            tmp_path, "any.md",
            "delve outside\n"
            "<!-- iamhoi -->\nleverage inside\n<!-- iamhoiend -->\n"
            "synergy after\n",
        )
        # Only "leverage inside" is scanned.
        assert len(findings) == 1
        assert findings[0].line == 3
        assert "leverage" in findings[0].detail

    def test_row3_legacy_whitelist_whole_file(self, tmp_path, monkeypatch):
        # Simulate whitelisted file by patching the tuple at module level.
        monkeypatch.setattr(cawt, "PUBLIC_FACING_GLOBS", ("legacy.md",))
        findings = self._scan(
            tmp_path, "legacy.md", "delve everywhere\n"
        )
        assert any("delve" in f.detail for f in findings)

    def test_row4_default_skip(self, tmp_path):
        findings = self._scan(
            tmp_path, "random.md", "delve and leverage everywhere\n"
        )
        assert findings == []


# ---------------------------------------------------------------------------
# Test 5: cutoff date frontmatter regex parser
# ---------------------------------------------------------------------------
class TestFrontmatterDate:
    def test_valid_date(self):
        m = vr.FRONTMATTER_DATE_PATTERN.search(
            "---\ntitle: foo\ndate: 2026-04-08\n---\n"
        )
        assert m
        assert date.fromisoformat(m.group(1)) == date(2026, 4, 8)

    def test_missing_date_returns_none(self):
        assert vr.FRONTMATTER_DATE_PATTERN.search("---\ntitle: foo\n---\n") is None

    def test_malformed_date_no_match(self):
        assert vr.FRONTMATTER_DATE_PATTERN.search("date: 2026/04/08") is None

    def test_cutoff_constant(self):
        assert vr.HOIBOY_CUTOFF_DATE == date(2026, 4, 7)
