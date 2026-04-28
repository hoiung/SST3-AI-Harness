#!/usr/bin/env bash
# sst3-dep-cve.sh — Wrap pip-audit / cargo audit / npm audit into NDJSON.
#
# Usage:   sst3-dep-cve.sh
# Output:  NDJSON, one object per advisory:
#          {ecosystem, package, version, cve_id, severity}
#          severity: lowercase canonical (low|medium|high|critical|unknown)
# Engines: pip-audit (Python) | cargo audit (Rust) | npm audit (JS).
#          require_engine_version warn-only on each (per Phase 3).
# Behaviour: missing-engine-but-manifest-present → stderr WARN + skip that
#            ecosystem. Wrapper exits 0 even with findings (advisory data
#            flows via NDJSON, never via exit code — consumers decide).

set -euo pipefail

# shellcheck source=./sst3-bash-utils.sh
source "$(dirname "$0")/sst3-bash-utils.sh"
export LC_ALL=C
SST3_EMITTED_COUNT=0

trap 'wrapper_sentinel "sst3-dep-cve" "$SST3_EMITTED_COUNT" "advisory"' EXIT
on_sigterm() {
    jq -nc --arg n "sst3-dep-cve" --argjson e "$SST3_EMITTED_COUNT" \
        '{kind:($n + "-killed"), reason:"sigterm", partial_records:$e}'
    exit 143
}
trap on_sigterm SIGTERM

if ! command -v jq >/dev/null 2>&1; then
    echo 'ERROR: jq not installed; see dotfiles/docs/guides/code-query-playbook.md "Wrapper-Script Lane > Install"' >&2
    exit 127
fi

# Parse synthetic-fixture mode: if --fixture-stub is set, emit a single
# canned advisory record so the self-test fixture does not need network.
# Stage 5 fix (D2) — recognise --paths-from explicitly to surface bad usage.
# (Records lack a `.file` field by design — the canonical filter is a no-op
# here per the activate_paths_from_filter `if (.file? // null) == null`
# fallback, but silently swallowing an unknown flag is worse UX than
# accepting it and emitting unfiltered output.)
FIXTURE_STUB=""
PATHS_FROM=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --fixture-stub)
            FIXTURE_STUB="${2:-}"
            shift 2 || break
            ;;
        --paths-from)
            PATHS_FROM="${2:-}"
            shift 2 || break
            ;;
        *)
            shift
            ;;
    esac
done

# Validate --paths-from path even though records lack .file (per design).
if [[ -n "$PATHS_FROM" && ! -r "$PATHS_FROM" ]]; then
    echo "ERROR: --paths-from file not readable: $PATHS_FROM" >&2
    exit 64
fi

if [[ -n "$FIXTURE_STUB" ]]; then
    if [[ ! -r "$FIXTURE_STUB" ]]; then
        echo "ERROR: --fixture-stub path not readable: $FIXTURE_STUB" >&2
        exit 64
    fi
    # Stub is NDJSON; pass through and count.
    while IFS= read -r line; do
        [[ -z "$line" ]] && continue
        printf '%s\n' "$line"
        SST3_EMITTED_COUNT=$((SST3_EMITTED_COUNT + 1))
    done < "$FIXTURE_STUB"
    exit 0
fi

emit_record() {
    local ecosystem="$1" package="$2" version="$3" cve_id="$4" severity="$5"
    severity=$(printf '%s' "$severity" | tr '[:upper:]' '[:lower:]')
    [[ -z "$severity" ]] && severity="unknown"
    jq -nc --arg e "$ecosystem" --arg p "$package" --arg v "$version" --arg c "$cve_id" --arg s "$severity" \
        '{ecosystem:$e, package:$p, version:$v, cve_id:$c, severity:$s}'
    SST3_EMITTED_COUNT=$((SST3_EMITTED_COUNT + 1))
}

# --- Python via pip-audit ---
if find . -maxdepth 4 -type f \( -name pyproject.toml -o -name requirements.txt -o -name poetry.lock \) \
    -not -path './.git/*' -print -quit 2>/dev/null | grep -q .; then
    if command -v pip-audit >/dev/null 2>&1; then
        require_engine_version pip-audit 2.6
        # Stage 5 fix (D2) — capture pip-audit exit code; emit stderr WARN
        # if non-zero so consumers can distinguish "engine ran cleanly, no
        # advisories" from "engine broke / network blocked" without changing
        # exit-code policy (advisory data flows via NDJSON per docstring).
        # pip-audit -f json emits {dependencies:[{name, version, vulns:[{id, fix_versions, ...}]}]}
        _pip_audit_rc=0
        _pip_audit_out=$(pip-audit -f json 2>/dev/null) || _pip_audit_rc=$?
        if [[ "$_pip_audit_rc" -ne 0 && -z "$_pip_audit_out" ]]; then
            echo "WARN: pip-audit exited $_pip_audit_rc with no JSON output (network blocked? lockfile malformed?); python advisories unavailable" >&2
        fi
        while IFS=$'\t' read -r pkg ver cve sev; do
            [[ -z "$pkg" ]] && continue
            emit_record "python" "$pkg" "$ver" "$cve" "$sev"
        done < <(printf '%s' "$_pip_audit_out" \
            | jq -r '
                .dependencies[]?
                | . as $d
                | $d.vulns[]?
                | [$d.name, $d.version, .id, (.severity // "unknown")] | @tsv' \
            2>/dev/null || true)
    else
        echo "WARN: pip-audit not installed; skipping python ecosystem (manifest detected)" >&2
    fi
fi

# --- Rust via cargo audit ---
if find . -maxdepth 4 -type f -name Cargo.lock -not -path './.git/*' -print -quit 2>/dev/null | grep -q .; then
    if command -v cargo-audit >/dev/null 2>&1 || command -v cargo >/dev/null 2>&1; then
        require_engine_version cargo 1.70
        _cargo_audit_rc=0
        _cargo_audit_out=$(cargo audit --json 2>/dev/null) || _cargo_audit_rc=$?
        # Stage 5 fix (D2) — cargo audit exits non-zero ALSO when vulnerabilities
        # found, so only WARN when stdout is empty (the engine genuinely failed).
        if [[ "$_cargo_audit_rc" -ne 0 && -z "$_cargo_audit_out" ]]; then
            echo "WARN: cargo audit exited $_cargo_audit_rc with no JSON output (network blocked? Cargo.lock malformed?); rust advisories unavailable" >&2
        fi
        while IFS=$'\t' read -r pkg ver cve sev; do
            [[ -z "$pkg" ]] && continue
            emit_record "rust" "$pkg" "$ver" "$cve" "$sev"
        done < <(printf '%s' "$_cargo_audit_out" \
            | jq -r '
                .vulnerabilities.list[]?
                | [.package.name, .package.version, .advisory.id, (.advisory.severity // "unknown")] | @tsv' \
            2>/dev/null || true)
    else
        echo "WARN: cargo audit not installed; skipping rust ecosystem (Cargo.lock detected)" >&2
    fi
fi

# --- JavaScript via npm audit ---
if find . -maxdepth 4 -type f -name package-lock.json -not -path './.git/*' -not -path '*/node_modules/*' -print -quit 2>/dev/null | grep -q .; then
    if command -v npm >/dev/null 2>&1; then
        require_engine_version npm 9.0
        _npm_audit_rc=0
        _npm_audit_out=$(npm audit --json 2>/dev/null) || _npm_audit_rc=$?
        if [[ "$_npm_audit_rc" -ne 0 && -z "$_npm_audit_out" ]]; then
            echo "WARN: npm audit exited $_npm_audit_rc with no JSON output (network blocked? package-lock.json malformed?); javascript advisories unavailable" >&2
        fi
        while IFS=$'\t' read -r pkg ver cve sev; do
            [[ -z "$pkg" ]] && continue
            emit_record "javascript" "$pkg" "$ver" "$cve" "$sev"
        done < <(printf '%s' "$_npm_audit_out" \
            | jq -r '
                .vulnerabilities | to_entries[]?
                | .key as $k
                | .value.via[]?
                | select(type == "object")
                | [$k, (.range // ""), (.url // ""), (.severity // "unknown")] | @tsv' \
            2>/dev/null || true)
    else
        echo "WARN: npm not installed; skipping javascript ecosystem (package-lock.json detected)" >&2
    fi
fi

exit 0
