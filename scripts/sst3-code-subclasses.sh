#!/usr/bin/env bash
# sst3-code-subclasses.sh — Reverse-inheritance lookup for a class via ast-grep.
#
# Usage:   sst3-code-subclasses.sh <class_name> <lang>
# Example: sst3-code-subclasses.sh BaseStrategyController python
# Output:  NDJSON, one object per subclass: {file, line, kind:"subclass", child}
# Engines: ast-grep --json=stream + jq base-list filter.
#
# #445 R4 (Bug D): companion to sst3-code-callers.sh, which is blind to
# inheritance — it only matches expression-position calls `Foo($$$)`, not
# `class Bar(Foo):` ClassDef nodes. On project-a,
# BaseStrategyController has 5 production subclass + production-call sites
# that callers.sh missed entirely. This wrapper closes that gap.
#
# Type-annotation references (`def f(x: Foo)`) and string-interpolated
# patches (`f"{MOD}.Foo._x"`) are deferred to future companion wrappers
# (sst3-code-typerefs.sh / sst3-code-stringrefs.sh) — different AST kinds,
# different engines.

set -euo pipefail
export LC_ALL=C


SST3_EMITTED_COUNT="${SST3_EMITTED_COUNT:-0}"
on_sigterm() {
    if command -v jq >/dev/null 2>&1; then
        jq -nc --arg n "sst3-code-subclasses" --argjson e "${SST3_EMITTED_COUNT:-0}" \
            '{kind:($n + "-killed"), reason:"sigterm", partial_records:$e}'
    else
        printf '{"kind":"%s-killed","reason":"sigterm","partial_records":%s}\n' \
            "sst3-code-subclasses" "${SST3_EMITTED_COUNT:-0}"
    fi
    exit 143
}
trap on_sigterm SIGTERM

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

if [[ $# -lt 2 ]]; then
    echo "ERROR: usage: $(basename "$0") <class_name> <lang>" >&2
    exit 64
fi

SYMBOL="$1"
LANG="$2"

assert_safe_identifier "$SYMBOL"

if ! command -v ast-grep >/dev/null 2>&1; then
    echo 'ERROR: ast-grep not installed; see dotfiles/docs/guides/code-query-playbook.md "Wrapper-Script Lane > Install"' >&2
    exit 127
fi

# Per-language class-definition pattern. Captures the subclass NAME and
# the base list (BASES); jq then filters down to those whose base list
# contains $SYMBOL.
case "$LANG" in
    python)
        # shellcheck disable=SC2016
        PATTERN='class $NAME($$$BASES): $$$BODY'
        ;;
    typescript|tsx|javascript)
        # shellcheck disable=SC2016
        PATTERN='class $NAME extends $BASE { $$$BODY }'
        ;;
    rust)
        # Rust uses impl blocks for trait/inheritance composition.
        # `impl <Trait> for <Type>` — match $TYPE implementing $SYMBOL trait.
        # shellcheck disable=SC2016
        PATTERN='impl $TRAIT for $TYPE { $$$BODY }'
        ;;
    *)
        echo "ERROR: unsupported lang: $LANG (supported: python, typescript, tsx, javascript, rust)" >&2
        exit 64
        ;;
esac

case "$LANG" in
    python)
        ast-grep run --pattern "$PATTERN" --lang python --json=stream 2>/dev/null \
            | jq -c --arg sym "$SYMBOL" '
                . as $m
                | ($m.metaVariables.multi.BASES // []) as $bases
                | if any($bases[]; .text == $sym) then
                    {file: $m.file, line: $m.range.start.line, kind: "subclass",
                     child: ($m.metaVariables.single.NAME.text // "?")}
                  else empty end
              ' \
            || true
        ;;
    typescript|tsx|javascript)
        ast-grep run --pattern "$PATTERN" --lang "$LANG" --json=stream 2>/dev/null \
            | jq -c --arg sym "$SYMBOL" '
                . as $m
                | if ($m.metaVariables.single.BASE.text // "") == $sym then
                    {file: $m.file, line: $m.range.start.line, kind: "subclass",
                     child: ($m.metaVariables.single.NAME.text // "?")}
                  else empty end
              ' \
            || true
        ;;
    rust)
        ast-grep run --pattern "$PATTERN" --lang rust --json=stream 2>/dev/null \
            | jq -c --arg sym "$SYMBOL" '
                . as $m
                | if ($m.metaVariables.single.TRAIT.text // "") == $sym then
                    {file: $m.file, line: $m.range.start.line, kind: "trait_impl",
                     child: ($m.metaVariables.single.TYPE.text // "?")}
                  else empty end
              ' \
            || true
        ;;
esac
