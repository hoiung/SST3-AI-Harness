#!/usr/bin/env bash
# feedback-aggregate-gate-486 fixture (#486).
# Regression gate for the commit-path strict/advisory split in
# leader-feedback-aggregate.sh. The every-commit pre-commit hook
# (`sst3-metrics-feedback-drift`) runs `--summarize`. Asserts:
#   A. clean in-scope corpus            -> --summarize exit 0
#   B. + a broken in-scope file         -> --summarize exit != 0  (AC5: hard
#                                          parse failure BLOCKS the commit;
#                                          this is the silent-rot regression
#                                          guard — pre-#486 --summarize was 0)
#   C. clean + a non-conforming-filename
#      file (not a telemetry file)      -> --summarize exit 0 + stderr WARNING
#                                          (AC7: a misfiled draft must NOT
#                                          wedge the gate / force --no-verify)
# Uses the SST3_FEEDBACK_DIR test seam so the real corpus is never touched.
# AC6 (advisory DRIFT never blocks) is proven on the real corpus in the
# Issue #486 Verification Loop; synthesising a 5-weighted-didnt DRIFT corpus
# here would be fixture overengineering for no extra signal.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
AGG="$REPO_ROOT/scripts/leader-feedback-aggregate.sh"
HERE="$(dirname "$0")"

run_summarize() {
    # echoes "<exit_code>" and writes stderr to $1
    local corpus="$1" errfile="$2" code
    set +e
    SST3_FEEDBACK_DIR="$corpus" bash "$AGG" --summarize >/dev/null 2>"$errfile"
    code=$?
    set -e
    echo "$code"
}

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

# --- Scenario A: clean in-scope corpus -> gate passes (exit 0) ---
A="$WORK/a"; mkdir -p "$A"
cp "$HERE/clean.md" "$A/feedback-test-1.md"
a_code=$(run_summarize "$A" "$WORK/a.err")
if [[ "$a_code" != "0" ]]; then
    echo "FAIL: scenario A (clean corpus) expected --summarize exit 0, got $a_code"
    cat "$WORK/a.err" >&2 || true
    exit 1
fi
echo "PASS: scenario A clean-corpus --summarize exit 0"

# --- Scenario B: + broken in-scope file -> gate BLOCKS (exit != 0) [AC5] ---
B="$WORK/b"; mkdir -p "$B"
cp "$HERE/clean.md"  "$B/feedback-test-1.md"
cp "$HERE/broken.md" "$B/feedback-test-2.md"
b_code=$(run_summarize "$B" "$WORK/b.err")
if [[ "$b_code" == "0" ]]; then
    echo "FAIL: scenario B (broken in-scope file present) expected --summarize exit != 0, got 0 — SILENT-ROT REGRESSION"
    cat "$WORK/b.err" >&2 || true
    exit 1
fi
echo "PASS: scenario B broken-in-scope --summarize exit $b_code (blocks, AC5)"

# --- Scenario C: clean + non-conforming filename -> exit 0 + WARNING [AC7] ---
C="$WORK/c"; mkdir -p "$C"
cp "$HERE/clean.md" "$C/feedback-test-1.md"
cp "$HERE/clean.md" "$C/feedback-misfiled-note.md"   # no -<N>.md => non-conforming
c_code=$(run_summarize "$C" "$WORK/c.err")
if [[ "$c_code" != "0" ]]; then
    echo "FAIL: scenario C (non-conforming filename) expected --summarize exit 0 (must not wedge), got $c_code"
    cat "$WORK/c.err" >&2 || true
    exit 1
fi
if ! grep -q 'WARNING non-conforming filename' "$WORK/c.err"; then
    echo "FAIL: scenario C expected a loud non-conforming WARNING on stderr; not found"
    cat "$WORK/c.err" >&2 || true
    exit 1
fi
echo "PASS: scenario C non-conforming-filename --summarize exit 0 + WARNING (AC7)"

echo "OK: feedback-aggregate-gate-486 fixture (3/3 assertions passed)"
