#!/usr/bin/env bash
# sst3-doc-lint.sh — Markdown linting for SST3 docs (markdownlint-cli2 wrapper).
#
# Usage:   sst3-doc-lint.sh [globs...]
# Default: lints SST3/**/*.md + docs/**/*.md + CLAUDE.md + README.md
# Output:  STDOUT — NDJSON, one object per violation: {file, line, rule, description}
#          STDERR — always emits a "scan complete" sentinel:
#                   "sst3-doc-lint: scanned <N> path(s), <M> finding(s)"
#                   The stderr sentinel lets consumers distinguish "all clean"
#                   (exit 0, empty stdout, sentinel present) from "didn't run"
#                   (no sentinel / "ENGINE CRASHED" line). #484 Stage-5 — parity
#                   with sst3-doc-links.sh; closes the silent-clean failure mode.
# Engine:  markdownlint-cli2 (npm). Exit 127 + stderr contract on missing engine.
# Exit:    0 = ran (clean or findings reshaped to NDJSON), 2 = engine crashed,
#          127 = engine missing.

set -euo pipefail
export LC_ALL=C


SST3_EMITTED_COUNT="${SST3_EMITTED_COUNT:-0}"
on_sigterm() {
    if command -v jq >/dev/null 2>&1; then
        jq -nc --arg n "sst3-doc-lint" --argjson e "${SST3_EMITTED_COUNT:-0}" \
            '{kind:($n + "-killed"), reason:"sigterm", partial_records:$e}'
    else
        printf '{"kind":"%s-killed","reason":"sigterm","partial_records":%s}\n' \
            "sst3-doc-lint" "${SST3_EMITTED_COUNT:-0}"
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

if ! command -v markdownlint-cli2 >/dev/null 2>&1; then
    echo 'ERROR: markdownlint-cli2 not installed; see dotfiles/docs/guides/code-query-playbook.md "Wrapper-Script Lane > Install"' >&2
    exit 127
fi

if [[ $# -eq 0 ]]; then
    GLOBS=('SST3/**/*.md' 'docs/**/*.md' 'CLAUDE.md' 'README.md')
else
    GLOBS=("$@")
fi

# markdownlint-cli2 emits text in two forms:
#   <file>:<line> error <rule> <description> [Context: "..."]
#   <file>:<line>:<col> error <rule> <description>
# We reshape to NDJSON. Both forms are handled by stripping line+col prefix and
# parsing the remainder for the MD### rule code and description.
#
# #484 Stage-5 reliability fix: capture markdownlint's exit code OUT of the
# pipe so a crashed engine is NOT silently swallowed by `| while ... done
# || true` (the silent-clean failure mode). markdownlint-cli2 exit: 0 = no
# findings, 1 = findings found (NORMAL here — the repo has no .markdownlint*
# config so canonical docs carry a default-rule baseline), >=2 = engine /
# config crash, 127 = not installed (handled above). Parity with the sibling
# sst3-doc-links.sh capture-exit + crash-guard + unconditional sentinel.
set +e
RAW=$(markdownlint-cli2 "${GLOBS[@]}" 2>&1)
MDL_EXIT=$?
set -e

if [[ $MDL_EXIT -ne 0 && $MDL_EXIT -ne 1 ]]; then
    echo "ERROR: markdownlint-cli2 crashed (exit=$MDL_EXIT) — output is NOT a clean run" >&2
    echo "sst3-doc-lint: ENGINE CRASHED (exit=$MDL_EXIT) — do NOT treat as clean" >&2
    exit 2
fi

OUT=$(printf '%s\n' "$RAW" | { grep -E '^[^[:space:]]+:[0-9]+(:[0-9]+)? (error|warning) MD' || true; } | while IFS= read -r LINE; do
    FILE=$(echo "$LINE" | sed -E 's/^([^:]+):.*$/\1/')
    LN=$(echo "$LINE" | sed -E 's/^[^:]+:([0-9]+).*$/\1/')
    RULE=$(echo "$LINE" | grep -oE 'MD[0-9]+(/[a-z-]+)?' | head -1)
    DESC=$(echo "$LINE" | sed -E "s|^[^:]+:[0-9]+(:[0-9]+)? (error\|warning) MD[0-9]+(/[a-z-]+)? ||; s| \[Context: .*\]$||")
    jq -nc --arg f "$FILE" --argjson l "${LN:-0}" --arg r "${RULE:-unknown}" --arg d "$DESC" \
        '{file: $f, line: $l, rule: $r, description: $d}'
done)

[[ -n "$OUT" ]] && printf '%s\n' "$OUT"

# Stderr sentinel: always emitted, regardless of exit code, so consumers can
# distinguish "ran clean" (sentinel present, 0 findings) from "didn't run"
# (no sentinel / ENGINE CRASHED line). Parity with sst3-doc-links.sh:108.
N_PATHS=${#GLOBS[@]}
if [[ -n "$OUT" ]]; then
    N_FINDINGS=$(printf '%s\n' "$OUT" | grep -c .)
else
    N_FINDINGS=0
fi
echo "sst3-doc-lint: scanned $N_PATHS path(s), $N_FINDINGS finding(s)" >&2
exit 0
