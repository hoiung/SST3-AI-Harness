#!/usr/bin/env bash
# sst3-sync-related-code.sh — Frontmatter `related_code:` path drift detector.
#
# Usage:   sst3-sync-related-code.sh [paths...]
# Default: scans docs/research/**/*.md
# Output:  NDJSON, one object per drift case: {doc, line, claimed_path, exists}
# Engine:  python3 (PyYAML optional). No external engines required.
# Note:    This is the wrapper that would have caught Stage 5 finding 3 (the
#          AST_ANALYSIS.md L27 + L805 path drift) automatically.

set -euo pipefail
export LC_ALL=C

if ! command -v python3 >/dev/null 2>&1; then
    echo 'ERROR: python3 not installed; see dotfiles/docs/guides/code-query-playbook.md "Wrapper-Script Lane > Install"' >&2
    exit 127
fi

# #447 Phase 3: standardise arg parsing on the canonical case-loop pattern.
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
        # #447 Phase 3: -P prevents symlink-following.
        mapfile -t PATHS < <(find -P docs/research -name '*.md' -type f)
    else
        PATHS=()
    fi
else
    PATHS=("${ARGS[@]}")
fi

# Repo root for resolving paths cited in frontmatter
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
DEVPROJECTS_ROOT=$(dirname "$REPO_ROOT")

MISSING_COUNT=0

# Universal "I ran" sentinel — emit on every exit path (#447 Phase 2, silent-zero).
trap 'printf "sst3-sync-related-code: scanned %d path(s), %d missing path(s)\n" "${#PATHS[@]}" "${MISSING_COUNT:-0}" >&2' EXIT

SST3_EMITTED_COUNT="${SST3_EMITTED_COUNT:-0}"
on_sigterm() {
    if command -v jq >/dev/null 2>&1; then
        jq -nc --arg n "sst3-sync-related-code" --argjson e "${SST3_EMITTED_COUNT:-0}" \
            '{kind:($n + "-killed"), reason:"sigterm", partial_records:$e}'
    else
        printf '{"kind":"%s-killed","reason":"sigterm","partial_records":%s}\n' \
            "sst3-sync-related-code" "${SST3_EMITTED_COUNT:-0}"
    fi
    exit 143
}
trap on_sigterm SIGTERM

for FILE in "${PATHS[@]}"; do
    [[ -f "$FILE" ]] || continue
    # Symlink guard (security audit L1B): refuse to follow symlinks to avoid
    # path-traversal class (e.g. malicious symlink to /etc/shadow).
    if [[ -L "$FILE" ]]; then
        echo "WARN: skipping symlink $FILE (sst3-sync-related-code refuses to follow symlinks)" >&2
        continue
    fi
    OUT=$(python3 - "$FILE" "$DEVPROJECTS_ROOT" <<'EOF'
import sys, os, re, json
file_path, dp_root = sys.argv[1], sys.argv[2]
try:
    with open(file_path) as f:
        content = f.read()
except OSError:
    sys.exit(0)
# Match YAML frontmatter at file start OR after a heading prelude.
# Both forms found in dotfiles/docs/research/.
fm = None
fm_start_line = 0
m = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
if m:
    fm = m.group(1)
    fm_start_line = 1
else:
    # Search for a YAML block delimited by --- elsewhere in the file
    for sm in re.finditer(r'(?m)^---\s*$', content):
        start = sm.end()
        em = re.search(r'(?m)^---\s*$', content[start:])
        if em:
            fm = content[start:start+em.start()]
            fm_start_line = content[:sm.start()].count('\n') + 2
            break
if not fm:
    sys.exit(0)
in_block = False
for i, line in enumerate(fm.split('\n'), start=fm_start_line):
    s = line.rstrip()
    if re.match(r'^related_code\s*:\s*$', s):
        in_block = True
        continue
    if in_block:
        m2 = re.match(r'^\s+-\s+file:\s*(\S.*)$', s)
        if m2:
            cited = m2.group(1).strip().strip('"\'')
            full = os.path.join(dp_root, cited)
            print(json.dumps({"doc": file_path, "line": i, "claimed_path": cited, "exists": os.path.exists(full)}))
        elif re.match(r'^[a-z_]+\s*:', s):
            in_block = False
EOF
) || true
    [[ -n "$OUT" ]] && echo "$OUT"
    if [[ "$STRICT" -eq 1 ]] && echo "$OUT" | grep -q '"exists": false'; then
        MISSING_COUNT=$((MISSING_COUNT + 1))
    fi
done

[[ "$STRICT" -eq 1 ]] && [[ "$MISSING_COUNT" -gt 0 ]] && exit 1
exit 0
