#!/usr/bin/env bash
# sst3-doc-yaml.sh — YAML lint for SST3 configs (yamllint wrapper).
#
# Usage:   sst3-doc-yaml.sh [paths...]
# Default: lints .github/, .pre-commit-config.yaml, SST3/**/*.yml, SST3/**/*.yaml
# Output:  NDJSON, one object per violation: {file, line, level, rule, description}
# Engine:  yamllint (pipx). Exit 127 + stderr contract on missing engine.

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

if ! command -v yamllint >/dev/null 2>&1; then
    echo 'ERROR: yamllint not installed; see dotfiles/docs/guides/code-query-playbook.md "Wrapper-Script Lane > Install"' >&2
    exit 127
fi

if [[ $# -eq 0 ]]; then
    PATHS=('.github/' '.pre-commit-config.yaml' 'SST3/')
    # Filter to existing paths only.
    EXISTING=()
    for p in "${PATHS[@]}"; do
        [[ -e "$p" ]] && EXISTING+=("$p")
    done
    PATHS=("${EXISTING[@]}")
else
    PATHS=("$@")
fi

# Empty-paths guard (#447 Phase 2): yamllint invoked with no args has undefined
# behaviour across versions (some scan cwd, others error). Fail loud + clean
# rather than silent-zero or scan-the-world.
if [[ ${#PATHS[@]} -eq 0 ]]; then
    echo "sst3-doc-yaml: no input paths" >&2
    exit 0
fi

VIOLATION_COUNT=0

# Universal "I ran" sentinel — emit on every exit path (#447 Phase 2).
trap 'printf "sst3-doc-yaml: scanned %d path(s), %d violation(s)\n" "${#PATHS[@]}" "${VIOLATION_COUNT:-0}" >&2' EXIT

SST3_EMITTED_COUNT="${SST3_EMITTED_COUNT:-0}"
on_sigterm() {
    if command -v jq >/dev/null 2>&1; then
        jq -nc --arg n "sst3-doc-yaml" --argjson e "${SST3_EMITTED_COUNT:-0}" \
            '{kind:($n + "-killed"), reason:"sigterm", partial_records:$e}'
    else
        printf '{"kind":"%s-killed","reason":"sigterm","partial_records":%s}\n' \
            "sst3-doc-yaml" "${SST3_EMITTED_COUNT:-0}"
    fi
    exit 143
}
trap on_sigterm SIGTERM


# yamllint -f parsable emits: <file>:<line>:<col>: [<level>] <description> (<rule>)
# Pipe through a counter that increments VIOLATION_COUNT (uses process-substitution
# to avoid the subshell-counter trap that bit Bug B in sst3-check.sh).
while IFS= read -r LINE; do
    FILE=$(echo "$LINE" | cut -d':' -f1)
    LN=$(echo "$LINE" | cut -d':' -f2)
    COL=$(echo "$LINE" | cut -d':' -f3)
    REST=$(echo "$LINE" | cut -d':' -f4-)
    LEVEL=$(echo "$REST" | grep -oE '\[(error|warning)\]' | tr -d '[]' || echo "info")
    RULE=$(echo "$REST" | grep -oE '\([a-z-]+\)$' | tr -d '()' || echo "unknown")
    DESC=$(echo "$REST" | sed -E 's/^\s*\[(error|warning)\]\s*//; s/\s*\([a-z-]+\)$//')
    jq -nc --arg f "$FILE" --argjson l "${LN:-0}" --arg lv "$LEVEL" --arg r "$RULE" --arg d "$DESC" \
        '{file: $f, line: $l, level: $lv, rule: $r, description: $d}'
    VIOLATION_COUNT=$((VIOLATION_COUNT + 1))
done < <(yamllint -f parsable "${PATHS[@]}" 2>/dev/null || true)
