#!/usr/bin/env bash
# KNOWN-BROKEN variant of sst3-doc-frontmatter.sh — EXIT-trap stderr sentinel removed.
# The active wrapper at scripts/sst3-doc-frontmatter.sh emits
# "sst3-doc-frontmatter: scanned N path(s), M invalid record(s)" on every
# exit path (#447 Phase 2 silent-zero fix). This variant strips that trap,
# so `doc-frontmatter-clean` fixture MUST flag the missing sentinel.
#
# Meta-validation: swap this file in, run sst3-self-test, expect non-zero.

set -euo pipefail

if ! command -v python3 >/dev/null 2>&1; then
    echo 'ERROR: python3 not installed; see dotfiles/docs/guides/code-query-playbook.md "Wrapper-Script Lane > Install"' >&2
    exit 127
fi

REQUIRED='domain type topics last_updated sources coverage'

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
        mapfile -t PATHS < <(find -P docs/research -name '*.md' -type f)
    else
        PATHS=()
    fi
else
    PATHS=("${ARGS[@]}")
fi

INVALID_COUNT=0
# NOTE: trap intentionally absent — that's the bug this variant ships.

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
