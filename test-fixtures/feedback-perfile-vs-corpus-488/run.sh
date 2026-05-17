#!/usr/bin/env bash
# feedback-perfile-vs-corpus-488 fixture (dotfiles#488 AC 3.2 concrete
# 4-step proof + AC 5.3(b)).
#
# Proves the Fix-C per-file commit hook does NOT regress the dotfiles#486
# silent-rot invariant, because the retained whole-corpus CI catch
# (AC 3.2(i-a) `leader-feedback-aggregate.sh --summarize`, non-swallowed)
# still fires on a file broken in an EARLIER commit. The 4 steps (exit
# codes recorded inline per the AC):
#   (1) a VALID feedback file parses clean                  -> exit 0
#   (2) a LATER commit corrupts an UNRELATED EARLIER file's
#       heading to bare `## Stage 1` (the #486/#488 halt class)
#   (3) the whole-corpus --summarize over the corrupted
#       corpus exits NON-ZERO  (short-circuits did NOT mask
#       it: --summarize forces regenerate_index --rebuild)   -> exit != 0
#   (4) a PER-FILE run scoped to ONLY commit (2)'s own file
#       PASSES (this is the gap the whole-corpus catch closes:
#       the rewired per-file commit hook correctly lets
#       commit (2) through — its own file is fine)           -> exit 0
# Uses the SST3_FEEDBACK_DIR test seam so the real corpus is untouched.
# Exit 0 = governance invariant preserved; exit 1 = regression.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
PARSER="$REPO_ROOT/scripts/feedback_parser.py"
AGG="$REPO_ROOT/scripts/leader-feedback-aggregate.sh"
HERE="$(dirname "$0")"

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
CORPUS="$WORK/corpus"; mkdir -p "$CORPUS"

rc() { set +e; "$@" >/dev/null 2>&1; echo $?; set -e; }

# --- step (1): a VALID earlier feedback file (filename<->FM parity) ---
cp "$HERE/valid.md" "$CORPUS/feedback-test-1.md"               # repo=test issue=1
c1=$(rc python3 "$PARSER" "$CORPUS/feedback-test-1.md")
if [[ "$c1" != "0" ]]; then
    echo "FAIL: step (1) expected VALID earlier file parse exit 0, got $c1"
    exit 1
fi
echo "PASS: step (1) valid earlier feedback file parses exit 0 [c1=$c1]"

# --- step (2): LATER commit adds its own VALID file, corrupts the
#               UNRELATED EARLIER file's heading to bare `## Stage 1` ---
sed 's/^issue: 1$/issue: 2/' "$HERE/valid.md" > "$CORPUS/feedback-test-2.md"  # repo=test issue=2
sed -i '0,/^## Stage 1/s/^## Stage 1.*/## Stage 1/' "$CORPUS/feedback-test-1.md"
if ! grep -qx '## Stage 1' "$CORPUS/feedback-test-1.md"; then
    echo "FAIL: step (2) bare-heading corruption was not applied to the earlier file"
    exit 1
fi
echo "PASS: step (2) later commit owns feedback-test-2.md; earlier feedback-test-1.md heading corrupted to bare '## Stage 1' [applied]"

# --- step (3): whole-corpus --summarize MUST exit non-zero (the
#               retained #486 catch — short-circuits did not mask it) ---
c3=$(rc env SST3_FEEDBACK_DIR="$CORPUS" bash "$AGG" --summarize)
if [[ "$c3" == "0" ]]; then
    echo "FAIL: step (3) whole-corpus --summarize expected exit != 0 (corrupted EARLIER file), got 0 — #486 SILENT-ROT REGRESSION"
    exit 1
fi
echo "PASS: step (3) whole-corpus --summarize exit $c3 (!=0 — earlier-commit breakage caught, #486 invariant retained) [c3=$c3]"

# --- step (4): per-file run scoped to ONLY commit (2)'s own file
#               PASSES (the gap the whole-corpus catch closes) ---
c4=$(rc python3 "$PARSER" "$CORPUS/feedback-test-2.md")
if [[ "$c4" != "0" ]]; then
    echo "FAIL: step (4) per-file validate of commit (2)'s own file expected exit 0, got $c4"
    exit 1
fi
echo "PASS: step (4) per-file validate scoped to commit (2)'s own file exit 0 (commit (2) correctly unblocked) [c4=$c4]"

echo "RECORDED EXIT CODES: c1=$c1 step2=applied c3=$c3 c4=$c4"
echo "OK: feedback-perfile-vs-corpus-488 fixture (4/4 assertions passed)"
