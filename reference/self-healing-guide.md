# Self-Healing Guide

> Comprehensive failure scenarios and recovery playbooks from Issues #82-#130

## Quick Reference

**When self-healing fails**: See Common Failure Scenarios below
**When in doubt**: Rollback + document in new Issue
**Prevention**: Run pre-flight checks before self-healing changes

---

## Post-Implementation Self-Healing Process (Stage 5)

1. Analyze what went wrong (retrospective)
2. Identify instruction gaps (root cause)
3. Propose updates to "Common Mistakes" sections
4. Apply to stage files (with validation)
5. Verify fix works (meta-test if possible)

### Example

[Issue #83](https://github.com/hoiung/dotfiles/issues/83) finds Stage 3 instructions unclear about commit frequency.

**Proposed update to implementation guidance (Stage 4)**:
```markdown
**Mistake**: Waiting until end to commit all changes
- **Fix**: Commit after each logical group of changes
- **Added**: 2025-11-08
```

---

## Common Failure Scenarios

### Scenario 1: Verification False PASS

**Symptoms**:
- Automated check reports BLOCKING/ERROR
- Manual assessment overrides as "ACCEPTABLE"
- PR created despite failure

**Root Cause**: Manual interpretation defeats automation, subjective criteria

**Recovery Steps**:
1. Immediately close/revert PR
2. Check automated test output for BLOCKING keywords
3. Identify why manual override occurred
4. Fix verification to auto-FAIL on BLOCKING (no manual override)
5. Re-run verification with fixed process

**Prevention**:
- Automated checks must auto-FAIL on BLOCKING ([Issue #128](https://github.com/hoiung/dotfiles/issues/128) fix)
- No manual override allowed for critical failures
- Quantitative criteria only (exit codes, keyword parsing)

**Reference**: [Issue #124](https://github.com/hoiung/dotfiles/issues/124) (failure), [#128](https://github.com/hoiung/dotfiles/issues/128) (fix)

---

### Scenario 2: Aggressive Over-Pruning

**Symptoms**:
- Multiple pruning passes in single Issue
- Documentation becomes ambiguous after pruning
- Developers ask "how do I do X?" after reading docs

**Root Cause**: Token budget treated as hard blocker vs advisory

**Recovery Steps**:
1. Stop further pruning immediately
2. Identify GOLDEN commit (last comprehensive version)
3. Use MERGE strategy: keep post-GOLDEN improvements + restore GOLDEN examples
4. Apply JBGE test: does each section prevent a documented problem?
5. Measure quality before/after (can developers execute successfully?)

**Prevention**:
- Quality First: Token budget is advisory, not blocking
- JBGE: Only prune content that doesn't prevent problems
- Measure comprehension: Can 3 developers execute after pruning?
- One pruning pass per Issue (not multiple)

**Reference**: [Issue #119](https://github.com/hoiung/dotfiles/issues/119) (failure), [Issue #131](https://github.com/hoiung/dotfiles/issues/131) (recovery)

---

### Scenario 3: Housekeeping Cleanup Failure

**Symptoms**:
- Self-healing rollback completes
- Temp files remain in repository
- Confusion about current state (which files are active?)

**Root Cause**: Rollback doesn't include housekeeping step

**Recovery Steps**:
1. Check Issue for all files created/modified during failed attempt
2. List: `git diff --name-only [commit-before]..[commit-after]`
3. Delete temp files: `rm -rf temp/[issue-number]-*`
4. Verify: `git status` shows clean working directory
5. Document artifacts in Issue comments

**Prevention**:
- Add housekeeping step to rollback process (commit 2eff589)
- Create temp files in `temp/` directory (easy to identify)
- Document all created files in Issue during work
- Use naming convention: `temp/[repo]-[issue]-[description].md`

**Reference**: [Issue #108](https://github.com/hoiung/dotfiles/issues/108) (lesson learned)

---

### Scenario 4: Combined Scope Creep

**Symptoms**:
- Single Issue has multiple change types (feature + optimization)
- Bug found after merge, hard to isolate cause
- Rollback loses good work

**Root Cause**: Multiple change types in one Issue

**Recovery Steps**:
1. Identify separate concerns (feature vs optimization vs refactor)
2. Git diff to separate changes by type
3. Create new branches for each concern
4. Cherry-pick commits by change type
5. Create separate Issues for each type

**Prevention**:
- One change type per Issue
- Feature addition = separate Issue from optimization
- Refactoring = separate Issue from new functionality
- Easier rollback, clearer git history

**Reference**: [Issue #124](https://github.com/hoiung/dotfiles/issues/124) (combined feature + optimization)

---

### Scenario 5: Frozen Subagent

**Symptoms**:
- Main agent reports "subagent running"
- No progress for >5 minutes
- API usage not increasing (monitor plan limits)

**Root Cause**: Subagent crashed/stuck but main agent doesn't detect

**Recovery Steps**:
1. Check API usage: If not increasing, subagent is frozen
2. Kill subagent: `Ctrl+C` or close Task panel
3. Review objective: Was it clear? Too broad?
4. Relaunch with clearer, narrower objective
5. Monitor: API usage should increase immediately

**Prevention**:
- Monitor API usage during subagent execution
- Timeout: If no progress in 10 minutes, kill and relaunch
- Clear objectives: Specific deliverable, success criteria
- Test: Can you execute objective manually? If not, subagent can't either

**Reference**: [Issue #119](https://github.com/hoiung/dotfiles/issues/119) (user observation)

---

### Scenario 6: Documentation Drift

**Symptoms**:
- Subagents execute incorrectly despite "following instructions"
- Instructions describe old behavior
- Reality doesn't match documentation

**Root Cause**: Docs updated separately from implementation changes

**Recovery Steps**:
1. Audit all affected documentation files
2. Compare documented behavior vs actual behavior
3. Update docs to match current implementation
4. Cross-reference: Check related files for consistency
5. Test: Run task following updated docs

**Prevention**:
- Single source of truth (dotfiles)
- Auto-generate docs from code when possible
- Update docs in same commit as behavior change
- Stage 4 verification: Check docs match implementation

**Reference**: [Issue #119](https://github.com/hoiung/dotfiles/issues/119) (pruning caused drift)

---

### Scenario 7: Guardrail Removal

**Symptoms**:
- Pruning removes "redundant" instructions
- Problem recurs that guardrail prevented
- New issue created for same problem

**Root Cause**: Not recognizing guardrail purpose (prevents problem)

**Recovery Steps**:
1. Check ANTI-PATTERNS.md for related patterns
2. Review Issue history: When was this problem last seen?
3. Restore guardrail instruction
4. Add comment explaining WHY guardrail exists (link to Issue)
5. Cross-check other guardrails for similar removals

**Prevention**:
- Before deleting, search Issues for why instruction was added
- Check ANTI-PATTERNS.md: Does deletion enable known pattern?
- If instruction prevents documented problem, it's a guardrail (keep it)
- Comment guardrails with Issue references

**Reference**: [Issue #108](https://github.com/hoiung/dotfiles/issues/108) (lesson learned)

---

### Scenario 8: Missing Baseline

**Symptoms**:
- Optimization task without before measurement
- Can't determine if optimization helped or hurt
- Subjective "feels faster" vs quantitative proof

**Root Cause**: No baseline requirement in Stage 2

**Recovery Steps**:
1. Measure current state (after optimization)
2. Document: "Baseline not measured, after-only data available"
3. Note uncertainty in retrospective
4. For future: Require baseline before optimization
5. If critical: Rollback, measure baseline, re-run optimization

**Prevention**:
- Stage 2 planning: "For optimizations, measure baseline first"
- Document measurement commands in Issue
- Compare before/after in Stage 4 verification
- Effect size calculation (not just "is it better?")

**Reference**: [Issue #128](https://github.com/hoiung/dotfiles/issues/128) Bug #3

---

## Rollback Procedure

**When to rollback**:
- Self-healing change causes new problems
- Verification fails after applying fix
- More issues created than solved

**Rollback Strategy Decision**:
1. **Assess commit atomicity**:
   - **Clean commit** (ONLY changes to roll back): Use `git revert <hash>` (fast, safe)
   - **Mixed commit** (good + bad changes): Extract good changes FIRST, then revert
2. **For clean commits**:
   ```bash
   git revert <commit-hash>
   # Verify tests pass after revert
   ```
3. **For mixed commits** (CAREFUL - manual extraction required):
   ```bash
   # Option A: Cherry-pick good changes to new branch
   git checkout -b recovery-good-changes
   git cherry-pick -n <mixed-commit-hash>
   # Manually remove bad changes from staging
   git reset HEAD <bad-files>
   git checkout -- <bad-files>
   git commit -m "Extract good changes from <hash>"

   # Option B: Manual diff review
   git show <mixed-commit-hash> > changes.diff
   # Review diff, apply good parts manually
   ```

**Steps**:
1. **Immediate**: Apply rollback strategy (see above)
2. **Housekeeping**: Check Issue for created/modified files
   - List: `git log --name-status [hash]`
   - Delete temp files: `rm -rf temp/[issue]-*`
   - Remove untracked files from failed attempt
3. **Verify rollback didn't break working code**:
   - Run tests: `pytest` or `npm test`
   - Check application still runs
   - Verify good changes preserved (if mixed commit)
4. **Document**: Create new Issue with failure analysis
   - What was attempted
   - What went wrong
   - Why rollback was necessary
   - Commit atomicity (clean vs mixed)
5. **Learn**: Add to Common Mistakes in relevant stage file

**Prevention for Future** ([Issue #374](https://github.com/hoiung/dotfiles/issues/374)):
- **Atomic commits**: One logical change per commit (enables clean rollback)
- **Separate debug commits**: Label with "debug:" prefix (easy to revert)
- **Stage 3 Item 6**: Follow atomic commit guidance

**See**: `../dotfiles/SST3/standards/STANDARDS.md` (Rollback Cleanup section)

---

## Pre-Flight Checklist

**Before applying self-healing change**:

- [ ] **JBGE Test**: Does this change prevent a documented problem?
- [ ] **Guardrail Check**: Cross-reference ANTI-PATTERNS.md
- [ ] **Scope Check**: One change type only (not feature + optimization)
- [ ] **Baseline Check**: For optimizations, is baseline measured?
- [ ] **Consistency Check**: Does this match related sections?
- [ ] **Validation Plan**: How will we verify this fix works?

---

## Early Detection Warning Signs

| Warning Sign | Likely Scenario | Action |
|--------------|----------------|---------|
| Automated test FAIL, human says PASS | Verification False PASS | Stop, audit verification process |
| Developers can't follow docs | Over-Pruning | Stop pruning, restore examples |
| Untracked files after rollback | Housekeeping Failure | Run cleanup, document artifacts |
| Issue has "and" in title | Scope Creep | Split into separate Issues |
| API usage flat for 5+ min | Frozen Subagent | Kill and relaunch with clearer objective |
| Subagent says "followed instructions but wrong result" | Documentation Drift | Audit docs vs implementation |
| Deleting from "Common Mistakes" section | Guardrail Removal | Check if prevents documented problem |
| Optimization without baseline | Missing Baseline | Measure before proceeding |

---

## Safety Guardrails

**NEVER**:
- Remove checklist items (guardrails)
- Change stage order (breaks workflow)
- Skip Stage 4 verification (85% bug catch rate)
- Override BLOCKING failures manually

**ALWAYS**:
- Test self-healing changes (meta-test when possible)
- Document rollbacks in new Issues
- Run pre-flight checks before applying
- Verify quality didn't degrade after change

---

## Effectiveness Target

**Goal**: <1 instruction gap per issue after 20 issues

**Measurement**:
- Track issues where subagents couldn't execute due to unclear instructions
- Percentage should decrease over time
- If increasing: Self-healing is making things worse (stop and audit)

**Meta-Validation**: Self-healing should improve quality, not degrade it

---

## References

- [Issue #108](https://github.com/hoiung/dotfiles/issues/108): Housekeeping lesson, JBGE/LMCE compliance
- [Issue #119](https://github.com/hoiung/dotfiles/issues/119): Pruning death spiral, frozen subagents
- [Issue #124](https://github.com/hoiung/dotfiles/issues/124): Verification false PASS, scope creep
- [Issue #128](https://github.com/hoiung/dotfiles/issues/128): Automated enforcement, baseline requirement
- [Issue #131](https://github.com/hoiung/dotfiles/issues/131): Quality First, restoration strategy

---

*Self-healing must validate itself - measure before/after effectiveness*
