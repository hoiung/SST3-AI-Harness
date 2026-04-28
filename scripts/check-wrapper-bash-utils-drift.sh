#!/usr/bin/env bash
# check-wrapper-bash-utils-drift.sh — pre-commit hook entrypoint (Issue #456 Phase 2).
#
# Runs the live-wrapper bash-utils drift audit ONLY (no fixture run).
# Exits 1 + emits NDJSON wrapper-drift records to stdout when any sst3-*.sh
# wrapper either:
#   (a) does not source sst3-bash-utils.sh AND is not on .bash-utils-exempt-list
#   (b) sources sst3-bash-utils.sh AFTER its first `command -v <engine>` check.
#
# Fast: scans only ~38 wrappers via Python regex; no fixture invocations.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$SCRIPT_DIR/_self_test_driver.py" --wrapper-drift-only
