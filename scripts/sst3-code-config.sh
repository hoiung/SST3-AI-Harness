#!/usr/bin/env bash
# sst3-code-config.sh — Code-to-config key tracing.
#
# Usage:   sst3-code-config.sh [--paths-from <ndjson>]
# Output:  NDJSON, one object per config key:
#          {key, defined_in:[paths], read_at:[{file,line}], unused_def, undef_read}
#          unused_def: true if key appears in YAML/TOML/.env but never read
#          undef_read: true if read_at exists but defined_in is empty
# Engines: ast-grep (Python `os.environ[$KEY]`, `os.getenv($KEY)`,
#          `config.get($KEY)`) + grep over .yaml/.yml/.toml/.env.
#
# Rationale (#447 Phase 8): the existing sync-doc-to-code wrapper checks
# doc-side coverage. This is the inverse — every config key the code reads,
# matched against where the value is defined. Surfaces dead config + un-defined
# reads in one pass.

set -euo pipefail

# shellcheck source=./sst3-bash-utils.sh
source "$(dirname "$0")/sst3-bash-utils.sh"
export LC_ALL=C
SST3_EMITTED_COUNT=0

on_sigterm() {
    jq -nc --arg n "sst3-code-config" --argjson e "$SST3_EMITTED_COUNT" \
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
if ! command -v jq >/dev/null 2>&1; then
    echo 'ERROR: jq not installed; see dotfiles/docs/guides/code-query-playbook.md "Wrapper-Script Lane > Install"' >&2
    exit 127
fi
if ! command -v rg >/dev/null 2>&1; then
    echo 'ERROR: ripgrep not installed; see dotfiles/docs/guides/code-query-playbook.md "Wrapper-Script Lane > Install"' >&2
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

# 1) Collect READ sites: {key -> [(file, line), ...]}
READS=$(mktemp)
DEFS=$(mktemp)
# Consolidated EXIT trap (Stage 5 fix — was overwriting wrapper_sentinel trap from line 24).
trap 'rm -f "$READS" "$DEFS"; wrapper_sentinel "sst3-code-config" "$SST3_EMITTED_COUNT" "config-key"' EXIT
trap 'rm -f "$READS" "$DEFS"' INT TERM

PATTERNS=(
    "os.environ[\$KEY]"
    "os.environ.get(\$KEY)"
    "os.getenv(\$KEY)"
    "config.get(\$KEY)"
)

for pattern in "${PATTERNS[@]}"; do
    while IFS= read -r record; do
        [[ -z "$record" ]] && continue
        file=$(jq -r '.file // ""' <<< "$record")
        line=$(jq -r '.range.start.line // 0' <<< "$record")
        key=$(jq -r '.metaVariables.single.KEY.text // ""' <<< "$record")
        # Strip surrounding quotes from string-literal keys
        key=$(printf '%s' "$key" | sed -e 's/^["'\'']//' -e 's/["'\'']$//')
        [[ -z "$file" || -z "$key" ]] && continue
        path_allowed "$file" || continue
        printf '%s\t%s\t%s\n' "$key" "$file" "$line" >> "$READS"
    done < <(ast-grep run --pattern "$pattern" --lang python --json=stream 2>/dev/null || true)
done

# 2) Collect DEFINED keys from .yaml/.yml/.toml/.env files. Heuristic — we
# treat top-level scalar keys + .env KEY=val lines as definitions.
while IFS= read -r f; do
    [[ ! -f "$f" ]] && continue
    case "$f" in
        *.env|*.env.*)
            while IFS= read -r line; do
                [[ "$line" =~ ^[[:space:]]*# ]] && continue
                # Stage 5 fix (D3) — broaden from `^[A-Z_][A-Z0-9_]*` so lowercase
                # + dot + dash keys (e.g. `database_url`, `MY-KEY.X`) correlate.
                if [[ "$line" =~ ^([A-Za-z_][A-Za-z0-9_.-]*)= ]]; then
                    printf '%s\t%s\n' "${BASH_REMATCH[1]}" "$f" >> "$DEFS"
                fi
            done < "$f"
            ;;
        *.yaml|*.yml)
            grep -E '^[[:space:]]*[A-Za-z_][A-Za-z0-9_]*[[:space:]]*:' "$f" 2>/dev/null \
                | sed -E 's/^[[:space:]]*([A-Za-z_][A-Za-z0-9_]*)[[:space:]]*:.*/\1/' \
                | awk -v src="$f" '{print $0 "\t" src}' >> "$DEFS"
            ;;
        *.toml)
            grep -E '^[[:space:]]*[A-Za-z_][A-Za-z0-9_]*[[:space:]]*=' "$f" 2>/dev/null \
                | sed -E 's/^[[:space:]]*([A-Za-z_][A-Za-z0-9_]*)[[:space:]]*=.*/\1/' \
                | awk -v src="$f" '{print $0 "\t" src}' >> "$DEFS"
            ;;
    esac
done < <(find . -maxdepth 5 -type f \( -name '*.yaml' -o -name '*.yml' -o -name '*.toml' -o -name '*.env' -o -name '.env' \) \
    -not -path './.git/*' -not -path '*/node_modules/*' -not -path '*/target/*' 2>/dev/null)

# 3) Aggregate: every unique key seen in either READS or DEFS gets one record.
ALL_KEYS=$( { cut -f1 "$READS"; cut -f1 "$DEFS"; } | sort -u )

while IFS= read -r key; do
    [[ -z "$key" ]] && continue
    defined_in=$(awk -F'\t' -v k="$key" '$1 == k {print $2}' "$DEFS" | sort -u | jq -Rcs 'split("\n")|map(select(length>0))')
    read_at=$(awk -F'\t' -v k="$key" '$1 == k {print $2"|"$3}' "$READS" \
        | jq -Rcs 'split("\n")
            | map(select(length>0))
            | map(split("|"))
            | map({file: .[0], line: (.[1]|tonumber? // 0)})')
    [[ -z "$defined_in" ]] && defined_in='[]'
    [[ -z "$read_at" ]] && read_at='[]'
    unused_def=$(jq -n --argjson d "$defined_in" --argjson r "$read_at" \
        '($d|length) > 0 and ($r|length) == 0')
    undef_read=$(jq -n --argjson d "$defined_in" --argjson r "$read_at" \
        '($d|length) == 0 and ($r|length) > 0')
    jq -nc --arg k "$key" --argjson d "$defined_in" --argjson r "$read_at" \
        --argjson ud "$unused_def" --argjson ur "$undef_read" \
        '{key:$k, defined_in:$d, read_at:$r, unused_def:$ud, undef_read:$ur}'
    SST3_EMITTED_COUNT=$((SST3_EMITTED_COUNT + 1))
done <<< "$ALL_KEYS"

exit 0
