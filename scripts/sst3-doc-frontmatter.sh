#!/usr/bin/env bash
# sst3-doc-frontmatter.sh — Frontmatter presence + required-fields validator.
#
# Usage:   sst3-doc-frontmatter.sh [paths...]
# Default: scans docs/research/**/*.md
# Output:  NDJSON, one object per file: {file, has_frontmatter, missing_fields, valid}
# Engine:  python3 + PyYAML (preferred) OR awk fallback. Required fields per
#          docs/research/ convention: domain, type, topics, last_updated, sources, coverage.
# Note:    Reports both presence (has_frontmatter) and required-field coverage.

set -euo pipefail
export LC_ALL=C

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

if ! command -v python3 >/dev/null 2>&1; then
    echo 'ERROR: python3 not installed; see dotfiles/docs/guides/code-query-playbook.md "Wrapper-Script Lane > Install"' >&2
    exit 127
fi

REQUIRED='domain type topics last_updated sources coverage'

# #447 Phase 3: standardise arg parsing on the canonical case-loop pattern
# (already used in sst3-code-callees.sh:34-39). Replaces the prior
# positional-only `if [[ "${1:-}" == "--strict" ]]` check that broke when
# --strict was passed second or in any other position.
STRICT=0
ARGS=()
for arg in "$@"; do
    case "$arg" in
        --strict) STRICT=1 ;;
        *) ARGS+=("$arg") ;;
    esac
done

if [[ ${#ARGS[@]} -eq 0 ]]; then
    if [[ -d docs/research ]]; then
        # #447 Phase 3: -P prevents symlink-following (defensive against any
        # malicious symlink in docs/research/).
        mapfile -t PATHS < <(find -P docs/research -name '*.md' -type f)
    else
        PATHS=()
    fi
else
    PATHS=("${ARGS[@]}")
fi

INVALID_COUNT=0

# Universal "I ran" sentinel — emit on every exit path (#447 Phase 2, silent-zero
# class fix). Without this, a missing docs/research/ directory (or zero matches)
# produced exit 0 + no stderr, indistinguishable from "all valid".
trap 'printf "sst3-doc-frontmatter: scanned %d path(s), %d invalid record(s)\n" "${#PATHS[@]}" "${INVALID_COUNT:-0}" >&2' EXIT

SST3_EMITTED_COUNT="${SST3_EMITTED_COUNT:-0}"
on_sigterm() {
    if command -v jq >/dev/null 2>&1; then
        jq -nc --arg n "sst3-doc-frontmatter" --argjson e "${SST3_EMITTED_COUNT:-0}" \
            '{kind:($n + "-killed"), reason:"sigterm", partial_records:$e}'
    else
        printf '{"kind":"%s-killed","reason":"sigterm","partial_records":%s}\n' \
            "sst3-doc-frontmatter" "${SST3_EMITTED_COUNT:-0}"
    fi
    exit 143
}
trap on_sigterm SIGTERM

for FILE in "${PATHS[@]}"; do
    [[ -f "$FILE" ]] || continue
    OUT=$(python3 - "$FILE" "$REQUIRED" <<'EOF'
import sys, json, re
file_path, required = sys.argv[1], sys.argv[2].split()
try:
    with open(file_path) as f:
        content = f.read()
except OSError:
    print(json.dumps({"file": file_path, "has_frontmatter": False, "missing_fields": required, "valid": False, "error": "read_failed"}))
    sys.exit(0)
m = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
if not m:
    print(json.dumps({"file": file_path, "has_frontmatter": False, "missing_fields": required, "valid": False}))
    sys.exit(0)
fm = m.group(1)
present = set(re.findall(r'^([a-z_][a-z_0-9]*)\s*:', fm, re.MULTILINE))
missing = [f for f in required if f not in present]
print(json.dumps({"file": file_path, "has_frontmatter": True, "missing_fields": missing, "valid": len(missing) == 0}))
EOF
) || true
    echo "$OUT"
    if [[ "$STRICT" -eq 1 ]] && echo "$OUT" | grep -q '"valid": false'; then
        INVALID_COUNT=$((INVALID_COUNT + 1))
    fi
done

[[ "$STRICT" -eq 1 ]] && [[ "$INVALID_COUNT" -gt 0 ]] && exit 1
exit 0
