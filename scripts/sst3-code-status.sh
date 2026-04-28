#!/usr/bin/env bash
# sst3-code-status.sh — Audit-trail status (replaces the prior daemon-MCP `config status` invocation).
#
# Usage:   sst3-code-status.sh
# Output:  Single JSON object: {last_updated, file_count, source_languages}
#          last_updated      : ISO-8601 commit time of HEAD (`git log -1 --format=%cI`)
#          file_count        : count of supported source files (sum of per-language counts)
#          source_languages  : array of {lang, count} for languages actually present (count > 0)
# Engines: git, find, jq. All host pre-reqs per Phase 0.
#
# Note: this wrapper is stateless — every invocation re-counts. There is no
# persistent graph, no embeddings, no SQLite. `source_languages` is COMPUTED
# from on-disk file presence, not a hard-coded constant — per #445 R4 fix
# (was lying about ts/tsx existence on Python-only repos).

set -euo pipefail
export LC_ALL=C


SST3_EMITTED_COUNT="${SST3_EMITTED_COUNT:-0}"
on_sigterm() {
    if command -v jq >/dev/null 2>&1; then
        jq -nc --arg n "sst3-code-status" --argjson e "${SST3_EMITTED_COUNT:-0}" \
            '{kind:($n + "-killed"), reason:"sigterm", partial_records:$e}'
    else
        printf '{"kind":"%s-killed","reason":"sigterm","partial_records":%s}\n' \
            "sst3-code-status" "${SST3_EMITTED_COUNT:-0}"
    fi
    exit 143
}
trap on_sigterm SIGTERM

# `find` is a coreutils dependency assumed present. `jq` is the wrapper-lane
# JSON engine — fail-fast with stderr contract if missing. `git` is OPTIONAL
# here: if absent, last_updated falls back to "unknown" rather than failing,
# because the wrapper's primary purpose (scale + language counts) does not
# require git history.
if ! command -v jq >/dev/null 2>&1; then
    echo 'ERROR: jq not installed; see dotfiles/docs/guides/code-query-playbook.md "Wrapper-Script Lane > Install"' >&2
    exit 127
fi

LAST_UPDATED=$(git log -1 --format=%cI 2>/dev/null || echo "unknown")

EXTS=(py ts tsx js jsx gs rs sh sql yaml yml md toml json)
LANG_JSON='[]'
TOTAL=0
for ext in "${EXTS[@]}"; do
    n=$(find . -type f -name "*.${ext}" \
        -not -path '*/node_modules/*' \
        -not -path '*/.venv/*' \
        -not -path '*/target/*' \
        -not -path '*/.git/*' \
        -not -path '*/dist/*' \
        -not -path '*/build/*' \
        2>/dev/null | wc -l)
    if [ "$n" -gt 0 ]; then
        LANG_JSON=$(jq -c --arg l "$ext" --argjson c "$n" '. + [{lang:$l, count:$c}]' <<<"$LANG_JSON")
        TOTAL=$((TOTAL + n))
    fi
done

jq -nc \
    --arg lu "$LAST_UPDATED" \
    --argjson fc "$TOTAL" \
    --argjson sl "$LANG_JSON" \
    '{last_updated: $lu, file_count: $fc, source_languages: $sl}'
