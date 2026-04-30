#!/usr/bin/env bash
# sst3-bash-utils.sh — Shared bash helpers for the wrapper-lane (Issue #447).
#
# Sister of dotfiles/scripts/sst3_utils.py (Python helpers).
# Dash-vs-underscore distinction prevents Python `from sst3_utils import` collision.
#
# Helpers:
#   assert_safe_identifier <val>             — reject shell metacharacters; exit 64 (Phase 1)
#   normalise_lang <lang>                    — canonicalise language name; exit 64 if unsupported (Phase 3)
#   require_engine_version <tool> <min>      — warn-only stderr if version below pin (Phase 3)
#   read_paths_from <ndjson_file>            — emit unique file paths from {file:...} NDJSON (Phase 8 retrofit)
#   wrapper_sentinel <name> <count> <kind>   — "I ran" stderr line; call from EXIT trap
#   activate_paths_from_filter <ndjson>      — install transparent stdout NDJSON .file filter (Phase 8)
#
# Source via:
#   source "$(dirname "$0")/sst3-bash-utils.sh"
#
# NDJSON contract reminder for callers of activate_paths_from_filter:
# the helper installs `exec > >(jq -c ...)` which aborts the jq stream on
# the FIRST malformed stdout line and silently drops everything after.
# Wrappers MUST emit only valid one-object-per-line JSON to stdout.
# stderr (sentinels, diagnostics) is unaffected.

# PATH bootstrap — relocated from sst3-self-test.sh:22-37 (Issue #456).
# Reaches engines under $HOME/{.cargo,.local,.npm-global}/bin from non-interactive
# bash (.bashrc early-returns there). getent guard fixes SC2116 empty-HOME bug.
# Self-test keeps an inline copy so it self-bootstraps if this helper breaks.
: "${HOME:=$(getent passwd "$(id -u)" 2>/dev/null | cut -d: -f6)}"
[[ -z "$HOME" ]] && { echo "ERROR: cannot resolve HOME for PATH bootstrap" >&2; exit 1; }
# Each prepended only when missing from PATH (idempotent on repeat sourcing). Iteration-last wins lookup precedence: final order = /usr/local > npm-global > local > cargo > orig PATH.
for extra in "$HOME/.cargo/bin" "$HOME/.local/bin" "$HOME/.npm-global/bin" "/usr/local/bin"; do
    case ":$PATH:" in
        *":$extra:"*) ;;
        *) [[ -d "$extra" ]] && PATH="$extra:$PATH" ;;
    esac
done
export PATH
# Reject anything other than a plain identifier with dots (Class.method allowed).
# Exit 64 (EX_USAGE) consistent with the wrapper bad-args contract.
# Closes the command-injection class on every wrapper that interpolates user-
# supplied SYMBOL/NAME/BASE_CLASS into a shell-evaluated ast-grep pattern.
assert_safe_identifier() {
    local val="$1"
    if [[ ! "$val" =~ ^[a-zA-Z_][a-zA-Z0-9_.]*$ ]]; then
        echo "ERROR: identifier '$val' contains unsafe characters; expected ^[a-zA-Z_][a-zA-Z0-9_.]*\$" >&2
        exit 64
    fi
}

# Canonicalise language name. Echoes the canonical form on stdout.
# Maps: py|python|python3 → python; js|javascript|gs → javascript;
#       ts|typescript → typescript; tsx → tsx; rs|rust → rust;
#       sh|bash|shell → bash; md|markdown → markdown.
# Anything else → exit 64.
normalise_lang() {
    local lang="$1"
    case "$lang" in
        py|python|python3) echo "python" ;;
        js|javascript|gs) echo "javascript" ;;
        ts|typescript) echo "typescript" ;;
        tsx) echo "tsx" ;;
        rs|rust) echo "rust" ;;
        sh|bash|shell) echo "bash" ;;
        md|markdown) echo "markdown" ;;
        *)
            echo "ERROR: unsupported lang: $lang (supported: python, javascript, typescript, tsx, rust, bash, markdown)" >&2
            exit 64
            ;;
    esac
}

# Warn-only engine-version pin. Empirical break-on-version-X data not yet
# collected (Phase 3 of #447 docs this as a Layer-2 follow-up). Emits
# `WARN:` to stderr if missing or below `<min>`. Never blocks.
# Usage: require_engine_version <tool> <min>
# E.g.   require_engine_version ast-grep 0.20
require_engine_version() {
    local tool="$1"
    local min="$2"
    if ! command -v "$tool" >/dev/null 2>&1; then
        echo "WARN: $tool not on PATH; pin min_known_working=$min (warn-only)" >&2
        return 0
    fi
    local ver
    ver=$("$tool" --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+(\.[0-9]+)?' | head -n1 || true)
    if [[ -z "$ver" ]]; then
        echo "WARN: could not parse $tool --version output for pin check (min_known_working=$min)" >&2
        return 0
    fi
    local lowest
    lowest=$(printf '%s\n%s\n' "$ver" "$min" | sort -V | head -n1)
    if [[ "$lowest" != "$min" ]]; then
        echo "WARN: $tool version $ver below min_known_working=$min (warn-only; not yet empirically blocked)" >&2
    fi
}

# Read NDJSON file emitting one file path per line, deduplicated, in input order.
# Each NDJSON record must have a `.file` string. Records lacking `.file` are skipped.
# Used by --paths-from <file> retrofit (Phase 8) and the self-test driver.
read_paths_from() {
    local ndjson_file="$1"
    if [[ ! -r "$ndjson_file" ]]; then
        echo "ERROR: --paths-from file not readable: $ndjson_file" >&2
        exit 64
    fi
    if ! command -v jq >/dev/null 2>&1; then
        echo 'ERROR: jq not installed; see dotfiles/docs/guides/code-query-playbook.md "Wrapper-Script Lane > Install"' >&2
        exit 127
    fi
    jq -r 'select(.file != null) | .file' "$ndjson_file" | awk '!seen[$0]++'
}

# Universal "I ran" sentinel — call from EXIT trap.
# Usage:
#   trap 'wrapper_sentinel "sst3-code-large" "$SST3_EMITTED_COUNT" "function"' EXIT
wrapper_sentinel() {
    local name="${1:-$(basename "$0" .sh)}"
    local count="${2:-0}"
    local kind="${3:-record}"
    printf '%s: emitted %d %s(s)\n' "$name" "$count" "$kind" >&2
}

# --paths-from retrofit: parse --paths-from from "$@", strip it, and if a
# filter file was given, redirect this script's stdout through a jq filter
# that only passes NDJSON records whose `.file` is in the allowed set.
# Body code emits as usual; filtering is transparent.
#
# Usage at top of a retrofitted wrapper (after `source sst3-bash-utils.sh`):
#     # Strip --paths-from from positional args + activate filter:
#     ARGS=(); PATHS_FROM=""
#     while [[ $# -gt 0 ]]; do
#         case "$1" in
#             --paths-from) PATHS_FROM="${2:-}"; shift 2 || break;;
#             *) ARGS+=("$1"); shift;;
#         esac
#     done
#     set -- "${ARGS[@]}"
#     activate_paths_from_filter "$PATHS_FROM"
#
# Empty PATHS_FROM = no-op (filter not installed; stdout passes through).
# stderr is NOT filtered (sentinel + diagnostics still flow through).
# (#447 Phase 8 — universal retrofit, mechanical.)
activate_paths_from_filter() {
    local nd="${1:-}"
    [[ -z "$nd" ]] && return 0
    if [[ ! -r "$nd" ]]; then
        echo "ERROR: --paths-from file not readable: $nd" >&2
        exit 64
    fi
    if ! command -v jq >/dev/null 2>&1; then
        echo 'ERROR: jq not installed; see dotfiles/docs/guides/code-query-playbook.md "Wrapper-Script Lane > Install"' >&2
        exit 127
    fi
    local pattern
    pattern=$(jq -Rsc 'split("\n")|map(select(length>0))' < <(read_paths_from "$nd"))
    [[ -z "$pattern" || "$pattern" == "[]" ]] && return 0
    # Redirect stdout into a coprocess that filters NDJSON by .file membership.
    exec > >(jq -c --argjson allowed "$pattern" \
        'if (.file? // null) == null then . else select(.file as $f | $allowed | index($f) != null) end')
}
