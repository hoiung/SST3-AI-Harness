#!/usr/bin/env bash
# sst3-code-entry-points.sh — Pre-baked entry-point discovery.
#
# Usage:   sst3-code-entry-points.sh <lang>
# Example: sst3-code-entry-points.sh python
# Output:  NDJSON, one object per entry point:
#          {file, line, kind, symbol}
#          kind: main | cli | http_handler | controller_init | service_main
# Engines: ast-grep pre-baked patterns per language.
#
# Rationale (#447 Phase 8): closes the onboarding-scenario gap (44% coverage).
# A new contributor / subagent can ask "where does this codebase START?"
# and get a uniform NDJSON answer regardless of language.

set -euo pipefail

# shellcheck source=./sst3-bash-utils.sh
source "$(dirname "$0")/sst3-bash-utils.sh"
export LC_ALL=C
SST3_EMITTED_COUNT=0

trap 'wrapper_sentinel "sst3-code-entry-points" "$SST3_EMITTED_COUNT" "entry"' EXIT
on_sigterm() {
    jq -nc --arg n "sst3-code-entry-points" --argjson e "$SST3_EMITTED_COUNT" \
        '{kind:($n + "-killed"), reason:"sigterm", partial_records:$e}'
    exit 143
}
trap on_sigterm SIGTERM

PATHS_FROM=""
ARGS=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        --paths-from)
            PATHS_FROM="${2:-}"
            shift 2 || break
            ;;
        *)
            ARGS+=("$1")
            shift
            ;;
    esac
done

if [[ ${#ARGS[@]} -lt 1 ]]; then
    echo "ERROR: usage: $(basename "$0") <lang> [--paths-from <ndjson>]" >&2
    exit 64
fi

LANG=$(normalise_lang "${ARGS[0]}")

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
    local file="$1" line="$2" kind="$3" symbol="$4"
    if path_allowed "$file"; then
        jq -nc --arg f "$file" --argjson l "$line" --arg k "$kind" --arg s "$symbol" \
            '{file:$f, line:$l, kind:$k, symbol:$s}'
        SST3_EMITTED_COUNT=$((SST3_EMITTED_COUNT + 1))
    fi
}

run_pattern() {
    local pattern="$1" kind="$2" sym_meta="${3:-}"
    while IFS= read -r record; do
        [[ -z "$record" ]] && continue
        file=$(jq -r '.file // ""' <<< "$record")
        line=$(jq -r '.range.start.line // 0' <<< "$record")
        if [[ -n "$sym_meta" ]]; then
            symbol=$(jq -r --arg m "$sym_meta" '.metaVariables.single[$m].text // ""' <<< "$record")
        else
            symbol="$kind"
        fi
        [[ -z "$file" ]] && continue
        emit_record "$file" "$line" "$kind" "$symbol"
    done < <(ast-grep run --pattern "$pattern" --lang "$LANG" --json=stream 2>/dev/null || true)
}

NL=$'\n'
case "$LANG" in
    python)
        run_pattern 'if __name__ == "__main__": $$$' "main"
        run_pattern "@app.route(\$\$\$)${NL}def \$NAME(\$\$\$): \$\$\$" "http_handler" "NAME"
        run_pattern "@app.get(\$\$\$)${NL}def \$NAME(\$\$\$): \$\$\$" "http_handler" "NAME"
        run_pattern "@app.post(\$\$\$)${NL}def \$NAME(\$\$\$): \$\$\$" "http_handler" "NAME"
        run_pattern "@router.get(\$\$\$)${NL}def \$NAME(\$\$\$): \$\$\$" "http_handler" "NAME"
        run_pattern "@router.post(\$\$\$)${NL}def \$NAME(\$\$\$): \$\$\$" "http_handler" "NAME"
        run_pattern "@click.command(\$\$\$)${NL}def \$NAME(\$\$\$): \$\$\$" "cli" "NAME"
        ;;
    rust)
        run_pattern 'fn main() { $$$ }' "main"
        run_pattern 'pub fn main() { $$$ }' "main"
        run_pattern "#[tokio::main]${NL}async fn main() { \$\$\$ }" "main"
        ;;
    javascript|typescript|tsx)
        run_pattern 'app.get($$$, $HANDLER)' "http_handler" "HANDLER"
        run_pattern 'app.post($$$, $HANDLER)' "http_handler" "HANDLER"
        run_pattern 'router.get($$$, $HANDLER)' "http_handler" "HANDLER"
        run_pattern 'router.post($$$, $HANDLER)' "http_handler" "HANDLER"
        ;;
    *)
        echo "ERROR: code-entry-points supports python|rust|javascript|typescript|tsx (got: $LANG)" >&2
        exit 64
        ;;
esac

exit 0
