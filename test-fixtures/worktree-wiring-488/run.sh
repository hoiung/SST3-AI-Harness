#!/usr/bin/env bash
# worktree-wiring-488 fixture (dotfiles#488 Fix-A, AC 1.4).
# Guards against silent doc-drift removing the EnterWorktree wiring that is
# the PRIMARY fix for "branches keep getting switched / implementations
# muddled". Asserts:
#   1. CLAUDE.md "Branch Safety (CRITICAL — DO NOT VIOLATE)" section is the
#      authoritative anchor: contains EnterWorktree AND "work in a worktree"
#      (the tool only activates from a user/CLAUDE.md/memory directive).
#   2. .claude/commands/Leader.md Stage-4 references EnterWorktree.
#   3. .claude/commands/SST3-solo.md "Before Starting Work" references it.
#   4. Leader.md Gate-2 block is the recursion-safe remote-FF form: contains
#      ExitWorktree AND has ZERO shared-tree `git (checkout|merge|reset)`
#      forms (AC 1.3 invariant — guards a drift that reverts Gate-2 to the
#      shared-HEAD `git checkout main && git merge` chokepoint).
#   5. "NEVER switch branches" is retained as the in-worktree invariant
#      (AC 1.2 — the rule is correct INSIDE an isolated worktree).
# Exit 0 = wiring intact; exit 1 = drift (a fix-A regression).

set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
CLAUDE="$REPO_ROOT/CLAUDE.md"
LEADER="$REPO_ROOT/.claude/commands/Leader.md"
SOLO="$REPO_ROOT/.claude/commands/SST3-solo.md"

fail() { echo "FAIL: $1"; exit 1; }

# --- 1. CLAUDE.md Branch-Safety anchor ---
bs=$(awk '/^### Branch Safety \(CRITICAL/{f=1} f&&/^### /&&!/Branch Safety/{if(seen)f=0} {if(f)print} /^### Branch Safety \(CRITICAL/{seen=1}' "$CLAUDE")
echo "$bs" | grep -q 'EnterWorktree' || fail "CLAUDE.md Branch-Safety section missing EnterWorktree anchor (#488 AC 1.1)"
echo "$bs" | grep -qi 'work in a worktree' || fail "CLAUDE.md Branch-Safety section missing 'work in a worktree' (EnterWorktree tool activation phrase)"
echo "$bs" | grep -q 'NEVER switch branches' || fail "CLAUDE.md Branch-Safety lost the 'NEVER switch branches' in-worktree invariant (#488 AC 1.2)"
echo "PASS: CLAUDE.md Branch-Safety anchor (EnterWorktree + work-in-a-worktree + NEVER-switch invariant)"

# --- 2/3. Leader.md + SST3-solo.md reference the anchor ---
grep -q 'EnterWorktree' "$LEADER" || fail "Leader.md missing EnterWorktree reference (#488 AC 1.1)"
echo "PASS: Leader.md references EnterWorktree"
grep -q 'EnterWorktree' "$SOLO" || fail "SST3-solo.md missing EnterWorktree reference (#488 AC 1.1)"
echo "PASS: SST3-solo.md references EnterWorktree"

# --- 4. Leader.md Gate-2 recursion-safe remote-FF (AC 1.3) ---
gate2=$(awk '/^### Gate 2: Merge/{f=1} f&&/^### Gate 3:/{f=0} {if(f)print}' "$LEADER")
echo "$gate2" | grep -q 'ExitWorktree' || fail "Leader.md Gate-2 missing ExitWorktree (#488 AC 1.3)"
if echo "$gate2" | grep -nE 'git (-C [^ ]+ )?(checkout|merge|reset)\b' >/dev/null; then
    fail "Leader.md Gate-2 reintroduced a shared-tree git checkout/merge/reset (#488 AC 1.3 regression)"
fi
echo "PASS: Leader.md Gate-2 is recursion-safe remote-FF (ExitWorktree present, zero shared-tree mutation)"

echo "OK: worktree-wiring-488 fixture (4/4 assertions passed)"
