#!/usr/bin/env bash
# sst3-code-secrets.sh — Public-repo secret + private-token scanner.
#
# Usage:   sst3-code-secrets.sh --diff <base-branch> [--blocklist <path>]
#          sst3-code-secrets.sh --staged          [--blocklist <path>]
#          sst3-code-secrets.sh --file <path>     [--blocklist <path>]
#          sst3-code-secrets.sh --all             [--blocklist <path>]
# Output:  NDJSON, one object per match: {file, line, match_token, source, category}
#          source=blocklist|regex
#          category=shared|private-business|private-tradebook|public-marker|<other>
# Engines: git diff (mode-dependent) | grep -F -f <blocklist> for literal terms,
#          plus optional `gitleaks` if installed (regex layer).
#
# Rationale (#447 Phase 6): every public-repo push currently relies on the
# pre-commit hook `check-public-repo-secrets.py`. There is no
# request-scoped wrapper for ad-hoc audits ("does branch X contain blocked
# tokens?", "does the staging area leak anything?", "scan a single file in
# isolation"). This wrapper closes that gap with the canonical NDJSON
# contract so subagents can audit secret-leak risk on demand.

set -euo pipefail

export LC_ALL=C
SST3_EMITTED_COUNT=0
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

trap 'wrapper_sentinel "sst3-code-secrets" "$SST3_EMITTED_COUNT" "leak"; rm -f "${LITERAL_TMP:-}"' EXIT

SST3_EMITTED_COUNT="${SST3_EMITTED_COUNT:-0}"
on_sigterm() {
    if command -v jq >/dev/null 2>&1; then
        jq -nc --arg n "sst3-code-secrets" --argjson e "${SST3_EMITTED_COUNT:-0}" \
            '{kind:($n + "-killed"), reason:"sigterm", partial_records:$e}'
    else
        printf '{"kind":"%s-killed","reason":"sigterm","partial_records":%s}\n' \
            "sst3-code-secrets" "${SST3_EMITTED_COUNT:-0}"
    fi
    exit 143
}
trap on_sigterm SIGTERM


MODE=""
TARGET=""
BLOCKLIST_OVERRIDE=""
ARGS=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        --blocklist)
            BLOCKLIST_OVERRIDE="${2:-}"
            shift 2 || break
            ;;
        --diff|--staged|--file|--all)
            ARGS+=("$1")
            shift
            ;;
        *)
            ARGS+=("$1")
            shift
            ;;
    esac
done
set -- "${ARGS[@]}"

if [[ $# -lt 1 ]]; then
    echo "ERROR: usage: $(basename "$0") --diff <base> | --staged | --file <path> | --all  [--blocklist <path>]" >&2
    exit 64
fi

if ! command -v git >/dev/null 2>&1; then
    echo 'ERROR: git not installed; see dotfiles/docs/guides/code-query-playbook.md "Wrapper-Script Lane > Install"' >&2
    exit 127
fi
if ! command -v jq >/dev/null 2>&1; then
    echo 'ERROR: jq not installed; see dotfiles/docs/guides/code-query-playbook.md "Wrapper-Script Lane > Install"' >&2
    exit 127
fi

MODE="$1"
TARGET="${2:-}"

REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
BLOCKLIST=""
if [[ -n "$BLOCKLIST_OVERRIDE" ]]; then
    if [[ ! -r "$BLOCKLIST_OVERRIDE" ]]; then
        echo "ERROR: --blocklist path not readable: $BLOCKLIST_OVERRIDE" >&2
        exit 64
    fi
    BLOCKLIST="$BLOCKLIST_OVERRIDE"
elif [[ -r "$REPO_ROOT/.secret-blocklist" ]]; then
    BLOCKLIST="$REPO_ROOT/.secret-blocklist"
elif [[ -r "$REPO_ROOT/scripts/.secret-blocklist-canonical" ]]; then
    BLOCKLIST="$REPO_ROOT/scripts/.secret-blocklist-canonical"
else
    echo "ERROR: no .secret-blocklist, --blocklist override, or .secret-blocklist-canonical found" >&2
    exit 64
fi

# Build the literal-term list (strip comments, blank lines, section headers).
LITERAL_TMP=$(mktemp)
grep -vE '^\s*#|^\s*$|^\[' "$BLOCKLIST" > "$LITERAL_TMP" || true

if [[ ! -s "$LITERAL_TMP" ]]; then
    echo "WARN: blocklist resolved to empty literal-term list ($BLOCKLIST)" >&2
fi

# Section-categorise blocklist entries by section header. We re-scan the file
# carrying the active section forward so the NDJSON `category` field maps
# back to the [shared] / [private-business] / [private-tradebook] / etc. groupings.
classify_token() {
    local needle="$1"
    awk -v want="$needle" '
        /^\[/ { sect = substr($0, 2, length($0)-2); next }
        /^\s*#|^\s*$/ { next }
        $0 == want { print sect; exit }
    ' "$BLOCKLIST"
}

emit_match() {
    local file="$1"
    local line="$2"
    local token="$3"
    local source="$4"
    local cat
    cat=$(classify_token "$token")
    [[ -z "$cat" ]] && cat="unknown"
    jq -nc --arg f "$file" --argjson l "$line" --arg t "$token" --arg s "$source" --arg c "$cat" \
        '{file:$f, line:$l, match_token:$t, source:$s, category:$c}'
    SST3_EMITTED_COUNT=$((SST3_EMITTED_COUNT + 1))
}

# Scan a single text stream against the literal blocklist; emit one record
# per (line, blocked-token) hit. We use `grep -F -n -f` to surface line
# numbers + matched literals together.
scan_stream() {
    local label="$1"
    while IFS=: read -r line_no rest; do
        [[ -z "$line_no" || -z "$rest" ]] && continue
        # Find which blocked token matched (grep -F -o emits per-match).
        while IFS= read -r tok; do
            [[ -z "$tok" ]] && continue
            emit_match "$label" "$line_no" "$tok" "blocklist"
        done < <(printf '%s\n' "$rest" | grep -Fof "$LITERAL_TMP" -o 2>/dev/null || true)
    done
}

case "$MODE" in
    --diff)
        if [[ -z "$TARGET" ]]; then
            echo "ERROR: --diff requires <base-branch>" >&2
            exit 64
        fi
        # +-prefixed added lines only; preserve file headers.
        # shellcheck disable=SC2034
        CURRENT_FILE=""
        while IFS= read -r LINE; do
            if [[ "$LINE" =~ ^\+\+\+\ b/(.+)$ ]]; then
                CURRENT_FILE="${BASH_REMATCH[1]}"
                LINE_OFFSET=0
                continue
            fi
            if [[ "$LINE" =~ ^@@\ -[0-9]+(,[0-9]+)?\ \+([0-9]+) ]]; then
                LINE_OFFSET="${BASH_REMATCH[2]}"
                continue
            fi
            if [[ "$LINE" =~ ^\+[^+] ]]; then
                content="${LINE:1}"
                while IFS= read -r tok; do
                    [[ -z "$tok" ]] && continue
                    emit_match "${CURRENT_FILE:-unknown}" "${LINE_OFFSET:-0}" "$tok" "blocklist"
                done < <(printf '%s\n' "$content" | grep -Fof "$LITERAL_TMP" -o 2>/dev/null || true)
                LINE_OFFSET=$((LINE_OFFSET + 1))
            elif [[ "$LINE" =~ ^[\ -] ]]; then
                LINE_OFFSET=$((LINE_OFFSET + 1))
            fi
        done < <(git diff "${TARGET}...HEAD" 2>/dev/null || true)
        ;;
    --staged)
        # Staged diff vs index; use --cached to scan staged adds only.
        CURRENT_FILE=""
        while IFS= read -r LINE; do
            if [[ "$LINE" =~ ^\+\+\+\ b/(.+)$ ]]; then
                CURRENT_FILE="${BASH_REMATCH[1]}"
                LINE_OFFSET=0
                continue
            fi
            if [[ "$LINE" =~ ^@@\ -[0-9]+(,[0-9]+)?\ \+([0-9]+) ]]; then
                LINE_OFFSET="${BASH_REMATCH[2]}"
                continue
            fi
            if [[ "$LINE" =~ ^\+[^+] ]]; then
                content="${LINE:1}"
                while IFS= read -r tok; do
                    [[ -z "$tok" ]] && continue
                    emit_match "${CURRENT_FILE:-unknown}" "${LINE_OFFSET:-0}" "$tok" "blocklist"
                done < <(printf '%s\n' "$content" | grep -Fof "$LITERAL_TMP" -o 2>/dev/null || true)
                LINE_OFFSET=$((LINE_OFFSET + 1))
            elif [[ "$LINE" =~ ^[\ -] ]]; then
                LINE_OFFSET=$((LINE_OFFSET + 1))
            fi
        done < <(git diff --cached 2>/dev/null || true)
        ;;
    --file)
        if [[ -z "$TARGET" || ! -r "$TARGET" ]]; then
            echo "ERROR: --file requires a readable path" >&2
            exit 64
        fi
        while IFS= read -r RECORD; do
            [[ -z "$RECORD" ]] && continue
            line_no="${RECORD%%:*}"
            rest="${RECORD#*:}"
            while IFS= read -r tok; do
                [[ -z "$tok" ]] && continue
                emit_match "$TARGET" "$line_no" "$tok" "blocklist"
            done < <(printf '%s\n' "$rest" | grep -Fof "$LITERAL_TMP" -o 2>/dev/null || true)
        done < <(grep -Fnof "$LITERAL_TMP" "$TARGET" 2>/dev/null || true)
        ;;
    --all)
        # Walk tracked files; skip the blocklist file itself.
        while IFS= read -r FILE; do
            [[ ! -f "$FILE" ]] && continue
            [[ "$FILE" == *".secret-blocklist"* ]] && continue
            [[ "$FILE" == *".secret-allowlist"* ]] && continue
            while IFS= read -r RECORD; do
                [[ -z "$RECORD" ]] && continue
                line_no="${RECORD%%:*}"
                rest="${RECORD#*:}"
                while IFS= read -r tok; do
                    [[ -z "$tok" ]] && continue
                    emit_match "$FILE" "$line_no" "$tok" "blocklist"
                done < <(printf '%s\n' "$rest" | grep -Fof "$LITERAL_TMP" -o 2>/dev/null || true)
            done < <(grep -Fnof "$LITERAL_TMP" "$FILE" 2>/dev/null || true)
        done < <(git ls-files 2>/dev/null || true)
        ;;
    *)
        echo "ERROR: unknown mode: $MODE (expected --diff|--staged|--file|--all)" >&2
        exit 64
        ;;
esac
