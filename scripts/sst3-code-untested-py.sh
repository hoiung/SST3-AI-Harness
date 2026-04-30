#!/usr/bin/env bash
# sst3-code-untested-py.sh — Zero-coverage Python function surface.
#
# Usage:   sst3-code-untested-py.sh
# Output:  NDJSON. On success: one object per file with untested defs:
#          {file, untested:[names]}.
#          On coverage-data error (cross-host paths, missing source):
#          {kind:"untested-py-error", reason:"<reason>", detail:"<msg>"}.
#          Always NDJSON — never raw stderr leaking through stdout.
# Engines: coverage json -o /tmp/cov.json; jq filter.
# Requires: coverage.py + a prior `coverage run` that produced .coverage data.
#          Missing tool or missing data → stderr contract + exit 127.
# Scope:   Python only. Rust + TS variants are deferred (Out of Scope, Phase A).
#
# #445 R4 Bug E: previously, when .coverage contained Windows-host paths
# (common on WSL setups where coverage was run on the Windows side via a
# Drive mount), `coverage json` printed "No source for code: ..." to STDOUT
# (not stderr) and the wrapper's `2>/dev/null` did not suppress it. The
# `|| true` on the jq pipe then masked the missing-file failure, so the
# upstream stdout error leaked as the wrapper's "NDJSON" output, breaking
# downstream jq consumers. Now: capture coverage exit + stderr, validate
# $COV_JSON exists before jq, emit structured NDJSON error record on
# failure.

set -euo pipefail
export LC_ALL=C

# shellcheck source=./sst3-bash-utils.sh
source "$(dirname "$0")/sst3-bash-utils.sh"

# --paths-from retrofit (#447 Phase 8): strip --paths-from from positional args
# and (if a filter NDJSON was supplied) install a transparent stdout filter
# via activate_paths_from_filter from sst3-bash-utils.sh.
__PATHS_FROM_SST3=""
__ARGS_SST3=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        --paths-from) __PATHS_FROM_SST3="${2:-}"; shift 2 || break;;
        *) __ARGS_SST3+=("$1"); shift;;
    esac
done
set -- "${__ARGS_SST3[@]+"${__ARGS_SST3[@]}"}"
activate_paths_from_filter "$__PATHS_FROM_SST3"

if ! command -v coverage >/dev/null 2>&1; then
    echo 'ERROR: coverage not installed; see dotfiles/docs/guides/code-query-playbook.md "Wrapper-Script Lane > Install"' >&2
    exit 127
fi

if [[ ! -f .coverage ]]; then
    # shellcheck disable=SC2016  # backticks inside single quotes are literal markdown, not command substitution
    echo 'ERROR: no .coverage data file; run `coverage run -m pytest` first; see dotfiles/docs/guides/code-query-playbook.md "Wrapper-Script Lane > Install"' >&2
    exit 127
fi

# #447 Phase 3 (Shape 7): fixed `/tmp/cov.json` raced when multiple shells
# invoked the wrapper concurrently. Default to mktemp; let SST3_COV_JSON
# override (used by tests + the deterministic-path Phase 4 self-test driver).
COV_JSON="${SST3_COV_JSON:-$(mktemp -t sst3_cov.XXXXXX.json)}"
trap 'rm -f "$COV_JSON"' EXIT

SST3_EMITTED_COUNT="${SST3_EMITTED_COUNT:-0}"
on_sigterm() {
    if command -v jq >/dev/null 2>&1; then
        jq -nc --arg n "sst3-code-untested-py" --argjson e "${SST3_EMITTED_COUNT:-0}" \
            '{kind:($n + "-killed"), reason:"sigterm", partial_records:$e}'
    else
        printf '{"kind":"%s-killed","reason":"sigterm","partial_records":%s}\n' \
            "sst3-code-untested-py" "${SST3_EMITTED_COUNT:-0}"
    fi
    exit 143
}
trap on_sigterm SIGTERM


# Capture coverage stdout+stderr separately. coverage.py prints
# "No source for code: ..." to STDOUT, not stderr.
set +e
COV_OUT=$(coverage json -o "$COV_JSON" -q --ignore-errors 2>&1)
COV_RC=$?
set -e

# Detect cross-host Windows paths (the common WSL failure mode).
if grep -qE 'No source for code.*[A-Z]:[\\/]' <<<"$COV_OUT"; then
    DETAIL=$(jq -Rs . <<<"$COV_OUT")
    printf '{"kind":"untested-py-error","reason":"coverage_data_cross_host","detail":%s}\n' "$DETAIL"
    exit 0
fi

if [[ $COV_RC -ne 0 ]] || [[ ! -s "$COV_JSON" ]]; then
    DETAIL=$(jq -Rs . <<<"$COV_OUT")
    printf '{"kind":"untested-py-error","reason":"coverage_failed","detail":%s}\n' "$DETAIL"
    exit 0
fi

# coverage json succeeded; emit untested-functions NDJSON.
jq -c '
    .files
    | to_entries[]
    | {
        file: .key,
        untested: [
            .value.functions
            | to_entries[]
            | select(.value.summary.percent_covered == 0)
            | .key
        ]
      }
    | select(.untested | length > 0)
' "$COV_JSON"
