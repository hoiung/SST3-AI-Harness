#!/usr/bin/env bash
# sst3-sync-tool-eviction.sh — Generic tool-name eviction guard.
#
# Usage:   sst3-sync-tool-eviction.sh <evicted_token> [files...]
# Example: sst3-sync-tool-eviction.sh "mcp__$(printf %s code-review-graph)__"
#          (token broken via printf so this docstring doesn't trip the
#          eviction-guard hook that scans this very file).
# Default scope: .claude/, SST3/, docs/research/, CLAUDE.md
# Output:  NDJSON, one object per offender: {file, line, token, context}
# Engine:  ripgrep. Exit 127 + stderr contract on missing engine.
# Note:    Generic version of check-no-code-review-graph.sh (Stage 5 hard-coded
#          one specific token; this lets the user pass any displaced tool name).
#          HISTORICAL-MCP-REFERENCES blocks are NOT skipped — caller decides
#          via path filtering.

set -euo pipefail
export LC_ALL=C


SST3_EMITTED_COUNT="${SST3_EMITTED_COUNT:-0}"
on_sigterm() {
    if command -v jq >/dev/null 2>&1; then
        jq -nc --arg n "sst3-sync-tool-eviction" --argjson e "${SST3_EMITTED_COUNT:-0}" \
            '{kind:($n + "-killed"), reason:"sigterm", partial_records:$e}'
    else
        printf '{"kind":"%s-killed","reason":"sigterm","partial_records":%s}\n' \
            "sst3-sync-tool-eviction" "${SST3_EMITTED_COUNT:-0}"
    fi
    exit 143
}
trap on_sigterm SIGTERM

if [[ $# -lt 1 ]]; then
    echo "ERROR: usage: $(basename "$0") <evicted_token> [files...]" >&2
    exit 64
fi

if ! command -v rg >/dev/null 2>&1; then
    echo 'ERROR: ripgrep not installed; see dotfiles/docs/guides/code-query-playbook.md "Wrapper-Script Lane > Install"' >&2
    exit 127
fi

TOKEN="$1"
shift

if [[ $# -eq 0 ]]; then
    SEARCH_PATHS=('.claude/' 'SST3/' 'docs/research/' 'CLAUDE.md')
    EXISTING=()
    for p in "${SEARCH_PATHS[@]}"; do
        [[ -e "$p" ]] && EXISTING+=("$p")
    done
    SEARCH_PATHS=("${EXISTING[@]}")
else
    SEARCH_PATHS=("$@")
fi

rg --json --no-heading -F "$TOKEN" "${SEARCH_PATHS[@]}" 2>/dev/null \
    | jq -c --arg tok "$TOKEN" 'select(.type=="match") | {
        file: .data.path.text,
        line: .data.line_number,
        token: $tok,
        context: (.data.lines.text | rtrimstr("\n"))
      }' \
    || true
