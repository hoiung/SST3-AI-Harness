#!/usr/bin/env bash
# sst3-check.sh — Layer-2 orchestrator composing the wrapper-lane (A+B+C).
#
# Usage:   sst3-check.sh [--code | --sec | --dep | --doc | --sync | --all] [--quiet]
# Default: --all
# Output:  NDJSON stream:
#          - One {kind:"orchestrator-progress", phase:"<label>", status:"started"} per phase
#          - Findings from each wrapper, tagged with {kind:"<area>", ...}
#          - One {kind:"orchestrator-progress", phase:"<label>", status:"complete|...", findings:N, seconds:T}
#            per phase on completion
#          - One terminating {kind:"orchestrator-complete", phases:[...], findings:N} on EXIT
#          The orchestrator-complete sentinel is emitted via EXIT trap so it
#          appears EVEN on early termination — lets consumers distinguish
#          "all phases done" from "killed mid-stream".
# Exit:    0 = no findings; 1 = findings emitted; 127 = required engine missing.
# Engines: composes sst3-code-* (Phase A) + sst3-doc-* (Phase B) + sst3-sync-* (Phase C).
#
# #445 R4 Bug B fix: pre-fix, the FINDINGS counter was incremented inside a
# pipeline subshell at the old emit() function — parent shell always saw 0.
# No completion sentinel meant consumers couldn't tell "ran clean" from
# "killed mid-stream". 5 inner wrappers exiting 127 silently produced no
# diagnostic JSON, indistinguishable from "no findings". Now: counter is
# captured via temp file + wc -l (real count, not subshell-lost), each phase
# emits started/complete progress sentinels with status+findings+seconds,
# and the EXIT trap guarantees orchestrator-complete fires even on SIGTERM
# from outer `timeout`.

set -euo pipefail

MODE=all
QUIET=0
STRICT=0
for arg in "$@"; do
    case "$arg" in
        --code) MODE=code ;;
        --sec) MODE=sec ;;
        --dep) MODE=dep ;;
        --doc) MODE=doc ;;
        --sync) MODE=sync ;;
        --all) MODE=all ;;
        --quiet) QUIET=1 ;;
        --strict) STRICT=1 ;;
        *) echo "ERROR: unknown arg: $arg" >&2; exit 64 ;;
    esac
done

WRAPPER_DIR="$(dirname "$(realpath "$0")")"
FINDINGS=0
PHASES_DONE=()
ENGINE_MISSING_COUNT=0

# Wrappers that REQUIRE explicit args (target symbol/class/lang) and therefore
# do NOT compose into --all — they're invoked directly when needed. The Shape 31
# orchestrator-meta record exposes this list so engineers reading "phases=N"
# from the output understand which wrappers got skipped by design vs by failure.
TARGET_REQUIRED_SKIPPED=(
    sst3-code-callers
    sst3-code-callees
    sst3-code-search
    sst3-code-impact
    sst3-code-review
    sst3-code-subclasses
    sst3-code-callers-transitive
    sst3-code-coverage
    sst3-code-cross-lang
    sst3-code-secrets
    sst3-code-shell
    sst3-code-recent-changes
    sst3-code-at-ref
    sst3-dep-usage
    sst3-dep-blast-radius
    sst3-sync-doc-to-code
    sst3-sync-url-liveness
)

# Per-phase timeout — prevents one slow inner wrapper from starving the rest
# under an outer wallclock cap.
PHASE_TIMEOUT="${SST3_CHECK_PHASE_TIMEOUT:-90}"

# EXIT trap: emit orchestrator-complete sentinel UNCONDITIONALLY. Guarantees
# downstream consumers can detect "orchestrator finished" via a terminating
# NDJSON record, regardless of whether we exited cleanly, hit `set -e`, or
# got SIGTERM from an outer timeout.
on_exit() {
    local rc=$?
    local phases_json
    if [[ ${#PHASES_DONE[@]} -eq 0 ]]; then
        phases_json='[]'
    else
        phases_json=$(printf '%s\n' "${PHASES_DONE[@]}" | jq -R . | jq -sc .)
    fi
    jq -nc \
        --argjson p "$phases_json" \
        --argjson n "$FINDINGS" \
        --arg m "$MODE" \
        '{kind:"orchestrator-complete", mode:$m, phases:$p, findings:$n}'
    exit "$rc"
}
trap on_exit EXIT

run_or_skip() {
    local LABEL="$1"
    local SCRIPT="$2"
    shift 2

    # Started sentinel
    jq -nc --arg p "$LABEL" '{kind:"orchestrator-progress", phase:$p, status:"started"}'

    if [[ ! -f "$SCRIPT" ]]; then
        jq -nc --arg p "$LABEL" '{kind:"orchestrator-progress", phase:$p, status:"skipped", reason:"script not found"}'
        PHASES_DONE+=("$LABEL:skipped")
        return 0
    fi

    [[ "$QUIET" -eq 0 ]] && echo "[sst3-check] running $LABEL" >&2

    local start=$SECONDS
    local tmp stderr_tmp
    tmp=$(mktemp)
    stderr_tmp=$(mktemp)
    set +e
    # #447 Phase 2: capture inner stderr to per-phase tmp file instead of
    # /dev/null. Engine-broken wrappers wrote diagnostics to stderr that the
    # orchestrator was throwing away; now we surface them in NDJSON so consumers
    # can debug without re-running.
    timeout --preserve-status "$PHASE_TIMEOUT" bash "$SCRIPT" "$@" >"$tmp" 2>"$stderr_tmp"
    local rc=$?
    set -e

    local lines=0
    if [[ -s "$tmp" ]]; then
        # Tag each wrapper-emitted NDJSON line with the orchestrator's kind.
        while IFS= read -r LINE; do
            [[ -z "$LINE" ]] && continue
            echo "$LINE" | jq -c --arg k "$LABEL" '. + {kind: $k}' 2>/dev/null || true
            lines=$((lines + 1))
        done < "$tmp"
    fi
    rm -f "$tmp"

    # Surface captured stderr as a structured NDJSON record (#447 Phase 2 / Shape 27).
    if [[ -s "$stderr_tmp" ]]; then
        local stderr_lines stderr_sample
        stderr_lines=$(wc -l < "$stderr_tmp")
        # Sample first 5 lines, JSON-array-encoded.
        stderr_sample=$(head -n 5 "$stderr_tmp" | jq -R . | jq -sc .)
        jq -nc \
            --arg p "$LABEL" \
            --argjson n "$stderr_lines" \
            --argjson s "$stderr_sample" \
            '{kind:($p + "-stderr-captured"), lines:$n, sample:$s}'
    fi
    rm -f "$stderr_tmp"

    FINDINGS=$((FINDINGS + lines))

    local status
    case "$rc" in
        0)        status=complete ;;
        124|143)  status=timeout ;;       # 124 = `timeout` direct, 143 = SIGTERM via --preserve-status
        127)      status=engine-missing ;;
        126)      status=skipped ;;
        *)        status=error ;;
    esac

    if [[ "$status" == "engine-missing" ]]; then
        ENGINE_MISSING_COUNT=$((ENGINE_MISSING_COUNT + 1))
    fi

    jq -nc \
        --arg p "$LABEL" \
        --arg s "$status" \
        --argjson n "$lines" \
        --argjson t $((SECONDS - start)) \
        --argjson rc "$rc" \
        '{kind:"orchestrator-progress", phase:$p, status:$s, findings:$n, seconds:$t, exit:$rc}'

    PHASES_DONE+=("$LABEL:$status")
}

if [[ "$MODE" == "all" || "$MODE" == "code" ]]; then
    run_or_skip code-status "$WRAPPER_DIR/sst3-code-status.sh"
    run_or_skip code-large "$WRAPPER_DIR/sst3-code-large.sh" 200 python
    run_or_skip code-untested-py "$WRAPPER_DIR/sst3-code-untested-py.sh"
    # Stage 5 fix (D5) — wire Phase 8 no-arg code wrappers.
    run_or_skip code-config "$WRAPPER_DIR/sst3-code-config.sh"
    run_or_skip code-orphans "$WRAPPER_DIR/sst3-code-orphans.sh" python
    run_or_skip code-entry-points "$WRAPPER_DIR/sst3-code-entry-points.sh"
    # NOTE: sst3-code-{callers, callees, callers-transitive, search, impact, review,
    # subclasses, coverage, cross-lang, secrets, shell, recent-changes, at-ref}
    # require explicit targets — see TARGET_REQUIRED_SKIPPED.
fi

# Stage 5 fix (D5) — Phase 8a security wrappers (all no-arg).
if [[ "$MODE" == "all" || "$MODE" == "sec" ]]; then
    run_or_skip sec-subprocess "$WRAPPER_DIR/sst3-sec-subprocess.sh"
    run_or_skip sec-deserialize "$WRAPPER_DIR/sst3-sec-deserialize.sh"
    run_or_skip sec-secret-touchpoints "$WRAPPER_DIR/sst3-sec-secret-touchpoints.sh"
    run_or_skip sec-input-sources "$WRAPPER_DIR/sst3-sec-input-sources.sh"
fi

# Stage 5 fix (D5) — Phase 8b dep wrappers (no-arg subset; usage + blast-radius
# require <package> arg → TARGET_REQUIRED_SKIPPED).
if [[ "$MODE" == "all" || "$MODE" == "dep" ]]; then
    run_or_skip dep-list "$WRAPPER_DIR/sst3-dep-list.sh"
    run_or_skip dep-cve "$WRAPPER_DIR/sst3-dep-cve.sh"
fi

if [[ "$MODE" == "all" || "$MODE" == "doc" ]]; then
    run_or_skip doc-lint "$WRAPPER_DIR/sst3-doc-lint.sh"
    run_or_skip doc-yaml "$WRAPPER_DIR/sst3-doc-yaml.sh"
    run_or_skip doc-frontmatter "$WRAPPER_DIR/sst3-doc-frontmatter.sh"
    run_or_skip doc-links "$WRAPPER_DIR/sst3-doc-links.sh"
    # Stage 5 fix (D5) — Phase 8c doc anchor-link drift (no-arg).
    run_or_skip doc-toc "$WRAPPER_DIR/sst3-doc-toc.sh"
fi

if [[ "$MODE" == "all" || "$MODE" == "sync" ]]; then
    run_or_skip sync-related-code "$WRAPPER_DIR/sst3-sync-related-code.sh"
    # Eviction guard: detect references to the displaced legacy MCP graph token.
    # Token is constructed at runtime to avoid tripping the same eviction hook
    # that this orchestrator phase is designed to detect.
    EVICTION_TOKEN="mcp__$(printf '%s' code-review-graph)__"
    run_or_skip sync-tool-eviction "$WRAPPER_DIR/sst3-sync-tool-eviction.sh" "$EVICTION_TOKEN"
    # NOTE: sst3-sync-doc-to-code.sh requires <doc> + <lang> args — not composable
    # without a default doc selection. Invoke directly when needed.
    # NOTE: sst3-sync-url-liveness.sh is an alias to sst3-doc-links.sh — already
    # invoked above in the doc lane to avoid duplicate execution.
fi

if [[ "$QUIET" -eq 0 ]]; then
    echo "[sst3-check] mode=$MODE findings=$FINDINGS phases=${#PHASES_DONE[@]} engine_missing=$ENGINE_MISSING_COUNT strict=$STRICT" >&2
fi

# Shape 31 fix (#447 Phase 2): emit an orchestrator-meta record exposing how
# many wrappers actually composed vs how many were skipped by design. Without
# this, "phases=9" leaves engineers wondering whether there are 9 wrappers
# total or 19 with 10 silently absent.
SKIPPED_JSON=$(printf '%s\n' "${TARGET_REQUIRED_SKIPPED[@]}" | jq -R . | jq -sc .)
jq -nc \
    --argjson r "${#PHASES_DONE[@]}" \
    --argjson s "$SKIPPED_JSON" \
    --arg m "$MODE" \
    '{kind:"orchestrator-meta", mode:$m, composable_phases_run:$r, target_required_skipped:$s}'

# --strict propagation (#447 Phase 2 silent-clean fix): without --strict, any
# inner engine-missing exits 0 (silent-clean). With --strict, ANY engine-missing
# wrapper escalates to exit 2 — distinct from "findings present" (1) and "all
# clean" (0). /Leader Stage 1a runs --strict by default per Phase 5 edits.
if [[ "$STRICT" -eq 1 ]] && [[ "$ENGINE_MISSING_COUNT" -gt 0 ]]; then
    echo "[sst3-check] STRICT: $ENGINE_MISSING_COUNT phase(s) missing engine — exit 2" >&2
    exit 2
fi

[[ "$FINDINGS" -gt 0 ]] && exit 1
exit 0
