#!/usr/bin/env bash
# sst3-sec-deserialize.sh — Surface unsafe-deserialise + dynamic-eval sinks.
#
# Usage:   sst3-sec-deserialize.sh [--paths-from <ndjson>]
# Output:  NDJSON, one object per sink: {file, line, sink, taint_source}
#          sink: pickle.loads | yaml.load | eval | exec | marshal.loads
#          taint_source: best-effort first-arg snippet (literal value or var
#          name) — auditors use this to triangulate where the bytes came from.
# Engines: ast-grep (Python only — these patterns are Python-specific)
#
# Note on yaml.load: only flagged when it is invoked WITHOUT a SafeLoader
# argument. The pattern catches the unsafe form `yaml.load($BYTES)` and
# `yaml.load($BYTES, $LOADER)` where $LOADER is not literally `SafeLoader`
# or `yaml.SafeLoader`. This is best-effort — auditors must still confirm.

set -euo pipefail

# shellcheck source=./sst3-bash-utils.sh
source "$(dirname "$0")/sst3-bash-utils.sh"
export LC_ALL=C
SST3_EMITTED_COUNT=0

trap 'wrapper_sentinel "sst3-sec-deserialize" "$SST3_EMITTED_COUNT" "sink"' EXIT
on_sigterm() {
    jq -nc --arg n "sst3-sec-deserialize" --argjson e "$SST3_EMITTED_COUNT" \
        '{kind:($n + "-killed"), reason:"sigterm", partial_records:$e}'
    exit 143
}
trap on_sigterm SIGTERM

PATHS_FROM=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --paths-from)
            PATHS_FROM="${2:-}"
            shift 2 || break
            ;;
        *)
            shift
            ;;
    esac
done

if ! command -v ast-grep >/dev/null 2>&1; then
    echo 'ERROR: ast-grep not installed; see dotfiles/docs/guides/code-query-playbook.md "Wrapper-Script Lane > Install"' >&2
    exit 127
fi
if ! command -v jq >/dev/null 2>&1; then
    echo 'ERROR: jq not installed; see dotfiles/docs/guides/code-query-playbook.md "Wrapper-Script Lane > Install"' >&2
    exit 127
fi

declare -a ALLOWED_PATHS=()
if [[ -n "$PATHS_FROM" ]]; then
    if [[ ! -r "$PATHS_FROM" ]]; then
        echo "ERROR: --paths-from file not readable: $PATHS_FROM" >&2
        exit 64
    fi
    while IFS= read -r p; do
        [[ -n "$p" ]] && ALLOWED_PATHS+=("$p")
    done < <(read_paths_from "$PATHS_FROM")
fi
path_allowed() {
    local file="$1"
    [[ ${#ALLOWED_PATHS[@]} -eq 0 ]] && return 0
    for allowed in "${ALLOWED_PATHS[@]}"; do
        [[ "$file" == "$allowed" || "$file" == "./$allowed" ]] && return 0
    done
    return 1
}

# (sink, ast-grep pattern). yaml.load gets a special filter post-match.
PATTERNS=(
    "pickle.loads|pickle.loads(\$\$\$)"
    "marshal.loads|marshal.loads(\$\$\$)"
    "eval|eval(\$\$\$)"
    "exec|exec(\$\$\$)"
    "yaml.load|yaml.load(\$\$\$)"
)

emit_record() {
    local file="$1" line="$2" sink="$3" taint="$4"
    if path_allowed "$file"; then
        jq -nc --arg f "$file" --argjson l "$line" --arg s "$sink" --arg t "$taint" \
            '{file:$f, line:$l, sink:$s, taint_source:$t}'
        SST3_EMITTED_COUNT=$((SST3_EMITTED_COUNT + 1))
    fi
}

is_safe_yaml_load() {
    local text="$1"
    [[ "$text" == *"SafeLoader"* ]] && return 0
    [[ "$text" == *"safe_load"* ]] && return 0
    return 1
}

extract_first_arg() {
    local text="$1"
    # Pull contents inside the outermost (...) pair.
    local inside="${text#*(}"
    inside="${inside%)*}"
    # Take everything up to the first top-level comma.
    local first="${inside%%,*}"
    # Trim whitespace.
    first="${first## }"
    first="${first%% }"
    echo "$first"
}

for spec in "${PATTERNS[@]}"; do
    IFS='|' read -r sink pattern <<< "$spec"
    while IFS= read -r record; do
        [[ -z "$record" ]] && continue
        file=$(jq -r '.file // ""' <<< "$record")
        line=$(jq -r '.range.start.line // 0' <<< "$record")
        text=$(jq -r '.text // ""' <<< "$record")
        [[ -z "$file" ]] && continue
        if [[ "$sink" == "yaml.load" ]] && is_safe_yaml_load "$text"; then
            continue
        fi
        taint=$(extract_first_arg "$text")
        emit_record "$file" "$line" "$sink" "$taint"
    done < <(ast-grep run --pattern "$pattern" --lang python --json=stream 2>/dev/null || true)
done

exit 0
