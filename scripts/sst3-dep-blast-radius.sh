#!/usr/bin/env bash
# sst3-dep-blast-radius.sh — Compose dep-usage + code-callers per use-site.
#
# Usage:   sst3-dep-blast-radius.sh <package> <lang>
# Example: sst3-dep-blast-radius.sh requests python
# Output:  NDJSON, one object per package-symbol use-site:
#          {file, line, symbol_used, callers_count}
#          callers_count is the number of inbound call sites for the
#          enclosing function — proxy for blast radius if the dep upgrade
#          breaks `symbol_used`.
# Engines: composes sst3-dep-usage.sh + sst3-code-callers.sh.
#
# Rationale (#447 Phase 8): the missing link between "we use foo.bar" and
# "if foo.bar breaks, N upstream callers explode". Subagents previously had
# to hand-stitch dep-usage output through code-callers; this wrapper does it.

set -euo pipefail

# shellcheck source=./sst3-bash-utils.sh
source "$(dirname "$0")/sst3-bash-utils.sh"
export LC_ALL=C
SST3_EMITTED_COUNT=0

trap 'wrapper_sentinel "sst3-dep-blast-radius" "$SST3_EMITTED_COUNT" "use-site"' EXIT
on_sigterm() {
    jq -nc --arg n "sst3-dep-blast-radius" --argjson e "$SST3_EMITTED_COUNT" \
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

if [[ ${#ARGS[@]} -lt 2 ]]; then
    echo "ERROR: usage: $(basename "$0") <package> <lang> [--paths-from <ndjson>]" >&2
    exit 64
fi

PACKAGE="${ARGS[0]}"
LANG_RAW="${ARGS[1]}"
assert_safe_identifier "$PACKAGE"
LANG=$(normalise_lang "$LANG_RAW")

if ! command -v jq >/dev/null 2>&1; then
    echo 'ERROR: jq not installed; see dotfiles/docs/guides/code-query-playbook.md "Wrapper-Script Lane > Install"' >&2
    exit 127
fi
if ! command -v ast-grep >/dev/null 2>&1; then
    echo 'ERROR: ast-grep not installed; see dotfiles/docs/guides/code-query-playbook.md "Wrapper-Script Lane > Install"' >&2
    exit 127
fi

SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"
USAGE_WRAPPER="$SCRIPTS_DIR/sst3-dep-usage.sh"
CALLERS_WRAPPER="$SCRIPTS_DIR/sst3-code-callers.sh"

if [[ ! -f "$USAGE_WRAPPER" || ! -f "$CALLERS_WRAPPER" ]]; then
    echo "ERROR: depends on sst3-dep-usage.sh + sst3-code-callers.sh in same dir" >&2
    exit 127
fi

# Forward --paths-from if provided.
declare -a USAGE_ARGS=("$PACKAGE" "$LANG")
[[ -n "$PATHS_FROM" ]] && USAGE_ARGS+=("--paths-from" "$PATHS_FROM")

# We surface per-symbol use-site records. callers_count counts inbound
# callers of the symbol itself (not the enclosing function — that requires
# a follow-up enclosing-function lookup we don't have a wrapper for yet).
while IFS= read -r record; do
    [[ -z "$record" ]] && continue
    file=$(jq -r '.file // ""' <<< "$record")
    line=$(jq -r '.line // 0' <<< "$record")
    symbol=$(jq -r '.symbol // ""' <<< "$record")
    [[ -z "$file" || -z "$symbol" ]] && continue

    # Count callers of the symbol. Skip empty/unsafe symbols.
    callers_count=0
    if [[ "$symbol" =~ ^[a-zA-Z_][a-zA-Z0-9_.]*$ ]]; then
        callers_count=$(bash "$CALLERS_WRAPPER" "$symbol" "$LANG" 2>/dev/null | wc -l)
    fi

    jq -nc --arg f "$file" --argjson l "$line" --arg s "$symbol" --argjson c "$callers_count" \
        '{file:$f, line:$l, symbol_used:$s, callers_count:$c}'
    SST3_EMITTED_COUNT=$((SST3_EMITTED_COUNT + 1))
done < <(bash "$USAGE_WRAPPER" "${USAGE_ARGS[@]}" 2>/dev/null || true)

exit 0
