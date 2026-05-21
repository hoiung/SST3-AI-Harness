<!-- stages: 4 -->
# Gate 2 — Recursion-Safe Remote Fast-Forward Merge (#498 AC 4.1)

Stage-4 merge gate. Replaces the pre-#488 shared-tree branch-switch + pull + local-merge + push chain with a worktree-isolated remote FF push that touches NO shared working tree.

## Canonical procedure (dotfiles#488 AC 1.3)

1. Ensure all work committed by exact pathspec (NEVER `git add -A`).
2. Publish the solo branch: `git push origin <solo-branch>`.
3. Server-side fast-forward: `git push origin <solo-branch>:master`.
4. On non-fast-forward rejection (transient pre-push race): `git fetch origin master` then `git rebase origin/master` INSIDE the worktree, retry step 3. Bounded ≤3 attempts. **NEVER** `--force` / `--force-with-lease`.
5. `ExitWorktree action:keep` until push confirmed landed (`git ls-remote origin master` == solo tip); then `ExitWorktree action:remove`; then `git push origin --delete <solo-branch>`; then `git fetch --prune`.

## Branch-switch invariant

This gate runs ONLY `git push` / `git fetch` / `git rebase` INSIDE the isolated worktree. It NEVER:
- branch-switches in the shared clone
- local-merges (`git merge` in main)
- resets the shared main working tree

This is the dotfiles#488 chokepoint. The shared-clone branch-switch class moves every concurrent agent's HEAD; the worktree-isolated remote FF is the cure.

## When the rebase race fires

Operator-evidenced: `origin/master` advances between step 2 and step 3 (typically when another solo branch landed in the same multi-second window). The fetch + rebase + retry handles this deterministically; the bound of 3 attempts prevents indefinite spin if something else is wrong (e.g. protected-branch rule, server-side reject).

## Cross-references

- `.claude/commands/Leader.md` Stage 4 Gate 2 — operator-facing procedure.
- `CLAUDE.md` "Branch Safety (CRITICAL — DO NOT VIOLATE)" — the prose-level invariant.
- `claude/hooks/sst3-branch-guard.sh` — runtime backstop (dotfiles#490).
- `claude/hooks/sst3-destructive-op-guard.sh` — DENY mode on `--force` / `--force-with-lease` / `filter-repo` / `reset --hard` / `branch -D` (#498 F-4).
