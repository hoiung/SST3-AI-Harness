#!/usr/bin/env bash
# sst3-code-callees.sh — Outgoing function calls within a target function body.
#
# Usage:   sst3-code-callees.sh <name> <lang> [--class]
# Examples:
#   sst3-code-callees.sh load_voice_rules python
#       → callees inside the free-function `load_voice_rules`
#   sst3-code-callees.sh BaseStrategyController.__init__ python
#       → callees inside method `__init__` scoped to class
#         BaseStrategyController (disambiguates the dozens of __init__ defs)
#   sst3-code-callees.sh BaseStrategyController python --class
#       → callees inside ALL methods of class BaseStrategyController
#         (class-API surface mapping)
#
# Output:  NDJSON, one object per callee site: {file, line, callee}.
#          With --class, an extra `method` field tags which method the
#          callee came from (preserves attribution).
# Design:  Two-pass ast-grep — pass 1 locates the target definition and
#          emits its file + line range(s); pass 2 finds every call
#          expression and jq filters to those inside the matched ranges.
#          Request-scoped (no persistent state).
#          Missing ast-grep → stderr contract + exit 127.
#
# #445 R4 Bug H fix: pre-fix wrapper accepted only free-function names.
# Class-name input returned 0 (silent zero); bare `__init__` matched
# every class's constructor unioned together, useless without scoping.
# Now: `Class.method` syntax narrows by class range, `--class` flag
# enumerates all methods of the class.

set -euo pipefail
export LC_ALL=C


SST3_EMITTED_COUNT="${SST3_EMITTED_COUNT:-0}"
on_sigterm() {
    if command -v jq >/dev/null 2>&1; then
        jq -nc --arg n "sst3-code-callees" --argjson e "${SST3_EMITTED_COUNT:-0}" \
            '{kind:($n + "-killed"), reason:"sigterm", partial_records:$e}'
    else
        printf '{"kind":"%s-killed","reason":"sigterm","partial_records":%s}\n' \
            "sst3-code-callees" "${SST3_EMITTED_COUNT:-0}"
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

CLASS_MODE=0
ARGS=()
for arg in "$@"; do
    case "$arg" in
        --class) CLASS_MODE=1 ;;
        *) ARGS+=("$arg") ;;
    esac
done

if [[ ${#ARGS[@]} -lt 2 ]]; then
    echo "ERROR: usage: $(basename "$0") <name> <lang> [--class]" >&2
    exit 64
fi

NAME="${ARGS[0]}"
LANG="${ARGS[1]}"

assert_safe_identifier "$NAME"

if ! command -v ast-grep >/dev/null 2>&1; then
    echo 'ERROR: ast-grep not installed; see dotfiles/docs/guides/code-query-playbook.md "Wrapper-Script Lane > Install"' >&2
    exit 127
fi

# Detect Class.method syntax. Splits NAME into CLASS_NAME + METHOD_NAME.
CLASS_NAME=""
METHOD_NAME=""
if [[ "$NAME" == *.* ]]; then
    CLASS_NAME="${NAME%%.*}"
    METHOD_NAME="${NAME##*.}"
fi

# Per-language class + function patterns. Class uses kind-rule for
# robustness against inheritance + decorator variations.
case "$LANG" in
    python)
        FN_RULE='id: callees-fn
language: python
rule:
  kind: function_definition
  has:
    field: name
    pattern: $NAME'
        CLASS_RULE='id: callees-class
language: python
rule:
  kind: class_definition
  has:
    field: name
    pattern: $CNAME'
        ;;
    typescript|tsx|javascript)
        # #447 Phase 3: extended to include arrow_function and variable_declarator
        # (with arrow_function child) so TS/JS arrow-function callees are detected.
        # Without this the wrapper missed every `const foo = () => ...` definition.
        # Anonymous arrow functions still won't match (no `name` field) — those
        # are not addressable by name anyway.
        FN_RULE="id: callees-fn
language: $LANG
rule:
  any:
    - kind: function_declaration
    - kind: method_definition
    - kind: variable_declarator
  has:
    field: name
    pattern: \$NAME"
        CLASS_RULE="id: callees-class
language: $LANG
rule:
  kind: class_declaration
  has:
    field: name
    pattern: \$CNAME"
        ;;
    rust)
        FN_RULE='id: callees-fn
language: rust
rule:
  kind: function_item
  has:
    field: name
    pattern: $NAME'
        # Rust impl block — matches `impl <Type>` or `impl <Trait> for <Type>`.
        # We anchor on the implementing type, not the trait.
        CLASS_RULE='id: callees-class
language: rust
rule:
  kind: impl_item'
        ;;
    *)
        echo "ERROR: unsupported lang: $LANG (supported: python, typescript, tsx, javascript, rust)" >&2
        exit 64
        ;;
esac

# Helper: emit RANGES JSON for a class scope (Class.method or --class).
class_range() {
    local cname="$1"
    ast-grep scan --inline-rules "$CLASS_RULE" --json=stream 2>/dev/null \
        | jq -c --arg cn "$cname" '
            select(.metaVariables.single.CNAME.text == $cn)
            | {file, start: .range.start.line, end: .range.end.line}
        ' || true
}

# Helper: emit RANGES JSON for free function or method-name match.
fn_ranges() {
    local fname="$1"
    ast-grep scan --inline-rules "$FN_RULE" --json=stream 2>/dev/null \
        | jq -c --arg fname "$fname" '
            select(.metaVariables.single.NAME.text == $fname)
            | {file, start: .range.start.line, end: .range.end.line}
        ' || true
}

# Helper: filter ranges to those nested inside class scope ranges.
inside_class() {
    local class_ranges_json="$1"
    jq -c --argjson cranges "$class_ranges_json" '
        . as $m
        | ($cranges[] | select($m.file == .file and $m.start >= .start and $m.end <= .end)) as $cr
        | $m + {method_in_class: true}
    '
}

# Resolve target ranges based on mode.
RANGES=""

if [[ -z "$CLASS_NAME" ]] && [[ "$CLASS_MODE" -eq 0 ]]; then
    # Bare name: free-function or every method of that name across all classes.
    RANGES=$(fn_ranges "$NAME")
    # Disambiguation hint for class-name input.
    if [[ -z "$RANGES" ]] && [[ "$NAME" =~ ^[A-Z][A-Za-z0-9_]*$ ]]; then
        echo "WARN: '$NAME' looks like a class; pass --class to enumerate methods, or use Class.method to scope" >&2
    fi
elif [[ "$CLASS_MODE" -eq 1 ]]; then
    # --class: union of all methods inside class.
    CLASS_RANGES=$(class_range "$NAME" | jq -sc .)
    if [[ -z "$CLASS_RANGES" ]] || [[ "$CLASS_RANGES" == "[]" ]]; then
        echo "WARN: class '$NAME' not found in $LANG sources" >&2
        exit 0
    fi
    # Get all method defs and filter to those inside class ranges.
    RANGES=$(ast-grep scan --inline-rules "$FN_RULE" --json=stream 2>/dev/null \
        | jq -c '
            . as $m
            | {file, start: $m.range.start.line, end: $m.range.end.line, method: $m.metaVariables.single.NAME.text}
        ' \
        | inside_class "$CLASS_RANGES" \
        || true)
elif [[ -n "$CLASS_NAME" ]] && [[ -n "$METHOD_NAME" ]]; then
    # Class.method: narrow method by class range.
    CLASS_RANGES=$(class_range "$CLASS_NAME" | jq -sc .)
    if [[ -z "$CLASS_RANGES" ]] || [[ "$CLASS_RANGES" == "[]" ]]; then
        echo "WARN: class '$CLASS_NAME' not found in $LANG sources" >&2
        exit 0
    fi
    RANGES=$(fn_ranges "$METHOD_NAME" \
        | inside_class "$CLASS_RANGES" \
        || true)
fi

if [[ -z "$RANGES" ]]; then
    exit 0
fi

# Pass 2: per file with a matched range, find call expressions and filter.
# shellcheck disable=SC2016
CALL_PATTERN='$F($$$)'

echo "$RANGES" | jq -sc 'group_by(.file)[] | {file: .[0].file, ranges: [.[] | {start, end, method: (.method // null)}]}' \
    | while read -r FILE_GROUP; do
        FILE=$(echo "$FILE_GROUP" | jq -r '.file')
        RANGES_JSON=$(echo "$FILE_GROUP" | jq -c '.ranges')
        ast-grep run --pattern "$CALL_PATTERN" --lang "$LANG" --json=stream "$FILE" 2>/dev/null \
            | jq -c --argjson ranges "$RANGES_JSON" '
                . as $m
                | ($m.range.start.line) as $ln
                | ($ranges[] | select($ln >= .start and $ln <= .end)) as $r
                | {file: $m.file, line: $ln, callee: ($m.metaVariables.single.F.text // $m.text)}
                  + (if ($r.method // null) != null then {method: $r.method} else {} end)
              ' \
            || true
    done
