#!/usr/bin/env bash
# sst3-sync-url-liveness.sh — URL liveness check (alias to sst3-doc-links.sh).
#
# Usage:   sst3-sync-url-liveness.sh [paths...]
# Default: SST3/ + docs/ + CLAUDE.md + README.md
# Output:  NDJSON, one object per failed URL: {file, url, status, error}
# Engine:  delegates to sst3-doc-links.sh (which wraps lychee).
# Note:    Provided as part of the sync-tooling lane for symmetry with the
#          other sst3-sync-*.sh wrappers; same engine + output shape as
#          sst3-doc-links.sh. Use whichever name reads better in your context.

set -euo pipefail
export LC_ALL=C


SST3_EMITTED_COUNT="${SST3_EMITTED_COUNT:-0}"
on_sigterm() {
    if command -v jq >/dev/null 2>&1; then
        jq -nc --arg n "sst3-sync-url-liveness" --argjson e "${SST3_EMITTED_COUNT:-0}" \
            '{kind:($n + "-killed"), reason:"sigterm", partial_records:$e}'
    else
        printf '{"kind":"%s-killed","reason":"sigterm","partial_records":%s}\n' \
            "sst3-sync-url-liveness" "${SST3_EMITTED_COUNT:-0}"
    fi
    exit 143
}
trap on_sigterm SIGTERM

WRAPPER_DIR="$(dirname "$(realpath "$0")")"
LINKS_WRAPPER="$WRAPPER_DIR/sst3-doc-links.sh"

if [[ ! -f "$LINKS_WRAPPER" ]]; then
    echo "ERROR: sst3-doc-links.sh not found at $LINKS_WRAPPER" >&2
    exit 127
fi

exec bash "$LINKS_WRAPPER" "$@"
