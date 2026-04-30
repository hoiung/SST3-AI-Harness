#!/usr/bin/env bash
# sst3-dep-list.sh — Enumerate every declared dependency across ecosystems.
#
# Usage:   sst3-dep-list.sh [--paths-from <ndjson>]
# Output:  NDJSON, one object per declared dependency:
#          {ecosystem, name, version_constraint, source}
#          ecosystem: python | rust | javascript
#          source: relative path of manifest the dep was read from
# Engines: python3 (tomllib) for pyproject.toml + Cargo.toml; jq for package.json.
#
# Rationale (#447 Phase 8): unblocks dep-upgrade scenarios. The current
# `sst3-sync-doc-to-code.sh` parses pyproject.toml deps as an allowlist for
# a different reason (doc cross-link freshness). This wrapper exposes the
# same parser as a primary contract.

set -euo pipefail

# shellcheck source=./sst3-bash-utils.sh
source "$(dirname "$0")/sst3-bash-utils.sh"
export LC_ALL=C
SST3_EMITTED_COUNT=0

trap 'wrapper_sentinel "sst3-dep-list" "$SST3_EMITTED_COUNT" "dep"' EXIT
on_sigterm() {
    jq -nc --arg n "sst3-dep-list" --argjson e "$SST3_EMITTED_COUNT" \
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

if ! command -v jq >/dev/null 2>&1; then
    echo 'ERROR: jq not installed; see dotfiles/docs/guides/code-query-playbook.md "Wrapper-Script Lane > Install"' >&2
    exit 127
fi
if ! command -v python3 >/dev/null 2>&1; then
    echo 'ERROR: python3 not installed; see dotfiles/docs/guides/code-query-playbook.md "Wrapper-Script Lane > Install"' >&2
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
    local ecosystem="$1" name="$2" constraint="$3" source="$4"
    if path_allowed "$source"; then
        jq -nc --arg e "$ecosystem" --arg n "$name" --arg c "$constraint" --arg s "$source" \
            '{ecosystem:$e, name:$n, version_constraint:$c, source:$s}'
        SST3_EMITTED_COUNT=$((SST3_EMITTED_COUNT + 1))
    fi
}

# --- Python: pyproject.toml ---
parse_pyproject() {
    local path="$1"
    python3 - "$path" <<'PY'
import sys, re
p = sys.argv[1]
try:
    import tomllib
except ImportError:
    sys.exit(0)
import pathlib
try:
    d = tomllib.loads(pathlib.Path(p).read_text())
except Exception:
    sys.exit(0)
proj = d.get('project', {})
deps = list(proj.get('dependencies', []))
for vals in proj.get('optional-dependencies', {}).values():
    deps.extend(vals)
for raw in deps:
    parts = re.split(r'(?P<op>[<>=!~])', raw, maxsplit=1)
    name = parts[0].strip()
    constraint = ''
    if len(parts) > 1:
        constraint = ''.join(parts[1:]).strip()
    name = re.split(r'\[|\s', name, 1)[0]
    print(f"{name}\t{constraint}")
PY
}

while IFS= read -r -d '' f; do
    while IFS=$'\t' read -r name constraint; do
        [[ -z "$name" ]] && continue
        emit_record "python" "$name" "$constraint" "$f"
    done < <(parse_pyproject "$f")
done < <(find . -maxdepth 4 -type f -name pyproject.toml \
    -not -path './.git/*' -not -path '*/node_modules/*' -print0 2>/dev/null)

# --- Rust: Cargo.toml ---
parse_cargo() {
    local path="$1"
    python3 - "$path" <<'PY'
import sys, pathlib
p = sys.argv[1]
try:
    import tomllib
except ImportError:
    sys.exit(0)
try:
    d = tomllib.loads(pathlib.Path(p).read_text())
except Exception:
    sys.exit(0)
def emit_section(section):
    sect = d.get(section, {}) or {}
    for name, spec in sect.items():
        if isinstance(spec, str):
            constraint = spec
        elif isinstance(spec, dict):
            constraint = spec.get('version', '')
        else:
            constraint = ''
        print(f"{name}\t{constraint}")
emit_section('dependencies')
emit_section('dev-dependencies')
emit_section('build-dependencies')
PY
}

while IFS= read -r -d '' f; do
    while IFS=$'\t' read -r name constraint; do
        [[ -z "$name" ]] && continue
        emit_record "rust" "$name" "$constraint" "$f"
    done < <(parse_cargo "$f")
done < <(find . -maxdepth 4 -type f -name Cargo.toml \
    -not -path './.git/*' -not -path '*/node_modules/*' -not -path '*/target/*' -print0 2>/dev/null)

# --- JavaScript: package.json ---
while IFS= read -r -d '' f; do
    while IFS=$'\t' read -r name constraint; do
        [[ -z "$name" ]] && continue
        emit_record "javascript" "$name" "$constraint" "$f"
    done < <(jq -r '
        (.dependencies // {}) + (.devDependencies // {}) + (.peerDependencies // {})
        | to_entries[]
        | "\(.key)\t\(.value)"' "$f" 2>/dev/null || true)
done < <(find . -maxdepth 4 -type f -name package.json \
    -not -path './.git/*' -not -path '*/node_modules/*' -print0 2>/dev/null)

exit 0
