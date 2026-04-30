#!/usr/bin/env bash
# sst3-self-test.sh — Wrapper-lane regression gate (#447 Phase 4).
#
# Usage:   sst3-self-test.sh [--only <fixture-name>] [--strict-engines]
# Output:  STDOUT — NDJSON, one record per fixture: {kind, fixture, drift?, ...}
#          plus terminating {kind:"self-test-complete", total, passed, failed, drift:[...]}
#          STDERR — single sentinel: "sst3-self-test: ran <total> fixture(s), <failed> drifted, <wrapper_drift> wrapper drift"
# Engine:  python3. Exit 127 + stderr contract on missing engine.
# Exit:    0 all pass / 1 any drifted / 2 driver crash / 64 bad args / 127 engine missing
#
# This wrapper is invoked by:
#   - Pre-commit hook `sst3-self-test` on every scripts/sst3-*.sh edit
#   - CI step "SST3 wrapper integrity self-test (BLOCKING)" in validate.yml
#   - /Leader Stage 1 entry (Phase 5 edit)
#
# It is the fail-fast gate that prevents wrapper-lane drift from reaching
# production, and the meta-validation step in CI proves that fixtures
# actually catch the bugs we shipped in Phases 1-3 (see _known-broken-wrappers/).

set -euo pipefail

# Expose dev-host engines installed via cargo / pipx / npm-global to the
# pre-commit-hook environment. pre-commit's minimal PATH excludes ~/.cargo/bin,
# ~/.local/bin, and ~/.npm-global/bin by default, which makes ast-grep (npm
# or cargo install), pip-audit (pipx), markdownlint-cli2 (npm) invisible to
# wrappers run by the hook even though they are present on the dev host.
# (#447 Phase 8 fix; #454 added ~/.npm-global/bin so npm-install ast-grep on
# a fresh dotfiles/scripts/install.sh bootstrap is reachable.) CI runners
# install engines under /usr/local/bin which is already on PATH; this is
# purely a dev-host pre-commit fallback.
for extra in "$HOME/.cargo/bin" "$HOME/.local/bin" "$HOME/.npm-global/bin" "/usr/local/bin"; do
    case ":$PATH:" in
        *":$extra:"*) ;;
        *) [[ -d "$extra" ]] && PATH="$extra:$PATH" ;;
    esac
done
export PATH

if ! command -v python3 >/dev/null 2>&1; then
    echo 'ERROR: python3 not installed; see dotfiles/docs/guides/code-query-playbook.md "Wrapper-Script Lane > Install"' >&2
    exit 127
fi

# Locate driver — colocated with this script.
DRIVER="$(dirname "$0")/_self_test_driver.py"
if [[ ! -f "$DRIVER" ]]; then
    echo "ERROR: driver missing at $DRIVER" >&2
    exit 2
fi

# Capture driver output to compute the stderr sentinel after-the-fact.
# Use a temp file so we don't lose the NDJSON stream on driver crash.
TMP_OUT=$(mktemp -t sst3_self_test.XXXXXX.ndjson)
trap 'rm -f "$TMP_OUT"' EXIT

set +e
python3 "$DRIVER" "$@" | tee "$TMP_OUT"
DRIVER_EXIT=${PIPESTATUS[0]}
set -e

# Parse the terminating sentinel for the stderr summary line.
SUMMARY=$(grep '"kind":"self-test-complete"' "$TMP_OUT" | tail -1 || true)
if [[ -n "$SUMMARY" ]]; then
    TOTAL=$(echo "$SUMMARY" | python3 -c 'import sys,json; print(json.loads(sys.stdin.read()).get("total",0))')
    FAILED=$(echo "$SUMMARY" | python3 -c 'import sys,json; print(json.loads(sys.stdin.read()).get("failed",0))')
    WDRIFT=$(echo "$SUMMARY" | python3 -c 'import sys,json; print(json.loads(sys.stdin.read()).get("wrapper_drift_count",0))')
    echo "sst3-self-test: ran $TOTAL fixture(s), $FAILED drifted, $WDRIFT wrapper drift" >&2
else
    echo "sst3-self-test: driver exited without sentinel (crash class)" >&2
fi

exit "$DRIVER_EXIT"
