#!/usr/bin/env bash
# sst3-code-callers.sh — Reverse-call lookup for a symbol via ast-grep fallback.
#
# Usage:   sst3-code-callers.sh <symbol> <lang>
# Example: sst3-code-callers.sh BANNED_WORDS python
# Output:  NDJSON, one object per call site: {file, line, kind}
# Design:  Primary engine intended is the CC `LSP` tool's `incomingCalls`,
#          callable by an agent directly when LSP is wired for the language.
#          When LSP is not wired (verified Phase 1 smoke 2026-04-25), this
#          bash wrapper falls back to ast-grep call-site pattern matching.
#          Missing ast-grep → stderr contract + exit 127.

set -euo pipefail
export LC_ALL=C


SST3_EMITTED_COUNT="${SST3_EMITTED_COUNT:-0}"
on_sigterm() {
    if command -v jq >/dev/null 2>&1; then
        jq -nc --arg n "sst3-code-callers" --argjson e "${SST3_EMITTED_COUNT:-0}" \
            '{kind:($n + "-killed"), reason:"sigterm", partial_records:$e}'
    else
        printf '{"kind":"%s-killed","reason":"sigterm","partial_records":%s}\n' \
            "sst3-code-callers" "${SST3_EMITTED_COUNT:-0}"
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

if [[ $# -lt 2 ]]; then
    echo "ERROR: usage: $(basename "$0") <symbol> <lang>" >&2
    exit 64
fi

SYMBOL="$1"
RAW_LANG="$2"

assert_safe_identifier "$SYMBOL"
LANG=$(normalise_lang "$RAW_LANG")

if ! command -v ast-grep >/dev/null 2>&1; then
    echo 'ERROR: ast-grep not installed; see dotfiles/docs/guides/code-query-playbook.md "Wrapper-Script Lane > Install"' >&2
    exit 127
fi

ast-grep run --pattern "${SYMBOL}(\$\$\$)" --lang "$LANG" --json=stream 2>/dev/null \
    | jq -c '{file, line: .range.start.line, kind: "call"}' \
    || true
