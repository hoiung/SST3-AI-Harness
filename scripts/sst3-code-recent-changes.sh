#!/usr/bin/env bash
# sst3-code-recent-changes.sh — Files changed in a recent time window.
#
# Usage:   sst3-code-recent-changes.sh <since> [<paths>...]
# Example: sst3-code-recent-changes.sh '2 weeks ago'
#          sst3-code-recent-changes.sh '2026-04-20' SST3/scripts
# Output:  NDJSON, one object per (file, commit): {file, last_commit, author, sha, lines_changed}
# Engine:  git log --since=<since> --name-only --numstat --format=...
#
# Rationale (#447 Phase 6): incident response and regression hunts currently
# rely on ad-hoc `git log` scrapes. This wrapper produces a stable NDJSON
# contract so subagents can ingest "what changed recently in <area>" without
# crafting bespoke git invocations each time.

set -euo pipefail

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
    echo "ERROR: usage: $(basename "$0") <since> [<paths>...]" >&2
    exit 64
fi

SINCE="$1"
shift
PATHS=("$@")

export LC_ALL=C
SST3_EMITTED_COUNT=0

if ! command -v git >/dev/null 2>&1; then
    echo 'ERROR: git not installed; see dotfiles/docs/guides/code-query-playbook.md "Wrapper-Script Lane > Install"' >&2
    exit 127
fi
if ! command -v jq >/dev/null 2>&1; then
    echo 'ERROR: jq not installed; see dotfiles/docs/guides/code-query-playbook.md "Wrapper-Script Lane > Install"' >&2
    exit 127
fi

# EXIT-trap sentinel — the silent-zero guard. Without this, "no commits in
# window" produced exit 0 + no stderr, indistinguishable from "wrapper crashed
# before emitting".
trap 'wrapper_sentinel "sst3-code-recent-changes" "$SST3_EMITTED_COUNT" "change"' EXIT

SST3_EMITTED_COUNT="${SST3_EMITTED_COUNT:-0}"
on_sigterm() {
    if command -v jq >/dev/null 2>&1; then
        jq -nc --arg n "sst3-code-recent-changes" --argjson e "${SST3_EMITTED_COUNT:-0}" \
            '{kind:($n + "-killed"), reason:"sigterm", partial_records:$e}'
    else
        printf '{"kind":"%s-killed","reason":"sigterm","partial_records":%s}\n' \
            "sst3-code-recent-changes" "${SST3_EMITTED_COUNT:-0}"
    fi
    exit 143
}
trap on_sigterm SIGTERM


# Build the git log argv. --numstat emits per-file added/deleted line counts;
# --format injects a sentinel line we parse below to anchor commit metadata.
GIT_ARGS=(log --since="$SINCE" --no-merges --numstat --format='__SST3_COMMIT__%H%x09%an%x09%ad' --date=iso-strict)
if [[ ${#PATHS[@]} -gt 0 ]]; then
    GIT_ARGS+=(-- "${PATHS[@]}")
fi

# Parse with awk: track current commit metadata, emit one record per
# (file, commit) pair with added+deleted aggregated to lines_changed.
# Process substitution (NOT pipe-into-while) keeps the increment in the
# parent shell so the EXIT-trap sentinel reports the real emitted count.
while IFS= read -r RECORD; do
    echo "$RECORD"
    SST3_EMITTED_COUNT=$((SST3_EMITTED_COUNT + 1))
done < <(git "${GIT_ARGS[@]}" 2>/dev/null | awk '
    BEGIN { sha=""; author=""; date=""; }
    /^__SST3_COMMIT__/ {
        line = substr($0, 18)
        n = split(line, parts, "\t")
        sha = parts[1]; author = parts[2]; date = parts[3]
        next
    }
    NF == 3 && $1 ~ /^[0-9-]+$/ && $2 ~ /^[0-9-]+$/ {
        added = ($1 == "-") ? 0 : $1
        deleted = ($2 == "-") ? 0 : $2
        lines = added + deleted
        file = $3
        gsub(/[\\"]/, "_", file)
        gsub(/[\\"]/, "_", author)
        printf "{\"file\":\"%s\",\"last_commit\":\"%s\",\"author\":\"%s\",\"sha\":\"%s\",\"lines_changed\":%d}\n", file, date, author, sha, lines
    }
')
