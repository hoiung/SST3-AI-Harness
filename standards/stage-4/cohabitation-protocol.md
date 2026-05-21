<!-- stages: 4 -->
# Cross-Repo Cohabitation Protocol — Stage-4 Canonical (#498 AC 4.1)

Multi-repo + multi-worktree + multi-agent concurrency contract. Originated in #469 Phase 4 closing dotfiles#449 stage 5.

## Single-concurrent-session-per-issue rule

NOT "single-session" — sequential sessions (compact + resume) are FINE. The contract is: NO two concurrent `/Leader` runs on the same Issue from different chat sessions.

Layer B sentinels (in `.sentinels/`) enforce — they auto-release after 24h staleness so a sequential resume can re-acquire; a concurrent acquire trips the sentinel as still-held.

## Two-worktree concurrency

Two agents working on DIFFERENT Issues in DIFFERENT worktrees of the same canonical clone is the supported case. The dotfiles#488 fix enables it:
- Each agent owns its own worktree (independent HEAD + index)
- Gate 2 uses the remote-FF push procedure (no shared-tree branch-switch)
- The `EnterWorktree` tool creates isolated worktrees from the same canonical

## Forbidden patterns

- Concurrent worktree creates against the same solo-branch name → second create errors
- Branch-switch in the shared canonical clone while a worktree holds the same branch
- `git pull --rebase` in the canonical's main while a worktree is mid-push

## Cross-references

- `../../standards/STANDARDS.md` "Cross-Repo Cohabitation Protocol" + "Multi-Agent Multi-Worktree Concurrency Contract".
- `CLAUDE.md` "Branch Safety (CRITICAL — DO NOT VIOLATE)" — operator-facing prose invariant.
- `claude/hooks/sst3-branch-guard.sh` — runtime enforcement (#490).
- `../../standards/stage-4/gate-2-merge.md` — the recursion-safe merge that respects this protocol.
