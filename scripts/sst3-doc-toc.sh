#!/usr/bin/env bash
# sst3-doc-toc.sh — Heading-anchor link drift in markdown docs.
#
# Usage:   sst3-doc-toc.sh [<paths>...] [--paths-from <ndjson>]
# Output:  NDJSON, one object per anchor link in markdown source:
#          {file, line, link_text, target_anchor, target_file, exists}
#          exists: true if the anchor is reachable in the target file
# Engines: ripgrep (link enumeration) + python3 (heading→slug match).
#
# Rationale (#447 Phase 8): markdownlint MD051 catches dangling anchors but
# returns lint codes, not NDJSON. Subagents need a structured contract so
# they can drive cross-doc cleanups + treat anchor-drift as a wrapper signal
# alongside other doc-* wrappers.

set -euo pipefail

# shellcheck source=./sst3-bash-utils.sh
source "$(dirname "$0")/sst3-bash-utils.sh"
export LC_ALL=C
SST3_EMITTED_COUNT=0

on_sigterm() {
    jq -nc --arg n "sst3-doc-toc" --argjson e "$SST3_EMITTED_COUNT" \
        '{kind:($n + "-killed"), reason:"sigterm", partial_records:$e}'
    exit 143
}
trap on_sigterm SIGTERM

PATHS_FROM=""
PATHS=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        --paths-from)
            PATHS_FROM="${2:-}"
            shift 2 || break
            ;;
        *)
            PATHS+=("$1")
            shift
            ;;
    esac
done

if ! command -v rg >/dev/null 2>&1; then
    echo 'ERROR: ripgrep not installed; see dotfiles/docs/guides/code-query-playbook.md "Wrapper-Script Lane > Install"' >&2
    exit 127
fi
if ! command -v python3 >/dev/null 2>&1; then
    echo 'ERROR: python3 not installed; see dotfiles/docs/guides/code-query-playbook.md "Wrapper-Script Lane > Install"' >&2
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

# Default scan target: . (find all .md files). Else use provided paths.
if [[ ${#PATHS[@]} -eq 0 ]]; then
    PATHS=(.)
fi

# Stage 5 fix — capture emit count via tmp file (subshell scope lost SST3_EMITTED_COUNT
# when emission ran inside python heredoc). Sentinel was always reporting 0.
TMP_OUT=$(mktemp)
trap 'rm -f "$TMP_OUT"; wrapper_sentinel "sst3-doc-toc" "$SST3_EMITTED_COUNT" "anchor-link"' EXIT

SST3_ALLOWED_PATHS="$(printf '%s\n' "${ALLOWED_PATHS[@]+"${ALLOWED_PATHS[@]}"}")" \
python3 - "${PATHS[@]}" > "$TMP_OUT" <<'PY'
import sys, os, re, json, pathlib

ROOTS = sys.argv[1:]
ALLOWED = {p for p in os.environ.get('SST3_ALLOWED_PATHS', '').splitlines() if p}
SLUG_RE = re.compile(r'[^a-zA-Z0-9 -]')
HEADING_RE = re.compile(r'^(#{1,6})\s+(.+?)\s*$')
LINK_RE = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')

def slugify(text: str) -> str:
    s = text.lower()
    s = SLUG_RE.sub('', s)
    s = s.replace(' ', '-').strip('-')
    return s

def collect_md(roots):
    files = []
    for r in roots:
        p = pathlib.Path(r)
        if p.is_file() and p.suffix.lower() == '.md':
            files.append(p)
        elif p.is_dir():
            for sub in p.rglob('*.md'):
                # Skip noisy dirs.
                parts = set(sub.parts)
                if any(skip in parts for skip in ('.git', 'node_modules', 'target', '_baseline-hashes.json')):
                    continue
                files.append(sub)
    return files

def headings_of(path: pathlib.Path):
    out = set()
    try:
        for line in path.read_text(encoding='utf-8', errors='replace').splitlines():
            m = HEADING_RE.match(line)
            if m:
                out.add(slugify(m.group(2)))
    except Exception:
        pass
    return out

files = collect_md(ROOTS)
heading_cache = {}

for f in files:
    try:
        text = f.read_text(encoding='utf-8', errors='replace')
    except Exception:
        continue
    for ln, line in enumerate(text.splitlines(), start=1):
        for m in LINK_RE.finditer(line):
            link_text, target = m.group(1), m.group(2)
            if '#' not in target:
                continue
            target_file_part, anchor = target.split('#', 1)
            anchor = anchor.strip()
            if not anchor:
                continue
            if target_file_part == '':
                # Same-file anchor.
                target_file = str(f)
            else:
                # Resolve relative path to target file.
                base_dir = f.parent
                resolved = (base_dir / target_file_part).resolve()
                target_file = str(resolved)
            if target_file not in heading_cache:
                p = pathlib.Path(target_file)
                if p.exists() and p.is_file():
                    heading_cache[target_file] = headings_of(p)
                else:
                    heading_cache[target_file] = None
            target_headings = heading_cache[target_file]
            if target_headings is None:
                exists = False
            else:
                exists = anchor in target_headings
            rec = {
                "file": str(f),
                "line": ln,
                "link_text": link_text,
                "target_anchor": anchor,
                "target_file": target_file,
                "exists": exists,
            }
            # --paths-from filter (Ralph Tier 3 FAIL D): non-empty ALLOWED set
            # restricts emit to records whose source `file` matches.
            if ALLOWED and rec["file"] not in ALLOWED:
                continue
            print(json.dumps(rec, separators=(',', ':')))
PY

SST3_EMITTED_COUNT=$(wc -l < "$TMP_OUT")
cat "$TMP_OUT"

exit 0
