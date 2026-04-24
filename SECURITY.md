# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it privately via GitHub's Security Advisory feature:

1. Go to the repository's **Security** tab.
2. Click **Report a vulnerability**.
3. Provide a clear description of the issue, reproduction steps, and affected versions.

Do **not** open a public issue for security reports — public issues are indexed and archived, which amplifies the disclosure.

## Supported Versions

Only the `main` branch is actively supported. Security fixes are applied forward; older commits are not patched.

## Response Expectations

Reports are reviewed ad-hoc (this is a personal / small-project repo, not a managed security pipeline). Triage time is best-effort. Critical issues affecting running infrastructure take priority.

## Scope

In scope:
- Secrets, credentials, private identifiers committed to the repository (handled by the existing secret-scan CI step).
- Supply-chain issues: malicious dependencies, compromised actions.
- Authentication / authorisation bypass in any server-code shipped from this repo.

Out of scope:
- Social engineering of the maintainer.
- Issues requiring physical access to machines running this code.
- Low-risk defaults (e.g. no HTTPS on a local-only dev server).

---

*Canonical template — propagated across public mirror repos via drift-manifest.*
