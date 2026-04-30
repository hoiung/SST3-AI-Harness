#!/usr/bin/env bash
# code-at-ref-historical fixture (Issue #447 Phase 6).
# Stands up an isolated tmp git repo with two commits, runs sst3-code-at-ref.sh
# against HEAD~1, asserts the output is tagged with the ref.

set -euo pipefail

SCRIPTS_DIR="$(cd "$(dirname "$0")/../../scripts" && pwd)"
WRAPPER="$SCRIPTS_DIR/sst3-code-at-ref.sh"
INNER="sst3-code-shell.sh"

TMP=$(mktemp -d -t sst3-at-ref.XXXXXX)
trap 'rm -rf "$TMP"' EXIT

cd "$TMP"
# Unset pre-commit's git env vars so `git init` operates on the tmp repo
# (pre-commit hooks inherit GIT_DIR/GIT_WORK_TREE pointing at the parent).
unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE
git init --quiet
git config user.email "fixture@sst3.local"
git config user.name "SST3 Fixture"

# HEAD~1: one function only.
mkdir -p sub
cat > sub/early.sh <<'EOF'
#!/usr/bin/env bash
early_func() {
    echo "early"
}
EOF
git add sub/early.sh
git commit --quiet -m "early"

# HEAD: add a second function file (NOT present at HEAD~1).
cat > sub/late.sh <<'EOF'
#!/usr/bin/env bash
late_func() {
    echo "late"
}
EOF
git add sub/late.sh
git commit --quiet -m "late"

# Run wrapper at HEAD~1 against the inner --struct mode on sub/.
OUT=$(bash "$WRAPPER" "HEAD~1" "$INNER" --struct sub/ 2>/dev/null || true)

# Assert: every JSON record is tagged with ref:HEAD~1.
TOTAL=$(printf '%s\n' "$OUT" | grep -c '^{' || true)
TAGGED=$(printf '%s\n' "$OUT" | grep -c '"ref":"HEAD~1"' || true)
if [[ "$TOTAL" -lt 1 ]]; then
    echo "FAIL: expected >=1 record, got $TOTAL"
    echo "OUT: $OUT"
    exit 1
fi
echo "PASS: emitted $TOTAL record(s) tagged with ref"

if [[ "$TOTAL" != "$TAGGED" ]]; then
    echo "FAIL: expected all $TOTAL records to carry ref tag, got $TAGGED"
    exit 1
fi
echo "PASS: all records carry ref:HEAD~1"

# Assert: late_func should NOT appear at HEAD~1.
if printf '%s\n' "$OUT" | grep -q 'late_func'; then
    echo "FAIL: late_func should not appear at HEAD~1 (added in HEAD)"
    exit 1
else
    echo "PASS: late_func correctly absent at HEAD~1"
fi

# Assert: early_func SHOULD appear.
if printf '%s\n' "$OUT" | grep -q 'early_func'; then
    echo "PASS: early_func present at HEAD~1"
else
    echo "FAIL: early_func missing from HEAD~1 output"
    exit 1
fi
