#!/usr/bin/env bash
# sst3-code-review.sh — Composite diff-scoped review (replaces 4MB-JSON monolith).
#
# Usage:   sst3-code-review.sh <base-branch>
# Example: sst3-code-review.sh main
# Output:  NDJSON written to /tmp/review.ndjson chaining:
#            {section:"impact", changed_file, impacted_callers}
#            {section:"untested-in-diff", file, untested:[names]}
# Engines: composes sst3-code-impact.sh + sst3-code-untested-py.sh.

set -euo pipefail
export LC_ALL=C


SST3_EMITTED_COUNT="${SST3_EMITTED_COUNT:-0}"
on_sigterm() {
    if command -v jq >/dev/null 2>&1; then
        jq -nc --arg n "sst3-code-review" --argjson e "${SST3_EMITTED_COUNT:-0}" \
            '{kind:($n + "-killed"), reason:"sigterm", partial_records:$e}'
    else
        printf '{"kind":"%s-killed","reason":"sigterm","partial_records":%s}\n' \
            "sst3-code-review" "${SST3_EMITTED_COUNT:-0}"
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

# #447 Phase 3 (Shape 27): startup engine checks. Previously code-review.sh had
# zero — relied on inner wrappers exiting 127. The blanket `|| true` patterns
# below then conflated engine-missing with empty-result, hiding the diagnostic.
if ! command -v ast-grep >/dev/null 2>&1; then
    echo 'ERROR: ast-grep not installed (required by sst3-code-impact.sh); see dotfiles/docs/guides/code-query-playbook.md "Wrapper-Script Lane > Install"' >&2
    exit 127
fi
if ! command -v jq >/dev/null 2>&1; then
    echo 'ERROR: jq not installed; see dotfiles/docs/guides/code-query-playbook.md "Wrapper-Script Lane > Install"' >&2
    exit 127
fi

BASE="$1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# #447 Phase 3 (Shape 7): fixed `/tmp/review.ndjson` raced multi-shell. Default
# to mktemp; SST3_REVIEW_NDJSON overrides (test fixtures + deterministic dev).
OUT="${SST3_REVIEW_NDJSON:-$(mktemp -t sst3_review.XXXXXX.ndjson)}"

: > "$OUT"

# #447 Phase 3 (Shape 27): replaced blanket `|| true` with explicit per-step
# error capture. If sst3-code-impact.sh fails (engine-broken / SIGTERM), we
# emit a structured diagnostic instead of silently producing an empty review.
set +e
IMPACT_OUT=$(bash "$SCRIPT_DIR/sst3-code-impact.sh" "$BASE" 2>&1)
IMPACT_RC=$?
set -e
if [[ $IMPACT_RC -ne 0 ]]; then
    jq -nc --arg s "$IMPACT_OUT" --argjson rc "$IMPACT_RC" \
        '{section:"review-error", source:"sst3-code-impact", exit:$rc, stderr:$s}' >> "$OUT"
else
    printf '%s\n' "$IMPACT_OUT" | grep -v '^$' \
        | jq -c '. + {section: "impact"}' >> "$OUT"
fi

if [[ -f .coverage ]] && command -v coverage >/dev/null 2>&1; then
    CHANGED=$(git diff --name-only "${BASE}...HEAD" -- '*.py' 2>/dev/null || true)
    if [[ -n "$CHANGED" ]]; then
        set +e
        UNTESTED_OUT=$(bash "$SCRIPT_DIR/sst3-code-untested-py.sh" 2>&1)
        UNTESTED_RC=$?
        set -e
        if [[ $UNTESTED_RC -ne 0 ]]; then
            jq -nc --arg s "$UNTESTED_OUT" --argjson rc "$UNTESTED_RC" \
                '{section:"review-error", source:"sst3-code-untested-py", exit:$rc, stderr:$s}' >> "$OUT"
        else
            printf '%s\n' "$UNTESTED_OUT" | grep -v '^$' \
                | jq -c --arg changed "$CHANGED" '
                    . as $u |
                    ($changed | split("\n")) as $files |
                    select($u.file as $f | $files | index($f)) |
                    $u + {section: "untested-in-diff"}
                  ' >> "$OUT"
        fi
    fi
fi

echo "$OUT"
