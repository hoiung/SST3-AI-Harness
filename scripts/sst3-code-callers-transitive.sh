#!/usr/bin/env bash
# sst3-code-callers-transitive.sh — BFS reverse-call lookup with depth.
#
# Usage:   sst3-code-callers-transitive.sh <symbol> <lang> [--depth=N]
# Example: sst3-code-callers-transitive.sh foo python --depth=3
# Output:  NDJSON, one record per visited symbol per depth level:
#          {file, line, symbol, depth, path:[chain]}
#          path: chain of symbol names from <symbol> (depth 0) to current.
# Engines: composes sst3-code-callers.sh (single-hop). Symbol extraction at
#          each call site is best-effort (enclosing-function heuristic via
#          ripgrep on the same line backward to nearest `def`/`fn`).
# Default depth: 2.
#
# Rationale (#447 Phase 8): single-hop callers leaves auditors hand-stitching
# chains. This wrapper enumerates the BFS with bounded depth so subagents
# get a complete blast-radius graph in one call.

set -euo pipefail

# shellcheck source=./sst3-bash-utils.sh
source "$(dirname "$0")/sst3-bash-utils.sh"
export LC_ALL=C
SST3_EMITTED_COUNT=0

on_sigterm() {
    jq -nc --arg n "sst3-code-callers-transitive" --argjson e "$SST3_EMITTED_COUNT" \
        '{kind:($n + "-killed"), reason:"sigterm", partial_records:$e}'
    exit 143
}
trap on_sigterm SIGTERM
# (EXIT trap registered later, after $QUEUE/$VISITED tmpfiles are created —
# combines tmpfile cleanup with wrapper_sentinel to avoid overwriting the
# sentinel registration. Ralph Tier 3 FAIL C.)

DEPTH=2
PATHS_FROM=""
ARGS=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        --depth=*)
            DEPTH="${1#--depth=}"
            shift
            ;;
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
    echo "ERROR: usage: $(basename "$0") <symbol> <lang> [--depth=N] [--paths-from <ndjson>]" >&2
    exit 64
fi
if [[ ! "$DEPTH" =~ ^[0-9]+$ ]] || [[ "$DEPTH" -lt 1 ]] || [[ "$DEPTH" -gt 5 ]]; then
    echo "ERROR: --depth must be 1..5 (got: $DEPTH)" >&2
    exit 64
fi

# Stage 5 fix — was accepting --paths-from but never applying it (SC2034).
activate_paths_from_filter "$PATHS_FROM"

SYMBOL="${ARGS[0]}"
LANG_RAW="${ARGS[1]}"
assert_safe_identifier "$SYMBOL"
LANG=$(normalise_lang "$LANG_RAW")

if ! command -v jq >/dev/null 2>&1; then
    echo 'ERROR: jq not installed; see dotfiles/docs/guides/code-query-playbook.md "Wrapper-Script Lane > Install"' >&2
    exit 127
fi
if ! command -v rg >/dev/null 2>&1; then
    echo 'ERROR: ripgrep not installed; see dotfiles/docs/guides/code-query-playbook.md "Wrapper-Script Lane > Install"' >&2
    exit 127
fi

SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"
CALLERS_WRAPPER="$SCRIPTS_DIR/sst3-code-callers.sh"
[[ -f "$CALLERS_WRAPPER" ]] || { echo "ERROR: missing $CALLERS_WRAPPER" >&2; exit 127; }

# Find the enclosing function/def name for a (file, line) by scanning backward.
enclosing_fn() {
    local file="$1" line="$2"
    case "$LANG" in
        python)
            awk -v target="$line" '
                /^[[:space:]]*def[[:space:]]+([a-zA-Z_][a-zA-Z0-9_]*)/ {
                    match($0, /def[[:space:]]+([a-zA-Z_][a-zA-Z0-9_]*)/, m); cur = m[1]
                }
                NR == target { print cur; exit }' "$file" 2>/dev/null
            ;;
        rust)
            awk -v target="$line" '
                /^[[:space:]]*(pub[[:space:]]+)?fn[[:space:]]+([a-zA-Z_][a-zA-Z0-9_]*)/ {
                    match($0, /fn[[:space:]]+([a-zA-Z_][a-zA-Z0-9_]*)/, m); cur = m[1]
                }
                NR == target { print cur; exit }' "$file" 2>/dev/null
            ;;
        javascript|typescript|tsx)
            awk -v target="$line" '
                /^[[:space:]]*(function|async function|export function|export default function)[[:space:]]+([a-zA-Z_$][a-zA-Z0-9_$]*)/ {
                    match($0, /function[[:space:]]+([a-zA-Z_$][a-zA-Z0-9_$]*)/, m); cur = m[1]
                }
                /^[[:space:]]*const[[:space:]]+([a-zA-Z_$][a-zA-Z0-9_$]*)[[:space:]]*=/ {
                    match($0, /const[[:space:]]+([a-zA-Z_$][a-zA-Z0-9_$]*)/, m); cur = m[1]
                }
                NR == target { print cur; exit }' "$file" 2>/dev/null
            ;;
        *)
            echo ""
            ;;
    esac
}

# BFS state. Use a queue (text file) and a visited set (text file).
QUEUE=$(mktemp)
VISITED=$(mktemp)
# Combine tmpfile cleanup with wrapper_sentinel for EXIT (Ralph Tier 3 FAIL C).
trap 'rm -f "$QUEUE" "$VISITED"; wrapper_sentinel "sst3-code-callers-transitive" "$SST3_EMITTED_COUNT" "caller"' EXIT
trap 'rm -f "$QUEUE" "$VISITED"' INT TERM

# Each queue entry: SYMBOL\tDEPTH\tPATH(comma-separated chain)
printf '%s\t0\t%s\n' "$SYMBOL" "$SYMBOL" > "$QUEUE"
echo "$SYMBOL" > "$VISITED"

while IFS= read -r entry; do
    [[ -z "$entry" ]] && continue
    sym=$(printf '%s' "$entry" | cut -f1)
    cur_depth=$(printf '%s' "$entry" | cut -f2)
    cur_path=$(printf '%s' "$entry" | cut -f3)
    [[ -z "$sym" ]] && continue

    if (( cur_depth >= DEPTH )); then
        continue
    fi

    while IFS= read -r call; do
        [[ -z "$call" ]] && continue
        file=$(jq -r '.file // ""' <<< "$call")
        line=$(jq -r '.line // 0' <<< "$call")
        [[ -z "$file" || "$line" == "0" ]] && continue
        encl=$(enclosing_fn "$file" "$line")
        [[ -z "$encl" ]] && encl="<top-level>"

        next_depth=$((cur_depth + 1))
        next_path="$cur_path,$encl"
        chain_json=$(printf '%s' "$next_path" | jq -Rc 'split(",")')

        jq -nc --arg f "$file" --argjson l "$line" --arg s "$encl" \
            --argjson d "$next_depth" --argjson p "$chain_json" \
            '{file:$f, line:$l, symbol:$s, depth:$d, path:$p}'
        SST3_EMITTED_COUNT=$((SST3_EMITTED_COUNT + 1))

        if [[ "$encl" != "<top-level>" ]] && ! grep -Fxq "$encl" "$VISITED"; then
            echo "$encl" >> "$VISITED"
            if [[ "$encl" =~ ^[a-zA-Z_][a-zA-Z0-9_.]*$ ]]; then
                printf '%s\t%s\t%s\n' "$encl" "$next_depth" "$next_path" >> "$QUEUE"
            fi
        fi
    done < <(bash "$CALLERS_WRAPPER" "$sym" "$LANG" 2>/dev/null || true)
done < "$QUEUE"

exit 0
