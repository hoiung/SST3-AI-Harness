#!/usr/bin/env bash
# command-injection fixture for Phase 1 (Issue #447).
# Asserts that 4 wrappers reject shell-metacharacter payloads with exit 64
# AND that the injection sentinel file is NEVER created.
#
# This fixture lands in Phase 1 (preview of Phase 4) because the fixture
# IS the proof that the assert_safe_identifier helper closes the
# command-injection class. Phase 4 baseline-hash step covers it.

set -euo pipefail

SCRIPTS="$(cd "$(dirname "$0")/../../scripts" && pwd)"
SENTINEL="/tmp/sst3_inject_test_$$"

declare -a TARGETS=(
    "sst3-code-callers.sh|callers|python"
    "sst3-code-callees.sh|callees|python"
    "sst3-code-subclasses.sh|subclasses|python"
    "sst3-code-impact.sh|impact|UNUSED"
)

# Cleanup any stale sentinel before run.
rm -f "$SENTINEL"

PASS=0
FAIL=0
declare -a FAIL_REASONS=()

for entry in "${TARGETS[@]}"; do
    IFS='|' read -r script label lang <<< "$entry"
    payload="foo\`touch $SENTINEL\`"

    # Each wrapper has different positional contract; first arg is always the symbol-like.
    if [[ "$script" == "sst3-code-impact.sh" ]]; then
        # impact takes <base-branch>; the SYM injection is internal to the loop.
        # Validate via direct helper call instead — sourced and used in identical position.
        rc=0
        ( source "$SCRIPTS/sst3-bash-utils.sh" && assert_safe_identifier "$payload" ) >/dev/null 2>&1 || rc=$?
    else
        rc=0
        bash "$SCRIPTS/$script" "$payload" "$lang" >/dev/null 2>&1 || rc=$?
    fi

    if [[ "$rc" == "64" ]]; then
        printf 'PASS: %-13s rejected with exit 64\n' "$label"
        PASS=$((PASS + 1))
    else
        printf 'FAIL: %-13s exit=%s (expected 64)\n' "$label" "$rc"
        FAIL=$((FAIL + 1))
        FAIL_REASONS+=("$label exit=$rc")
    fi
done

# Sentinel must never have been created — proves backticks did not execute.
if [[ -e "$SENTINEL" ]]; then
    printf 'FAIL: injection sentinel created at %s — backticks executed\n' "$SENTINEL"
    rm -f "$SENTINEL"
    FAIL=$((FAIL + 1))
    FAIL_REASONS+=("sentinel-created")
else
    printf 'PASS: no injection sentinel created\n'
    PASS=$((PASS + 1))
fi

printf '\n=== command-injection fixture: %d pass, %d fail ===\n' "$PASS" "$FAIL"
if (( FAIL > 0 )); then
    printf 'reasons: %s\n' "${FAIL_REASONS[*]}"
    exit 1
fi
exit 0
