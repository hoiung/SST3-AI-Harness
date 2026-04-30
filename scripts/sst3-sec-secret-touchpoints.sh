#!/usr/bin/env bash
# sst3-sec-secret-touchpoints.sh — Surface every secret/credential touchpoint.
#
# Usage:   sst3-sec-secret-touchpoints.sh [--paths-from <ndjson>]
# Output:  NDJSON, one object per touchpoint: {file, line, kind, identifier}
#          kind: env_read | dotenv_load | password_literal | aws_access_key | aws_secret_key
#          identifier: the env-var name, dotenv path, or token (truncated)
# Engines: ast-grep (Python env_read / dotenv_load) + ripgrep (regex literals)
#
# Rationale (#447 Phase 8): the current secrets wrapper (sst3-code-secrets.sh)
# scans against a literal blocklist. This wrapper is upstream of that — it
# enumerates every CALL SITE that touches a secret / credential / env-var,
# regardless of whether the value itself leaked. Auditors use it to verify
# the secret-handling surface area before each release.

set -euo pipefail

# shellcheck source=./sst3-bash-utils.sh
source "$(dirname "$0")/sst3-bash-utils.sh"
export LC_ALL=C
SST3_EMITTED_COUNT=0

trap 'wrapper_sentinel "sst3-sec-secret-touchpoints" "$SST3_EMITTED_COUNT" "touchpoint"' EXIT
on_sigterm() {
    jq -nc --arg n "sst3-sec-secret-touchpoints" --argjson e "$SST3_EMITTED_COUNT" \
        '{kind:($n + "-killed"), reason:"sigterm", partial_records:$e}'
    exit 143
}
trap on_sigterm SIGTERM

PATHS_FROM=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --paths-from)
            PATHS_FROM="${2:-}"
            shift 2 || break
            ;;
        *)
            shift
            ;;
    esac
done

if ! command -v ast-grep >/dev/null 2>&1; then
    echo 'ERROR: ast-grep not installed; see dotfiles/docs/guides/code-query-playbook.md "Wrapper-Script Lane > Install"' >&2
    exit 127
fi
if ! command -v rg >/dev/null 2>&1; then
    echo 'ERROR: ripgrep not installed; see dotfiles/docs/guides/code-query-playbook.md "Wrapper-Script Lane > Install"' >&2
    exit 127
fi
if ! command -v jq >/dev/null 2>&1; then
    echo 'ERROR: jq not installed; see dotfiles/docs/guides/code-query-playbook.md "Wrapper-Script Lane > Install"' >&2
    exit 127
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
path_allowed() {
    local file="$1"
    [[ ${#ALLOWED_PATHS[@]} -eq 0 ]] && return 0
    for allowed in "${ALLOWED_PATHS[@]}"; do
        [[ "$file" == "$allowed" || "$file" == "./$allowed" ]] && return 0
    done
    return 1
}

emit_record() {
    local file="$1" line="$2" kind="$3" ident="$4"
    if path_allowed "$file"; then
        jq -nc --arg f "$file" --argjson l "$line" --arg k "$kind" --arg i "$ident" \
            '{file:$f, line:$l, kind:$k, identifier:$i}'
        SST3_EMITTED_COUNT=$((SST3_EMITTED_COUNT + 1))
    fi
}

# 1) ast-grep — Python env reads.
PY_PATTERNS=(
    "env_read|os.environ[\$KEY]"
    "env_read|os.environ.get(\$KEY)"
    "env_read|os.getenv(\$KEY)"
    "dotenv_load|dotenv.load_dotenv(\$\$\$)"
    "dotenv_load|load_dotenv(\$\$\$)"
)

for spec in "${PY_PATTERNS[@]}"; do
    IFS='|' read -r kind pattern <<< "$spec"
    while IFS= read -r record; do
        [[ -z "$record" ]] && continue
        file=$(jq -r '.file // ""' <<< "$record")
        line=$(jq -r '.range.start.line // 0' <<< "$record")
        ident=$(jq -r '.metaVariables.single.KEY.text // ""' <<< "$record")
        [[ -z "$file" ]] && continue
        emit_record "$file" "$line" "$kind" "$ident"
    done < <(ast-grep run --pattern "$pattern" --lang python --json=stream 2>/dev/null || true)
done

# 2) ripgrep — literal patterns. We enumerate matches with --json so we get
# file + line. Each pattern gets its own kind.
declare -a RG_RULES=(
    'password_literal|password\s*=\s*["\x27][^"\x27]+["\x27]'
    'aws_access_key|AKIA[0-9A-Z]{16}'
    'aws_secret_key|aws_secret_access_key\s*=\s*["\x27][^"\x27]+["\x27]'
)

for rule in "${RG_RULES[@]}"; do
    IFS='|' read -r kind regex <<< "$rule"
    while IFS= read -r json_line; do
        [[ -z "$json_line" ]] && continue
        type=$(jq -r '.type' <<< "$json_line" 2>/dev/null || echo "")
        [[ "$type" != "match" ]] && continue
        file=$(jq -r '.data.path.text // empty' <<< "$json_line")
        line=$(jq -r '.data.line_number' <<< "$json_line")
        match=$(jq -r '.data.submatches[0].match.text // ""' <<< "$json_line")
        # Truncate the match to keep the NDJSON small.
        ident="${match:0:60}"
        [[ -n "$file" && -n "$line" ]] && emit_record "$file" "$line" "$kind" "$ident"
    done < <(rg --json -e "$regex" --no-messages 2>/dev/null || true)
done

exit 0
