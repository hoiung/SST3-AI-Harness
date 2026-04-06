# Failed Experiments

Track self-healing changes reverted after validation period. Learn from failures.

## Revert Criteria
- 0/3 success rate in validation period
- Caused confusion in 2+ issues
- Introduced new bugs or violated guardrails
- Meta-test failure or quality regression

## Auto-Updated By
`../dotfiles/SST3/scripts/auto-rollback.py`, Stage 5 post-implementation review, manual documentation

## Entry Template
```markdown
### Issue #X - YYYY-MM-DD
**Origin**: Issue #X
**Description**: [What was added]
**Reason**: [Why it failed]
**Files**: [List affected files]
**Learnings**: [What we learned]
**Alternative**: [What to try instead]
```

## Failure Patterns
- Instruction too vague → confusion
- Instruction too rigid → false positives
- Missing context → misapplication
- Conflicting guidance → contradictions
- Scope creep → validation failure

## Learnings Integration
1. Refine validation criteria
2. Improve instruction design
3. Adjust rollback triggers
4. Identify alternatives

## Historical Record

*No failed experiments yet - validation system new as of Issue #119*

Note: Some experiments will fail. This proves validation works.

## Related
`validation-protocol.md`, `../scripts/auto-rollback.py`, `../dotfiles/SST3/standards/STANDARDS.md`
