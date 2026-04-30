#!/usr/bin/env bash
# KNOWN-BROKEN variant of sst3-code-large.sh — markdown branch removed.
# The active wrapper at scripts/sst3-code-large.sh covers `md`/`markdown`
# via a heading-block heuristic (#447 Phase 3). This variant strips that
# branch, so calling with `lang=md` falls through to the unsupported-lang
# error path — `code-large-md` fixture MUST flag this as drift.
#
# Meta-validation: swap this file in, run sst3-self-test, expect non-zero.
# Restore the active wrapper after.

set -euo pipefail

if [[ $# -lt 2 ]]; then
    echo "ERROR: usage: $(basename "$0") <min_lines> <lang>" >&2
    exit 64
fi

MIN_LINES="$1"
LANG="$2"

if ! command -v ast-grep >/dev/null 2>&1; then
    echo 'ERROR: ast-grep not installed; see dotfiles/docs/guides/code-query-playbook.md "Wrapper-Script Lane > Install"' >&2
    exit 127
fi

case "$LANG" in
    python) RULE='id: large-fn
language: python
rule:
  kind: function_definition
  has:
    field: name
    pattern: $NAME' ;;
    *)
        echo "ERROR: unsupported lang: $LANG (broken-variant: only python supported)" >&2
        exit 64
        ;;
esac

ast-grep scan --inline-rules "$RULE" --json=stream 2>/dev/null \
    | jq -c --argjson min "$MIN_LINES" '
        . as $m |
        ($m.range.end.line - $m.range.start.line + 1) as $n |
        select($n >= $min) |
        {file: $m.file, name: ($m.metaVariables.single.NAME.text // "?"), lines: $n}
      ' \
    || true
