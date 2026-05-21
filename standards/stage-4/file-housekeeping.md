<!-- stages: 4 -->
# File Housekeeping — Stage-4 Canonical (#498 AC 4.1)

Per-Issue housekeeping invariants. Originated in Issue #108 + cumulative cleanup discipline.

## Per-Issue housekeeping

- Every Issue scope MUST include a "Cleanup Requirements" subsection (Code Hygiene + File Housekeeping). Template: `../../templates/issue-template.md`.
- Code Hygiene: remove dead code touched by this Issue; remove commented-out blocks; remove `print()` debug-leftovers; remove unused imports; remove "TODO: later" without owner.
- File Housekeeping: delete files this Issue obsoletes; remove duplicate fixtures; delete temp scripts in `/tmp/` if they were committed; delete `_drafts/` files migrated upstream.

## Issue #108 lesson: repetition is intentional

The same housekeeping checklist appears in EVERY Issue body, not in a "global housekeeping doc". Reason: per-Issue scoping is what makes the cleanup actionable; a global doc is a wishlist, a per-Issue scope is a contract. Cleanup-as-acceptance-criterion is the discipline.

## What does NOT belong in housekeeping

- Reorganising files unrelated to this Issue (scope creep)
- Renaming functions for "consistency" when no caller needs the rename
- "Modernising" old code that still works (Quality First — don't churn working code)

## Cross-references

- `../../standards/STANDARDS.md` "File Housekeeping" + "Issue #108 Lesson".
- `../../templates/issue-template.md` "Cleanup Requirements" subsection.
- `../../standards/ANTI-PATTERNS.md` AP #6 (Scope Creep) — counterweight to housekeeping ambition.
