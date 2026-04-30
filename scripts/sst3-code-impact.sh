#!/usr/bin/env bash
# sst3-code-impact.sh — Blast-radius analysis for files changed vs a base branch.
#
# Usage:   sst3-code-impact.sh <base-branch>
# Example: sst3-code-impact.sh main
# Output:  NDJSON, one object per changed file: {changed_file, impacted_callers}
#          where impacted_callers is an integer count of call sites referencing
#          a top-level symbol in changed_file.
# Engines: git diff --name-only base...HEAD; ast-grep --json=stream per file.

set -euo pipefail
export LC_ALL=C


SST3_EMITTED_COUNT="${SST3_EMITTED_COUNT:-0}"
on_sigterm() {
    if command -v jq >/dev/null 2>&1; then
        jq -nc --arg n "sst3-code-impact" --argjson e "${SST3_EMITTED_COUNT:-0}" \
            '{kind:($n + "-killed"), reason:"sigterm", partial_records:$e}'
    else
        printf '{"kind":"%s-killed","reason":"sigterm","partial_records":%s}\n' \
            "sst3-code-impact" "${SST3_EMITTED_COUNT:-0}"
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

if [[ $# -lt 1 ]]; then
    echo "ERROR: usage: $(basename "$0") <base-branch>" >&2
    exit 64
fi

BASE="$1"

if ! command -v ast-grep >/dev/null 2>&1; then
    echo 'ERROR: ast-grep not installed; see dotfiles/docs/guides/code-query-playbook.md "Wrapper-Script Lane > Install"' >&2
    exit 127
fi

CHANGED=$(git diff --name-only "${BASE}...HEAD" -- '*.py' '*.ts' '*.tsx' '*.js' '*.rs' 2>/dev/null || true)

if [[ -z "$CHANGED" ]]; then
    exit 0
fi

while IFS= read -r FILE; do
    [[ -f "$FILE" ]] || continue
    case "$FILE" in
        *.py)  LANG="python" ;;
        *.ts)  LANG="typescript" ;;
        *.tsx) LANG="tsx" ;;
        *.js)  LANG="javascript" ;;
        *.rs)  LANG="rust" ;;
        *)     continue ;;
    esac
    # shellcheck disable=SC2016  # ast-grep meta-vars $F, $$$ must NOT undergo bash expansion
    SYMBOLS=$(ast-grep run --pattern 'def $F($$$)' --lang "$LANG" "$FILE" --json=stream 2>/dev/null | jq -r '.metaVariables.single.F.text // empty' | sort -u)
    COUNT=0
    for SYM in $SYMBOLS; do
        [[ -z "$SYM" ]] && continue
        assert_safe_identifier "$SYM"
        N=$(ast-grep run --pattern "${SYM}(\$\$\$)" --lang "$LANG" --json=stream 2>/dev/null | wc -l || echo 0)
        COUNT=$((COUNT + N))
    done
    jq -nc --arg f "$FILE" --argjson c "$COUNT" '{changed_file: $f, impacted_callers: $c}'
done <<< "$CHANGED"
