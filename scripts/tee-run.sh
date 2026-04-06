#!/usr/bin/env bash
# tee-run.sh — SST3 Bash output discipline primitive (#406 F4.1 + Phase 9 fixes)
#
# Usage: tee-run.sh <label> -- <cmd> [args...]
#
# Runs <cmd>, tees combined stdout+stderr to a per-label log under
# ${SST3_TEE_DIR:-~/.cache/sst3/tee/}, prints "[tee: <path>]" header plus the
# last N lines (SST3_TEE_TAIL, default 200) to stdout, and exits with the
# original command's exit code.
#
# Anti-RTK design rules (#406):
#   1. NEVER silently truncate test failures — full log is on disk; agent reads
#      it on demand if the tail isn't enough.
#   2. NEVER mutate the underlying command — exit code, stdout/stderr semantics,
#      and ordering are preserved (output is just SAVED to disk in addition).
#   3. NEVER add telemetry — local file only, no network.
#   4. Kill switch is loud: SST3_WRAPPERS=off prints stderr banner before exec.
#   5. Tee-recovery: full log on disk even if the wrapped command crashes.
#   6. Observability at write time: structured event ALWAYS written to
#      sst3-events.jsonl after the command runs, regardless of exit code.
#
# Phase 9 fixes (#406 Stage 5 audit):
#   - BUG-A: previously `set -o errexit + pipefail` killed the script on
#     non-zero exit BEFORE the metrics block could write. Fixed by disabling
#     errexit/pipefail around the pipeline and capturing PIPESTATUS manually.
#   - BUG-B: previously `mkdir -p` failure (read-only TEE_DIR) silently exited
#     before running the wrapped command. Fixed: degraded mode runs the
#     command without tee and prints a loud stderr banner.
#   - Auto-rotation: TEE_DIR pruned on every run — files older than
#     SST3_TEE_TTL_DAYS (default 7) deleted. Bounds disk growth (#406 M1).
#   - sst3-events.jsonl rotated when it exceeds SST3_METRICS_MAX_BYTES
#     (default 1 MiB). Bounds disk growth (#406 M2).

set -o nounset

# Kill switch (loud, not silent)
if [[ "${SST3_WRAPPERS:-on}" == "off" ]]; then
    echo "[sst3] tee-run bypassed (SST3_WRAPPERS=off), no tee recording" >&2
    if [[ "${1:-}" == "--" ]]; then
        shift
    elif [[ $# -ge 2 ]]; then
        shift
    fi
    exec "$@"
fi

# Argument parsing
if [[ $# -lt 3 || "$2" != "--" ]]; then
    echo "[sst3 tee-run] usage: tee-run.sh <label> -- <cmd> [args...]" >&2
    exit 64
fi

LABEL="$1"
shift 2

# Sanitise label so we can safely use it in a filename
SAFE_LABEL=$(printf '%s' "$LABEL" | tr -c '[:alnum:]._-' '_')

# Constants (paralleled in sst3_utils.DEFAULT_METRICS_PATH — see comment there)
TEE_DIR="${SST3_TEE_DIR:-$HOME/.cache/sst3/tee}"
TAIL_LINES="${SST3_TEE_TAIL:-200}"
METRICS_PATH="${SST3_METRICS_PATH:-$HOME/.cache/sst3/sst3-events.jsonl}"
TTL_DAYS="${SST3_TEE_TTL_DAYS:-7}"
METRICS_MAX_BYTES="${SST3_METRICS_MAX_BYTES:-1048576}"  # 1 MiB

# BUG-B fix: degraded mode if cache dir cannot be created
DEGRADED=0
if ! mkdir -p "$TEE_DIR" "$(dirname "$METRICS_PATH")" 2>/dev/null; then
    echo "[sst3 tee-run] WARN: cannot create cache dirs (read-only?), running without tee" >&2
    DEGRADED=1
fi

if [[ "$DEGRADED" -eq 1 ]]; then
    # Honour anti-RTK rule 2: command MUST run even if tee can't.
    "$@"
    exit "$?"
fi

# M1 fix: rotate stale tee files (older than TTL_DAYS) — best-effort
find "$TEE_DIR" -maxdepth 1 -type f -name '*.log' -mtime "+${TTL_DAYS}" -delete 2>/dev/null || true

# M2 fix: rotate metrics file if it exceeds the size cap — best-effort
if [[ -f "$METRICS_PATH" ]]; then
    METRICS_SIZE=$(stat -c%s "$METRICS_PATH" 2>/dev/null || stat -f%z "$METRICS_PATH" 2>/dev/null || echo 0)
    if [[ "$METRICS_SIZE" -gt "$METRICS_MAX_BYTES" ]]; then
        mv "$METRICS_PATH" "${METRICS_PATH}.1" 2>/dev/null || true
    fi
fi

TS=$(date -u +%Y%m%dT%H%M%SZ)
TEE_FILE="$TEE_DIR/${SAFE_LABEL}-${TS}.log"

START_NS=$(date +%s%N 2>/dev/null || date +%s000000000)

# Header so the agent knows where the full log is
printf '[tee: %s]\n' "$TEE_FILE"

# BUG-A fix: errexit + pipefail OFF around the pipeline so PIPESTATUS capture
# and the metrics block are guaranteed to run even when the wrapped command
# exits non-zero.
set +o errexit
set +o pipefail
{
    if command -v stdbuf >/dev/null 2>&1; then
        stdbuf -oL -eL "$@" 2>&1
    else
        "$@" 2>&1
    fi
} | tee "$TEE_FILE" | tail -n "$TAIL_LINES"
EXIT_CODE=${PIPESTATUS[0]}

END_NS=$(date +%s%N 2>/dev/null || date +%s000000000)
DURATION_MS=$(( (END_NS - START_NS) / 1000000 ))

# Write-time observability per AP #12 (#406 F7.1 schema). ALWAYS runs because
# errexit is off above. Best-effort: failures here MUST NOT crash the wrapper.
{
    printf '{"ts":"%s","script":"tee-run.sh","event":"wrapper_run","level":"info","fields":{"label":"%s","exit_code":%d,"duration_ms":%d,"tee":"%s"}}\n' \
        "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        "$LABEL" \
        "$EXIT_CODE" \
        "$DURATION_MS" \
        "$TEE_FILE" \
        >> "$METRICS_PATH"
} 2>/dev/null || true

exit "$EXIT_CODE"
