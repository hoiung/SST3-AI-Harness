#!/usr/bin/env bash
# sst3-doc-links.sh — Outbound link liveness check (lychee wrapper).
#
# Usage:   sst3-doc-links.sh [--strict] [paths...]
# Default: checks SST3/**/*.md + docs/**/*.md + CLAUDE.md + README.md
# Output:  STDOUT — NDJSON, one object per failed link: {file, url, status, error}
#          STDERR — always emits a "scan complete" sentinel:
#                   "sst3-doc-links: scanned <N> path(s), <M> broken link(s)"
#          The stderr sentinel lets consumers distinguish "all clean" (exit 0,
#          empty stdout, sentinel present) from "didn't run" (no sentinel).
# Engine:  lychee. Exit 127 + stderr contract on missing engine.
# Exit:    0 = clean, 1 = --strict + broken found, 2 = lychee crashed.
# Note:    --strict: exit 1 if any failed link is found (for pre-commit gating).
#          #445 R4 fix: jq filter was reading `.fail_map` but lychee emits
#          `.error_map` — silent-zero on every broken link. Now reads correct key.

set -euo pipefail
export LC_ALL=C


SST3_EMITTED_COUNT="${SST3_EMITTED_COUNT:-0}"
on_sigterm() {
    if command -v jq >/dev/null 2>&1; then
        jq -nc --arg n "sst3-doc-links" --argjson e "${SST3_EMITTED_COUNT:-0}" \
            '{kind:($n + "-killed"), reason:"sigterm", partial_records:$e}'
    else
        printf '{"kind":"%s-killed","reason":"sigterm","partial_records":%s}\n' \
            "sst3-doc-links" "${SST3_EMITTED_COUNT:-0}"
    fi
    exit 143
}
trap on_sigterm SIGTERM

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

if ! command -v lychee >/dev/null 2>&1; then
    echo 'ERROR: lychee not installed; see dotfiles/docs/guides/code-query-playbook.md "Wrapper-Script Lane > Install"' >&2
    exit 127
fi

# #447 Phase 3: standardise arg parsing on the canonical case-loop pattern.
STRICT=0
ARGS=()
for arg in "$@"; do
    case "$arg" in
        --strict) STRICT=1 ;;
        *) ARGS+=("$arg") ;;
    esac
done
set -- "${ARGS[@]}"

if [[ $# -eq 0 ]]; then
    DEFAULT_PATHS=('SST3/' 'docs/' 'CLAUDE.md' 'README.md')
    PATHS=()
    for p in "${DEFAULT_PATHS[@]}"; do
        [[ -e "$p" ]] && PATHS+=("$p")
    done
    if [[ ${#PATHS[@]} -eq 0 ]]; then
        echo "sst3-doc-links: no default paths exist (SST3/ docs/ CLAUDE.md README.md); pass paths explicitly" >&2
        exit 0
    fi
else
    PATHS=("$@")
fi

# lychee --format json emits one JSON object summarising all checks.
# Capture exit code separately: 0 = clean, 2 = errors found, other = crash.
set +e
RAW=$(lychee --format json --no-progress --max-concurrency 4 "${PATHS[@]}" 2>/tmp/sst3-lychee.err.$$)
LYCHEE_EXIT=$?
set -e

if [[ $LYCHEE_EXIT -ne 0 && $LYCHEE_EXIT -ne 2 ]]; then
    echo "ERROR: lychee crashed (exit=$LYCHEE_EXIT); see /tmp/sst3-lychee.err.$$" >&2
    exit 2
fi
rm -f /tmp/sst3-lychee.err.$$

# Reshape error_map into NDJSON one record per broken link.
OUT=$(printf '%s' "$RAW" \
    | jq -c '.error_map // {} | to_entries[] | .key as $f | .value[]? | {file: $f, url: .url, status: (.status.code // "unknown" | tostring), error: (.status.text // "failed")}' \
    2>/dev/null || true)

[[ -n "$OUT" ]] && echo "$OUT"

# Stderr sentinel: always emitted, regardless of exit code.
N_PATHS=${#PATHS[@]}
if [[ -n "$OUT" ]]; then
    N_BROKEN=$(printf '%s\n' "$OUT" | grep -c .)
else
    N_BROKEN=0
fi
echo "sst3-doc-links: scanned $N_PATHS path(s), $N_BROKEN broken link(s)" >&2

[[ "$STRICT" -eq 1 ]] && [[ -n "$OUT" ]] && exit 1
exit 0
