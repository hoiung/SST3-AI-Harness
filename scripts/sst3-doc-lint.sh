#!/usr/bin/env bash
# sst3-doc-lint.sh — Markdown linting for SST3 docs (markdownlint-cli2 wrapper).
#
# Usage:   sst3-doc-lint.sh [globs...]
# Default: lints SST3/**/*.md + docs/**/*.md + CLAUDE.md + README.md
# Output:  NDJSON, one object per violation: {file, line, rule, description}
# Engine:  markdownlint-cli2 (npm). Exit 127 + stderr contract on missing engine.

set -euo pipefail
export LC_ALL=C


SST3_EMITTED_COUNT="${SST3_EMITTED_COUNT:-0}"
on_sigterm() {
    if command -v jq >/dev/null 2>&1; then
        jq -nc --arg n "sst3-doc-lint" --argjson e "${SST3_EMITTED_COUNT:-0}" \
            '{kind:($n + "-killed"), reason:"sigterm", partial_records:$e}'
    else
        printf '{"kind":"%s-killed","reason":"sigterm","partial_records":%s}\n' \
            "sst3-doc-lint" "${SST3_EMITTED_COUNT:-0}"
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

if ! command -v markdownlint-cli2 >/dev/null 2>&1; then
    echo 'ERROR: markdownlint-cli2 not installed; see dotfiles/docs/guides/code-query-playbook.md "Wrapper-Script Lane > Install"' >&2
    exit 127
fi

if [[ $# -eq 0 ]]; then
    GLOBS=('SST3/**/*.md' 'docs/**/*.md' 'CLAUDE.md' 'README.md')
else
    GLOBS=("$@")
fi

# markdownlint-cli2 emits text in two forms:
#   <file>:<line> error <rule> <description> [Context: "..."]
#   <file>:<line>:<col> error <rule> <description>
# We reshape to NDJSON. Both forms are handled by stripping line+col prefix and
# parsing the remainder for the MD### rule code and description.
markdownlint-cli2 "${GLOBS[@]}" 2>&1 | grep -E '^[^[:space:]]+:[0-9]+(:[0-9]+)? (error|warning) MD' | while IFS= read -r LINE; do
    FILE=$(echo "$LINE" | sed -E 's/^([^:]+):.*$/\1/')
    LN=$(echo "$LINE" | sed -E 's/^[^:]+:([0-9]+).*$/\1/')
    RULE=$(echo "$LINE" | grep -oE 'MD[0-9]+(/[a-z-]+)?' | head -1)
    DESC=$(echo "$LINE" | sed -E "s|^[^:]+:[0-9]+(:[0-9]+)? (error\|warning) MD[0-9]+(/[a-z-]+)? ||; s| \[Context: .*\]$||")
    jq -nc --arg f "$FILE" --argjson l "${LN:-0}" --arg r "${RULE:-unknown}" --arg d "$DESC" \
        '{file: $f, line: $l, rule: $r, description: $d}'
done || true
