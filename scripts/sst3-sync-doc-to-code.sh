#!/usr/bin/env bash
# sst3-sync-doc-to-code.sh — Verify doc claims about code identifiers exist.
#
# Usage:   sst3-sync-doc-to-code.sh <doc-file> [<lang>]
# Default lang: python
# Output:  NDJSON, one object per code-identifier claim: {doc, line, identifier, exists}
# Engine:  composes sst3-code-search.sh. Exit 127 if that wrapper missing.
# Note:    Heuristic — extracts backtick-quoted snake_case / camelCase / PascalCase
#          identifiers from doc prose and verifies each has at least one match in code.
#
# #445 R4 Bug G: pre-fix FP rate was 45% (9/20 on auto_pb CLAUDE.md were
# Python builtins, JS files, PG config keys, third-party libs, tool params).
# Now applies a 4-source allowlist: (1) Python builtins + keywords (computed),
# (2) file-extension regex (.js, .ts, .yaml, etc.), (3) pyproject.toml
# `[project.dependencies]` (computed), (4) curated static list at
# `dotfiles/standards/doc-to-code-allowlist.txt` (PostgreSQL GUCs,
# MCP tool params, harness vocab). Allowlisted tokens are SKIPPED — not
# emitted with `exists:true` — to keep output focused on real drift.

set -euo pipefail
export LC_ALL=C


SST3_EMITTED_COUNT="${SST3_EMITTED_COUNT:-0}"
on_sigterm() {
    if command -v jq >/dev/null 2>&1; then
        jq -nc --arg n "sst3-sync-doc-to-code" --argjson e "${SST3_EMITTED_COUNT:-0}" \
            '{kind:($n + "-killed"), reason:"sigterm", partial_records:$e}'
    else
        printf '{"kind":"%s-killed","reason":"sigterm","partial_records":%s}\n' \
            "sst3-sync-doc-to-code" "${SST3_EMITTED_COUNT:-0}"
    fi
    exit 143
}
trap on_sigterm SIGTERM

if [[ $# -lt 1 ]]; then
    echo "ERROR: usage: $(basename "$0") <doc-file> [<lang>]" >&2
    exit 64
fi

DOC="$1"
LANG="${2:-python}"

WRAPPER_DIR="$(dirname "$(realpath "$0")")"
SEARCH_WRAPPER="$WRAPPER_DIR/sst3-code-search.sh"
ALLOWLIST_FILE="$WRAPPER_DIR/../standards/doc-to-code-allowlist.txt"

if [[ ! -x /bin/bash ]] || [[ ! -f "$SEARCH_WRAPPER" ]]; then
    echo "ERROR: sst3-code-search.sh not found at $SEARCH_WRAPPER" >&2
    exit 127
fi

if [[ ! -f "$DOC" ]]; then
    echo "ERROR: doc file not found: $DOC" >&2
    exit 64
fi

# Build allowlist: builtins + curated file + pyproject deps.
ALLOW=""
if command -v python3 >/dev/null 2>&1; then
    ALLOW=$(python3 -c "import builtins, keyword; print('\n'.join(set(dir(builtins)) | set(keyword.kwlist)))" 2>/dev/null || true)
fi
if [[ -f "$ALLOWLIST_FILE" ]]; then
    ALLOW="${ALLOW}"$'\n'"$(grep -vE '^\s*(#|$)' "$ALLOWLIST_FILE" || true)"
fi
if [[ -f pyproject.toml ]] && command -v python3 >/dev/null 2>&1; then
    DEPS=$(python3 -c "
import re, sys
try:
    import tomllib
except ImportError:
    sys.exit(0)
import pathlib
try:
    d = tomllib.loads(pathlib.Path('pyproject.toml').read_text())
except Exception:
    sys.exit(0)
deps = d.get('project', {}).get('dependencies', [])
opt = d.get('project', {}).get('optional-dependencies', {})
for vals in opt.values():
    deps.extend(vals)
for x in deps:
    name = re.split(r'[<>=!~\[\s]', x, 1)[0]
    print(name)
    print(name.replace('-', '_'))
" 2>/dev/null || true)
    ALLOW="${ALLOW}"$'\n'"$DEPS"
fi

# Extract `identifier` patterns from backticks. Filter to plausible code identifiers
# (snake_case_with_underscores OR CamelCase OR mixed_with_dots).
LN=0
while IFS= read -r LINE; do
    LN=$((LN + 1))
    # Find all `...` snippets
    while IFS= read -r SNIPPET; do
        # Skip non-Python file references (.js, .ts, .yaml, etc.) — wrong language scope.
        if [[ "$SNIPPET" =~ \.(js|ts|jsx|tsx|md|html|css|ya?ml|json|toml|sh|rs|sql)$ ]]; then
            continue
        fi
        # Skip allowlisted tokens (builtins / curated / pyproject deps).
        if [[ -n "$ALLOW" ]] && grep -Fxq "$SNIPPET" <<<"$ALLOW"; then
            continue
        fi
        # Plausible identifier filter: 3+ chars, contains underscore OR mixed-case OR dot-method
        if [[ "$SNIPPET" =~ ^[a-zA-Z_][a-zA-Z0-9_.]*[a-z][A-Z][a-zA-Z0-9_.]*$|^[a-z]+_[a-z_]+$|^[A-Z][a-zA-Z]+[A-Z][a-zA-Z]+$ ]]; then
            # Count matches in code via search wrapper (literal mode for speed).
            # `</dev/null` is critical: the outer `while ... done < "$DOC"` loop
            # redirects stdin from the doc file, and inner subshells inherit it.
            # ripgrep with non-TTY stdin reads stdin-as-input instead of the
            # filesystem, returning 0 matches for everything (false negatives
            # for every real identifier). The </dev/null disconnects subshell
            # stdin so rg falls back to filesystem search. Bug surfaced by
            # #445 R4 Sonnet-Ralph review.
            COUNT=$(bash "$SEARCH_WRAPPER" "$SNIPPET" "$LANG" --literal </dev/null 2>/dev/null | wc -l)
            EXISTS=$([ "$COUNT" -gt 0 ] && echo true || echo false)
            jq -nc --arg d "$DOC" --argjson l "$LN" --arg id "$SNIPPET" --argjson e "$EXISTS" \
                '{doc: $d, line: $l, identifier: $id, exists: $e}'
        fi
    done < <(echo "$LINE" | grep -oE '`[^`]+`' | tr -d '`' || true)
done < "$DOC" || true
