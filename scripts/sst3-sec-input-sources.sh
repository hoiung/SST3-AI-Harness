#!/usr/bin/env bash
# sst3-sec-input-sources.sh — Surface every untrusted-input entry point.
#
# Usage:   sst3-sec-input-sources.sh [--paths-from <ndjson>]
# Output:  NDJSON, one object per source:
#          {file, line, source_kind, snippet}
#          source_kind: http_body | http_query | http_form | cli_argv | stdin | file_open
#          snippet: best-effort 60-char window of the match
# Engines: ast-grep (Python only — Phase 8 ships Python; Rust + JS in follow-up)
#
# Rationale (#447 Phase 8): pairs with sst3-sec-subprocess.sh + sec-deserialize.
# Auditors trace data flow from "where does untrusted input enter?" to
# "where does it reach a sink?" — this wrapper enumerates the entry points.

set -euo pipefail

# shellcheck source=./sst3-bash-utils.sh
source "$(dirname "$0")/sst3-bash-utils.sh"
export LC_ALL=C
SST3_EMITTED_COUNT=0

trap 'wrapper_sentinel "sst3-sec-input-sources" "$SST3_EMITTED_COUNT" "source"' EXIT
on_sigterm() {
    jq -nc --arg n "sst3-sec-input-sources" --argjson e "$SST3_EMITTED_COUNT" \
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

emit_record() {
    local file="$1" line="$2" source_kind="$3" snippet="$4"
    if path_allowed "$file"; then
        snippet="${snippet:0:60}"
        jq -nc --arg f "$file" --argjson l "$line" --arg sk "$source_kind" --arg sn "$snippet" \
            '{file:$f, line:$l, source_kind:$sk, snippet:$sn}'
        SST3_EMITTED_COUNT=$((SST3_EMITTED_COUNT + 1))
    fi
}

# (source_kind, ast-grep pattern). All Python.
PATTERNS=(
    "http_body|request.json"
    "http_body|request.get_json(\$\$\$)"
    "http_body|request.data"
    "http_form|request.form"
    "http_query|request.args"
    "cli_argv|sys.argv"
    "stdin|sys.stdin.read(\$\$\$)"
    "stdin|input(\$\$\$)"
    "file_open|open(\$\$\$)"
)

for spec in "${PATTERNS[@]}"; do
    IFS='|' read -r kind pattern <<< "$spec"
    while IFS= read -r record; do
        [[ -z "$record" ]] && continue
        file=$(jq -r '.file // ""' <<< "$record")
        line=$(jq -r '.range.start.line // 0' <<< "$record")
        text=$(jq -r '.text // ""' <<< "$record")
        [[ -z "$file" ]] && continue
        emit_record "$file" "$line" "$kind" "$text"
    done < <(ast-grep run --pattern "$pattern" --lang python --json=stream 2>/dev/null || true)
done

exit 0
