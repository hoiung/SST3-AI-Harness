#!/usr/bin/env python3
"""
Verify a `published_to: <repo>@<sha>` frontmatter assertion against the target repo.

Used by blog-priv migration sample-invocations (and any future content-publication
gate) to harden the frontmatter contract: a draft claiming `published_to: hoiboy-uk@<sha>`
must point at a SHA that actually resolves in the hoiboy-uk worktree.

Returns (True, "") if the SHA exists in the repo as a commit object.
Returns (False, msg) on every fail mode (no '@', empty SHA, literal `pending`,
unresolvable SHA, missing repo). Pure stdlib + git CLI — no PyYAML / PyGit / etc.

Issue: hoiung/dotfiles#460 (Track A1 — pre-existing #459 deferral).
"""

from __future__ import annotations

import subprocess
from pathlib import Path


def verify_published_sha(published_to: str, repo_path: str | Path) -> tuple[bool, str]:
    """
    Verify a `<repo>@<sha>` published_to assertion against `repo_path`.

    `published_to` format: `<repo-name>@<full-sha>` (e.g. `hoiboy-uk@deadbeef...`).
    `repo_path` is the absolute filesystem path to the target repo's worktree.

    Returns (True, "") if the SHA exists in the repo as a commit object.
    Returns (False, msg) on every fail mode (literal `pending`, malformed,
    unresolvable, missing repo).
    """
    if "@" not in published_to:
        return (False, f"malformed published_to: missing '@' in {published_to!r}")
    _, sha = published_to.split("@", 1)
    sha = sha.strip()
    if not sha:
        return (False, f"empty SHA in published_to: {published_to!r}")
    if sha == "pending":
        return (False, f"published_to literal 'pending' (not yet published): {published_to!r}")
    repo_p = Path(repo_path).expanduser()
    if not (repo_p / ".git").exists():
        return (False, f"not a git repo: {repo_p}")
    result = subprocess.run(
        ["git", "-C", str(repo_p), "cat-file", "-e", f"{sha}^{{commit}}"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return (
            False,
            f"SHA {sha!r} does not resolve to a commit in {repo_p}: "
            f"{result.stderr.strip() or 'cat-file exited non-zero'}",
        )
    return (True, "")
