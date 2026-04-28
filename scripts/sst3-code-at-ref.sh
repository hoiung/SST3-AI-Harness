#!/usr/bin/env bash
# sst3-code-at-ref.sh — Meta-wrapper: run another wrapper against a historical ref.
#
# Usage:   sst3-code-at-ref.sh <ref> <wrapper-name> [args...]
# Example: sst3-code-at-ref.sh v0.5.0 sst3-code-large.sh 200 python
#          sst3-code-at-ref.sh main~10 sst3-code-callers.sh foo python
# Output:  NDJSON tagged with the ref. Every record from the inner wrapper is
#          re-emitted with `ref` injected:
#              {ref: "<ref>", ...inner_record}
# Engine:  git worktree (temporary, cleaned up via EXIT trap).
#
# Rationale (#447 Phase 6): "did this regression exist 3 weeks ago?" + "how
# many large functions were there at the v0.5 release?" + "list callers as of
# the bug-introducing commit" — all currently require manual `git worktree`
# scaffolding. This wrapper composes any existing sst3-code-*.sh against a
# historical ref with one bash line.

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

if [[ $# -lt 2 ]]; then
    echo "ERROR: usage: $(basename "$0") <ref> <wrapper-name> [args...]" >&2
    exit 64
fi

REF="$1"
WRAPPER="$2"
shift 2

if ! command -v git >/dev/null 2>&1; then
    echo 'ERROR: git not installed; see dotfiles/docs/guides/code-query-playbook.md "Wrapper-Script Lane > Install"' >&2
    exit 127
fi
if ! command -v jq >/dev/null 2>&1; then
    echo 'ERROR: jq not installed; see dotfiles/docs/guides/code-query-playbook.md "Wrapper-Script Lane > Install"' >&2
    exit 127
fi

# Reject path-traversal in the wrapper name; only basenames allowed.
if [[ "$WRAPPER" == */* || "$WRAPPER" == *..* ]]; then
    echo "ERROR: wrapper name must be a basename (got '$WRAPPER')" >&2
    exit 64
fi

# Resolve the wrapper path against the SCRIPTS dir of THIS dotfiles checkout.
# We deliberately do NOT use the worktree's copy of the script because the
# wrapper itself may have changed/regressed at the older ref — running the
# wrapper at HEAD against the worktree at <ref> is the correct comparison.
# Resolve scripts dir to an absolute path now, before any later cd into the
# worktree invalidates relative paths. Wrappers ship as `-rw-r--r--` and are
# invoked via `bash <path>`, so we check `-f` (regular file), not `-x`.
SCRIPTS_DIR="$(cd "$(dirname "$0")" 2>/dev/null && pwd)"
WRAPPER_PATH="$SCRIPTS_DIR/$WRAPPER"
if [[ ! -f "$WRAPPER_PATH" ]]; then
    echo "ERROR: wrapper not found: $WRAPPER_PATH" >&2
    exit 64
fi

# Verify the ref exists before incurring worktree cost.
if ! git rev-parse --verify "${REF}^{commit}" >/dev/null 2>&1; then
    echo "ERROR: unknown ref: $REF" >&2
    exit 64
fi

WORKTREE=$(mktemp -d -t sst3-at-ref.XXXXXX)
trap 'wrapper_sentinel "sst3-code-at-ref" "$SST3_EMITTED_COUNT" "record"; git worktree remove --force "$WORKTREE" >/dev/null 2>&1 || rm -rf "$WORKTREE"' EXIT

SST3_EMITTED_COUNT="${SST3_EMITTED_COUNT:-0}"
on_sigterm() {
    if command -v jq >/dev/null 2>&1; then
        jq -nc --arg n "sst3-code-at-ref" --argjson e "${SST3_EMITTED_COUNT:-0}" \
            '{kind:($n + "-killed"), reason:"sigterm", partial_records:$e}'
    else
        printf '{"kind":"%s-killed","reason":"sigterm","partial_records":%s}\n' \
            "sst3-code-at-ref" "${SST3_EMITTED_COUNT:-0}"
    fi
    exit 143
}
trap on_sigterm SIGTERM


if ! git worktree add --detach "$WORKTREE" "$REF" >/dev/null 2>&1; then
    echo "ERROR: failed to create worktree at $REF" >&2
    exit 1
fi

# Run the inner wrapper with the worktree as its CWD. Pipe stdout through jq
# to inject {ref: "<ref>"} on every record.
(
    cd "$WORKTREE"
    bash "$WRAPPER_PATH" "$@" 2>&1
) | while IFS= read -r LINE; do
    # Inner wrapper's stderr is also captured (2>&1) — distinguish JSON from
    # stderr lines by attempting to parse. Stderr passes through to our stderr.
    if printf '%s' "$LINE" | jq -e . >/dev/null 2>&1; then
        printf '%s' "$LINE" | jq -c --arg ref "$REF" '. + {ref: $ref}' || true
        SST3_EMITTED_COUNT=$((SST3_EMITTED_COUNT + 1))
        export SST3_EMITTED_COUNT
    else
        printf '%s\n' "$LINE" >&2
    fi
done
