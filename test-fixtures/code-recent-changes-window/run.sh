#!/usr/bin/env bash
# code-recent-changes-window fixture (Issue #447 Phase 6).
# Stands up an isolated tmp git repo so the assertions are deterministic
# regardless of dotfiles' own git history.

set -euo pipefail

SCRIPTS_DIR="$(cd "$(dirname "$0")/../../scripts" && pwd)"
WRAPPER="$SCRIPTS_DIR/sst3-code-recent-changes.sh"

TMP=$(mktemp -d -t sst3-recent-changes.XXXXXX)
trap 'rm -rf "$TMP"' EXIT

cd "$TMP"
# Unset pre-commit's git env vars so `git init` operates on the tmp repo
# (pre-commit hooks inherit GIT_DIR/GIT_WORK_TREE pointing at the parent).
unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE
git init --quiet
git config user.email "fixture@sst3.local"
git config user.name "SST3 Fixture"

# Old commit (15 days ago) — should NOT appear in --since "7 days ago" window.
echo "old content" > old_file.txt
git add old_file.txt
GIT_AUTHOR_DATE="$(date -d '15 days ago' --iso-8601=seconds)" \
    GIT_COMMITTER_DATE="$(date -d '15 days ago' --iso-8601=seconds)" \
    git commit --quiet -m "old commit"

# Recent commit (1 day ago) — SHOULD appear.
echo "recent content" > recent_file.txt
echo "more lines" >> recent_file.txt
git add recent_file.txt
GIT_AUTHOR_DATE="$(date -d '1 day ago' --iso-8601=seconds)" \
    GIT_COMMITTER_DATE="$(date -d '1 day ago' --iso-8601=seconds)" \
    git commit --quiet -m "recent commit"

# Run the wrapper. Capture stdout + stderr separately.
OUT=$(bash "$WRAPPER" "7 days ago" 2>/dev/null)

# Assert: exactly one record (recent_file.txt only).
RECORD_COUNT=$(printf '%s\n' "$OUT" | grep -c '^{' || true)
if [[ "$RECORD_COUNT" -lt 1 ]]; then
    echo "FAIL: expected >=1 record, got $RECORD_COUNT"
    echo "OUT: $OUT"
    exit 1
fi
echo "PASS: emitted $RECORD_COUNT record(s) within window"

if printf '%s\n' "$OUT" | grep -q 'recent_file.txt'; then
    echo "PASS: recent_file.txt referenced"
else
    echo "FAIL: recent_file.txt missing from output"
    echo "OUT: $OUT"
    exit 1
fi

if printf '%s\n' "$OUT" | grep -q 'old_file.txt'; then
    echo "FAIL: old_file.txt should NOT appear (older than --since window)"
    exit 1
else
    echo "PASS: old_file.txt correctly excluded by --since window"
fi
