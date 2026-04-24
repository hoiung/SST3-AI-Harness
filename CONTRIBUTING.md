# Contributing

Thanks for considering a contribution. This is a small / personal-project repo — external contributions are welcome but reviewed informally.

## Before You Open an Issue or PR

1. Check existing issues and recent commits — the change may already be in flight.
2. For non-trivial changes, open an issue first to discuss scope.
3. Read the repository's `README.md` and `CLAUDE.md` (if present) to understand the project's conventions.

## Issues

- Use a descriptive title. Self-contained, no issue/PR numbers embedded.
- Include reproduction steps, expected vs actual behaviour, and environment details for bugs.
- Feature requests should explain the problem first, proposed solution second.

## Pull Requests

- One logical change per PR. Split unrelated work into separate PRs.
- Keep commits clean. Small, focused commits beat one giant squash.
- PR description: summary + what-changed + how-tested. Link the related issue with `Related to #<N>` (NOT `Fixes` or `Closes` — issues are closed manually after review).
- CI must pass. If CI is flaky, say so in the PR — don't rebase-and-force-push to mask it.

## Code Style

The repo-specific conventions live in `README.md` / `CLAUDE.md` / existing code. Match the surrounding style. If a linter or formatter is configured, run it.

## What Gets Merged

Merges are subjective. Changes that fit the project's purpose, follow the conventions, and have clear rationale get merged. Changes that don't fit — even if technically correct — may be declined. That's not personal; it's scope.

## Security Issues

**Do not open a public issue for security reports.** See `SECURITY.md` for the private disclosure process.

---

*Canonical template — propagated across public mirror repos via drift-manifest.*
