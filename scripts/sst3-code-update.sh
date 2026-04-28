#!/usr/bin/env bash
# sst3-code-update.sh — No-op contract preservation (replaces the prior daemon-MCP `graph update` invocation).
#
# Usage:   sst3-code-update.sh
# Output:  Single JSON object: {status, repo_head}
# Reason:  Wrapper lane is stateless — there is no graph and no state to
#          refresh. Canonical docs historically referenced `graph update`;
#          this no-op preserves the contract surface and avoids fragile
#          find-replace deletions across canonical docs. Issue #445 Stage 5
#          retained the wrapper but renamed the script
#          (sst3-graph-update.sh → sst3-code-update.sh) per honest-naming audit.

set -euo pipefail

REPO_HEAD=$(git rev-parse HEAD 2>/dev/null || echo "unknown")

jq -nc \
    --arg head "$REPO_HEAD" \
    '{status: "stateless, no update needed", repo_head: $head}'
