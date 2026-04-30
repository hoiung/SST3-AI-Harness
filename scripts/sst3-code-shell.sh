#!/usr/bin/env bash
# sst3-code-shell.sh — Shell-script lint + structural query wrapper.
#
# Usage:   sst3-code-shell.sh [--lint|--struct] [paths...]
# Default: --lint mode, scanning scripts/*.sh + scripts/*.sh + .git/hooks/*
#          --struct mode emits regex-based bash structural facts (function
#          definitions, source/dot includes, eval/exec invocations, here-docs).
#          NOTE: Phase 6 ships ripgrep-regex --struct because ast-grep's bash
#          tree-sitter grammar does not yet parse `$F() { $$$ }` patterns.
#          When ast-grep bash improves we will swap engine without changing
#          the NDJSON contract.
# Output:  NDJSON
#          --lint:   {file, line, kind, name, severity}
#                    kind=shellcheck-<code>, name=shellcheck rule code,
#                    severity=error|warning|info|style
#          --struct: {file, line, kind, name, severity}
#                    kind=function-def|source-include|eval-call|exec-call|heredoc
#                    name=function name / sourced path / token / heredoc tag
#                    severity=info (structural facts are not severity-rated)
# Engines: shellcheck --format=json (lint); ripgrep --json -e <regex> (struct).
#
# Rationale (#447 Phase 6): closes the dotfiles dogfood gap — until now the
# wrapper-lane could not audit its own bash. This wrapper makes shell scripts
# first-class citizens of the structural-query lane.

set -euo pipefail

export LC_ALL=C
SST3_EMITTED_COUNT=0
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

MODE="--lint"
ARGS=()
for arg in "$@"; do
    case "$arg" in
        --lint|--struct) MODE="$arg" ;;
        *) ARGS+=("$arg") ;;
    esac
done

if [[ ${#ARGS[@]} -eq 0 ]]; then
    mapfile -t PATHS < <(find -P SST3/scripts scripts .git/hooks -maxdepth 3 -type f \( -name '*.sh' -o -name '*.bash' \) 2>/dev/null || true)
else
    PATHS=()
    for P in "${ARGS[@]}"; do
        if [[ -d "$P" ]]; then
            mapfile -t -O "${#PATHS[@]}" PATHS < <(find -P "$P" -type f \( -name '*.sh' -o -name '*.bash' \) 2>/dev/null || true)
        elif [[ -f "$P" ]]; then
            PATHS+=("$P")
        fi
    done
fi

trap 'wrapper_sentinel "sst3-code-shell" "$SST3_EMITTED_COUNT" "finding"' EXIT

SST3_EMITTED_COUNT="${SST3_EMITTED_COUNT:-0}"
on_sigterm() {
    if command -v jq >/dev/null 2>&1; then
        jq -nc --arg n "sst3-code-shell" --argjson e "${SST3_EMITTED_COUNT:-0}" \
            '{kind:($n + "-killed"), reason:"sigterm", partial_records:$e}'
    else
        printf '{"kind":"%s-killed","reason":"sigterm","partial_records":%s}\n' \
            "sst3-code-shell" "${SST3_EMITTED_COUNT:-0}"
    fi
    exit 143
}
trap on_sigterm SIGTERM


if [[ ${#PATHS[@]} -eq 0 ]]; then
    exit 0
fi

if ! command -v jq >/dev/null 2>&1; then
    echo 'ERROR: jq not installed; see dotfiles/docs/guides/code-query-playbook.md "Wrapper-Script Lane > Install"' >&2
    exit 127
fi

if [[ "$MODE" == "--lint" ]]; then
    if ! command -v shellcheck >/dev/null 2>&1; then
        echo 'ERROR: shellcheck not installed; see dotfiles/docs/guides/code-query-playbook.md "Wrapper-Script Lane > Install"' >&2
        exit 127
    fi
    # The `shellcheck` tool with `--format=json` emits a single JSON array;
    # we reshape it to one NDJSON record per comment below.
    SC_JSON=$(shellcheck --format=json "${PATHS[@]}" 2>/dev/null || true)
    if [[ -z "$SC_JSON" || "$SC_JSON" == "[]" ]]; then
        exit 0
    fi
    while IFS= read -r RECORD; do
        echo "$RECORD"
        SST3_EMITTED_COUNT=$((SST3_EMITTED_COUNT + 1))
    done < <(jq -c '.[] | {file: .file, line: .line, kind: ("shellcheck-SC" + (.code|tostring)), name: ("SC" + (.code|tostring)), severity: .level}' <<<"$SC_JSON" 2>/dev/null)
else
    if ! command -v rg >/dev/null 2>&1; then
        echo 'ERROR: ripgrep not installed; see dotfiles/docs/guides/code-query-playbook.md "Wrapper-Script Lane > Install"' >&2
        exit 127
    fi
    # Each entry: regex<TAB>kind<TAB>name-extractor (sed cmd applied to match text).
    # kind=function-def | source-include | eval-call | exec-call | heredoc
    declare -a STRUCT_PATTERNS=(
        $'^\\s*([a-zA-Z_][a-zA-Z0-9_]*)\\s*\\(\\)\\s*\\{?\tfunction-def\ts/^\\s*\\([a-zA-Z_][a-zA-Z0-9_]*\\).*$/\\1/'
        $'^\\s*function\\s+([a-zA-Z_][a-zA-Z0-9_]*)\tfunction-def\ts/^\\s*function\\s\\+\\([a-zA-Z_][a-zA-Z0-9_]*\\).*$/\\1/'
        $'^\\s*(\\.|source)\\s+([^\\s|;&]+)\tsource-include\ts/^\\s*\\(\\.\\|source\\)\\s\\+\\([^\\s|;&]\\+\\).*$/\\2/'
        $'(^|[^a-zA-Z_])eval\\s\teval-call\ts/.*/eval/'
        $'(^|[^a-zA-Z_])exec\\s\texec-call\ts/.*/exec/'
        $'<<-?\\s*[\'"]?([A-Z][A-Z0-9_]*)[\'"]?\theredoc\ts/.*<<-\\?\\s*[\'"]\\?\\([A-Z][A-Z0-9_]*\\)[\'"]\\?.*$/\\1/'
    )
    for FILE in "${PATHS[@]}"; do
        [[ -f "$FILE" ]] || continue
        for entry in "${STRUCT_PATTERNS[@]}"; do
            IFS=$'\t' read -r REGEX KIND NAME_SED <<< "$entry"
            while IFS=$'\t' read -r LINE_NO MATCH_TEXT; do
                [[ -z "$LINE_NO" ]] && continue
                NAME=$(printf '%s' "$MATCH_TEXT" | sed "$NAME_SED" 2>/dev/null || echo "unknown")
                jq -nc --arg f "$FILE" --argjson l "$LINE_NO" --arg k "$KIND" --arg n "${NAME:-unknown}" \
                    '{file:$f, line:$l, kind:$k, name:$n, severity:"info"}'
                SST3_EMITTED_COUNT=$((SST3_EMITTED_COUNT + 1))
            done < <(rg --json -n -e "$REGEX" "$FILE" 2>/dev/null \
                | jq -r 'select(.type=="match") | [(.data.line_number|tostring), (.data.lines.text // "")] | @tsv' 2>/dev/null || true)
        done
    done
fi
