<!-- stages: 4 -->
# Gate 3 — User-Review-Checklist Post (#498 AC 4.1)

Final Stage-4 gate. Runs AFTER Gate 2 merge lands on origin/master. Uses the `../../templates/user-review-checklist.md` template VERBATIM; do NOT invent custom checklist forms.

## Canonical procedure

1. Read `../../templates/user-review-checklist.md`. Use the TEMPLATE — do NOT invent your own.
2. Fill ALL 10 sections. None are optional:
   - Scope Verification
   - Context Checkpoint
   - Gap Analysis — No Excuses Gate
   - How It Works
   - Cross-Issue Impact
   - Discoverability Check
   - Fail Fast Audit
   - Modular Architecture Review
   - Post-Implementation Review Gate
   - Closure Gate
3. Post the completed checklist as a comment on the GitHub Issue.
4. Report to operator: what was merged, Issue URL, checklist comment URL.

## §3 Gap Analysis — No-Excuses Gate (post-Cut-#9 contract)

Every item in §3 "Items Not Fixed" MUST carry one of three explicit flags (canonical: template §3 + Leader.md Stage 5 §3-Deferral angle):
- `[deferred-FP: <evidence>]` — confirmed false positive
- `[deferred-N/A: <rationale>]` — intentional descope
- `[deferred-tracking-issue: <issue#>]` — moved to a referenced OPEN issue

Items without any flag default to UNVERIFIED → trigger Stage 5 re-litigation. **F-15 (#498)**: this applies to the AGENT's own §3 entries — no self-exemption.

## Cross-references

- `../../templates/user-review-checklist.md` — the template (post-Cut-#9, ≤179 lines).
- `.claude/commands/Leader.md` Stage 4 Gate 3 — operator-facing procedure.
- Stage 5 `§3-Deferral Re-Litigation Angle` in `.claude/commands/Leader.md` — the audit-time enforcement.
