#!/usr/bin/env bash
# sst3-code-search.sh — Wrapper-lane structural / literal symbol search.
#
# Usage:   sst3-code-search.sh <pattern> <lang> [--literal]
# Example: sst3-code-search.sh '$F($$$)' python
#          sst3-code-search.sh 'voice_rules' python --literal
# Output:  NDJSON, one object per match: {file, range:{start,end}, text}
# Engines: ripgrep (--literal mode); ast-grep --json=stream (structural, default).
#          Missing engine → stderr contract + exit 127 (per Phase 5 hook + Ralph).

set -euo pipefail
export LC_ALL=C


SST3_EMITTED_COUNT="${SST3_EMITTED_COUNT:-0}"
on_sigterm() {
    if command -v jq >/dev/null 2>&1; then
        jq -nc --arg n "sst3-code-search" --argjson e "${SST3_EMITTED_COUNT:-0}" \
            '{kind:($n + "-killed"), reason:"sigterm", partial_records:$e}'
    else
        printf '{"kind":"%s-killed","reason":"sigterm","partial_records":%s}\n' \
            "sst3-code-search" "${SST3_EMITTED_COUNT:-0}"
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

if [[ $# -lt 2 ]]; then
    echo "ERROR: usage: $(basename "$0") <pattern> <lang> [--literal]" >&2
    exit 64
fi

PATTERN="$1"
RAW_LANG="$2"
MODE="${3:-structural}"

# #447 Phase 3: normalise language alias before passing to ast-grep
# (prevents silent-pass of unsupported lang strings to inner engine).
LANG=$(normalise_lang "$RAW_LANG")

if [[ "$MODE" == "--literal" ]]; then
    if ! command -v rg >/dev/null 2>&1; then
        echo 'ERROR: ripgrep not installed; see dotfiles/docs/guides/code-query-playbook.md "Wrapper-Script Lane > Install"' >&2
        exit 127
    fi
    # #447 Phase 2: dropped `-w` (word-boundary) — patterns containing whitespace
    # silently matched nothing under -w (e.g. 'def ' produced 0 hits). Literal
    # mode is now exact-substring match. Warn callers if their pattern looks
    # like an identifier (no whitespace, valid ident chars) so they know they
    # could pass --word-regex separately if they want word-boundary semantics.
    if [[ "$PATTERN" == *' '* ]]; then
        echo "INFO: sst3-code-search literal mode — exact substring match (-w word-boundary dropped #447 Phase 2)" >&2
    fi
    # #447 Phase 4 fix: pass `.` explicitly so rg walks cwd in non-TTY contexts.
    # When stdin is not a TTY (CI, pre-commit, subagent subprocess invocations,
    # the self-test driver), rg reads paths from stdin instead of walking cwd —
    # which produces 0 matches with 0 stderr (silent-zero class). Surfaced
    # during Phase 4 self-test rollout: the code-search-keyword fixture
    # passed under interactive bash but failed under pre-commit's subprocess.
    rg --json -n "$PATTERN" . 2>/dev/null \
        | jq -c 'select(.type=="match") | {file: .data.path.text, range: {start: .data.line_number, end: .data.line_number}, text: (.data.lines.text // "")}' \
        || true
else
    if ! command -v ast-grep >/dev/null 2>&1; then
        echo 'ERROR: ast-grep not installed; see dotfiles/docs/guides/code-query-playbook.md "Wrapper-Script Lane > Install"' >&2
        exit 127
    fi
    # #447 Phase 4 fix: same non-TTY guard for the structural path. ast-grep's
    # `run --pattern X --lang L` defaults to walking cwd, but only when stdin
    # is a TTY; under subprocess invocation it reads file paths from stdin.
    # `--globs` would also work; bare `.` is the smaller change.
    ast-grep run --pattern "$PATTERN" --lang "$LANG" --json=stream . 2>/dev/null \
        | jq -c '{file, range: {start: .range.start.line, end: .range.end.line}, text}' \
        || true
fi
