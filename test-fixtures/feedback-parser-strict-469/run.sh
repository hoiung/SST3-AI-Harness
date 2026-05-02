#!/usr/bin/env bash
# feedback-parser-strict-469 fixture (#469 Phase 5).
# Regression gate for the strict-mode --emit-ndjson behaviour. Asserts:
#   1. feedback-test-1.md → exit 0 + N>0 NDJSON lines + NO schema_violation
#   2. feedback-test-2.md → exit 1 + 1 stub line + schema_violation:true
#   3. feedback-test-3.md → exit 1 + 1 stub line + schema_violation:true
#   4. feedback-test-4.md → exit 1 + 1 stub line + schema_violation:true
#   5. feedback-test-5.md → exit 1 + 1 stub line + schema_violation:true
# Catches drift if a future edit reverts strict-mode emit-ndjson back to
# lax parse_record() (the silent-skip codepath split that #469 closed).

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
PARSER="$REPO_ROOT/SST3/scripts/feedback_parser.py"
HERE="$(dirname "$0")"

assert_clean() {
    local file="$1"
    local out
    set +e
    out=$(python3 "$PARSER" "$file" --emit-ndjson --commit-sha test 2>/dev/null)
    local code=$?
    set -e
    if (( code != 0 )); then
        echo "FAIL: $(basename "$file") expected exit 0, got $code"
        exit 1
    fi
    local lines
    lines=$(printf '%s\n' "$out" | grep -c '^{' || true)
    if (( lines == 0 )); then
        echo "FAIL: $(basename "$file") expected N>0 NDJSON lines, got 0"
        exit 1
    fi
    if printf '%s' "$out" | grep -q '"schema_violation":[ ]*true'; then
        echo "FAIL: $(basename "$file") clean fixture unexpectedly emitted schema_violation:true"
        exit 1
    fi
    echo "PASS: $(basename "$file") (clean: $lines NDJSON lines)"
}

assert_broken() {
    local file="$1"
    local out
    set +e
    out=$(python3 "$PARSER" "$file" --emit-ndjson --commit-sha test 2>/dev/null)
    local code=$?
    set -e
    if (( code == 0 )); then
        echo "FAIL: $(basename "$file") expected exit 1, got 0 (silent-skip regression)"
        exit 1
    fi
    local lines
    lines=$(printf '%s\n' "$out" | grep -c '^{' || true)
    if (( lines != 1 )); then
        echo "FAIL: $(basename "$file") expected exactly 1 stub line, got $lines"
        exit 1
    fi
    if ! printf '%s' "$out" | grep -q '"schema_violation":[ ]*true'; then
        echo "FAIL: $(basename "$file") stub missing schema_violation:true"
        exit 1
    fi
    echo "PASS: $(basename "$file") (broken: stub emitted, exit $code)"
}

assert_clean   "$HERE/feedback-test-1.md"
assert_broken  "$HERE/feedback-test-2.md"
assert_broken  "$HERE/feedback-test-3.md"
assert_broken  "$HERE/feedback-test-4.md"
assert_broken  "$HERE/feedback-test-5.md"

echo "OK: feedback-parser-strict-469 fixture (5/5 assertions passed)"
