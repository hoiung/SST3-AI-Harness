#!/usr/bin/env bash
# sst3-code-coverage.sh — Line-level coverage projection for Python.
#
# Usage:   sst3-code-coverage.sh [<coverage_json_path>] [--paths-from <ndjson>]
# Output:  NDJSON, one object per source file:
#          {file, total_lines, covered_lines, missing_ranges:[[start,end]], coverage_pct}
# Engines: `coverage json` output (Python `coverage` package). Default
#          path: `.coverage.json` in CWD; overrides via positional arg.
#
# Rationale (#447 Phase 8): function-level untested-py exists; this is its
# line-level sibling. Subagents auditing test sufficiency need missing-line
# ranges to reason about uncovered branches.

set -euo pipefail

# shellcheck source=./sst3-bash-utils.sh
source "$(dirname "$0")/sst3-bash-utils.sh"
export LC_ALL=C
SST3_EMITTED_COUNT=0

on_sigterm() {
    jq -nc --arg n "sst3-code-coverage" --argjson e "$SST3_EMITTED_COUNT" \
        '{kind:($n + "-killed"), reason:"sigterm", partial_records:$e}'
    exit 143
}
trap on_sigterm SIGTERM

COVERAGE_JSON=""
PATHS_FROM=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --paths-from)
            PATHS_FROM="${2:-}"
            shift 2 || break
            ;;
        *)
            if [[ -z "$COVERAGE_JSON" ]]; then
                COVERAGE_JSON="$1"
            fi
            shift
            ;;
    esac
done

if [[ -z "$COVERAGE_JSON" ]]; then
    COVERAGE_JSON=".coverage.json"
fi

if ! command -v jq >/dev/null 2>&1; then
    echo 'ERROR: jq not installed; see dotfiles/docs/guides/code-query-playbook.md "Wrapper-Script Lane > Install"' >&2
    exit 127
fi
if ! command -v python3 >/dev/null 2>&1; then
    echo 'ERROR: python3 not installed; see dotfiles/docs/guides/code-query-playbook.md "Wrapper-Script Lane > Install"' >&2
    exit 127
fi

if [[ ! -r "$COVERAGE_JSON" ]]; then
    echo "ERROR: coverage.json not readable: $COVERAGE_JSON (run \`coverage json -o $COVERAGE_JSON\` first; cross-host WSL/Windows path: ensure path resolves on the host running this wrapper, see R4 Bug E)" >&2
    exit 64
fi

declare -a ALLOWED_PATHS=()
if [[ -n "$PATHS_FROM" ]]; then
    if [[ ! -r "$PATHS_FROM" ]]; then
        echo "ERROR: --paths-from file not readable: $PATHS_FROM" >&2
        exit 64
    fi
    while IFS= read -r p; do
        [[ -n "$p" ]] && ALLOWED_PATHS+=("$p")
    done < <(read_paths_from "$PATHS_FROM")
fi

# Filter NDJSON stream by `.file` membership in ALLOWED_PATHS.
# Empty ALLOWED_PATHS = pass-through. Mirrors activate_paths_from_filter
# from sst3-bash-utils.sh but applies AFTER python emits records (rather
# than via exec-redirect at top of script — coverage's python emitter is
# a single block, so post-pipe is cleaner than coprocess redirect).
path_allowed_filter() {
    if [[ ${#ALLOWED_PATHS[@]} -eq 0 ]]; then
        cat
    else
        local pattern
        pattern=$(printf '%s\n' "${ALLOWED_PATHS[@]}" | jq -Rsc 'split("\n")|map(select(length>0))')
        jq -c --argjson allowed "$pattern" \
            'select(.file as $f | $allowed | index($f) != null)'
    fi
}

# Stage 5 fix — capture emit count via tmp file (subshell scope lost SST3_EMITTED_COUNT
# when emission ran inside `python | filter` pipeline). Sentinel was always reporting 0.
TMP_OUT=$(mktemp)
trap 'rm -f "$TMP_OUT"; wrapper_sentinel "sst3-code-coverage" "$SST3_EMITTED_COUNT" "file"' EXIT

# coverage.json shape: {files: {<path>: {executed_lines:[], missing_lines:[], summary:{...}}}}
python3 - "$COVERAGE_JSON" <<'PY' | path_allowed_filter > "$TMP_OUT"
import sys, json
src = sys.argv[1]
with open(src) as fh:
    data = json.load(fh)
files = data.get('files', {})
def to_ranges(lines):
    if not lines:
        return []
    lines = sorted(set(lines))
    out = []
    start = prev = lines[0]
    for n in lines[1:]:
        if n == prev + 1:
            prev = n
        else:
            out.append([start, prev])
            start = prev = n
    out.append([start, prev])
    return out
for path, info in sorted(files.items()):
    executed = info.get('executed_lines') or []
    missing = info.get('missing_lines') or []
    total = len(executed) + len(missing)
    covered = len(executed)
    pct = round(100.0 * covered / total, 2) if total else 0.0
    rec = {
        "file": path,
        "total_lines": total,
        "covered_lines": covered,
        "missing_ranges": to_ranges(missing),
        "coverage_pct": pct,
    }
    print(json.dumps(rec, separators=(',', ':')))
PY

SST3_EMITTED_COUNT=$(wc -l < "$TMP_OUT")
cat "$TMP_OUT"

exit 0
