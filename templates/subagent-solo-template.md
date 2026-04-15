# SST3 Solo Execution Template

## Task: [Brief Description]

**Issue**: #[number] OR "Ad-hoc: [description]"
**Goal**: [Specific objective]

---

## Execution Guardrails (MANDATORY)

Read `../standards/STANDARDS.md` and `[repository]/CLAUDE.md` in full before starting. All work must follow Quality First, JBGE, LMCE, Fail Fast, Use Existing Before Building, Modularity (defined in STANDARDS.md). Git workflow per `../templates/issue-template.md` Solo Assignment section: commit per file, never `git add -A`, merge to main BEFORE user review.

### Before Starting Work
- [ ] Read CLAUDE.md in full
- [ ] Read STANDARDS.md in full
- [ ] Read Issue line-by-line (not skim)
- [ ] List 3-5 key scope items as evidence of reading
- [ ] Create solo branch: `git checkout -b solo/issue-{number}-{description}`

### During Work (At Each Phase Checkpoint)
- [ ] **Post checkpoint to Issue comment** with:
  - Phase completed
  - Files modified
  - Key changes made
  - Any blockers or scope changes
- [ ] **Check context memory**: Keep going. 1M context window exists to be used. Stop ONLY at 80%+ used, destructive-action consent, genuinely stuck, or task complete (STANDARDS.md "Keep Going Until Done")
- [ ] **Commit after EACH file change**: `git add {file} && git commit -m "type: description (#issue)" && git push`

### After Compact (Context Recovery)
- [ ] Re-read CLAUDE.md
- [ ] Re-read STANDARDS.md
- [ ] Re-read Issue (or last checkpoint comment)
- [ ] Continue from last checkpoint

---

## CRITICAL Context (Always Include)

**temp/ Files**: Use `C:/temp/[repo]-adhoc-[description].ext` for ANY temporary files
**Repository**: Work in [repo-name]/ only, NO temp/analysis folders created in repo
**Housekeeping**: Document all files you CREATE/MODIFY in Issue #[number] OR final report
**Code Hygiene**: Remove debug code (console.log, print, debug flags), abandoned implementations, partial work from scope changes

---

## Verification Loop (MANDATORY - Repeat Until Clean)

> Canonical: [`SST3/workflow/WORKFLOW.md` "## Verification Loop"](../workflow/WORKFLOW.md#verification-loop). Run that loop here. Don't restate it. (#406 F3.6 dedup — single source of truth.)

- [ ] Verification Loop run, all checks pass per WORKFLOW.md canonical list

---

## Update Checkboxes Progressively

```python
mcp__github-checkbox__update_issue_checkbox(
    issue_number=[NUMBER],
    checkbox_text="[Exact checkbox text without [ ] prefix]",
    evidence="[Concise proof: what you did, key results]"
)
```

**Evidence Format**:
- **Quick fix**: `Fixed [issue] in [file]: [1-line description]`
- **File edit**: `Updated [file] lines [X-Y]: [change]`
- **Validation**: `Verified [criteria]: [result]`

---

## Final Report Requirements

End final message with these sections:

1. **Files Created**: Full paths (or "none")
2. **Files Modified**: Full paths with line ranges
3. **Issue Updates**: Links to all comments posted
4. **Quality Checks**: Quality First, JBGE, LMCE, Fail Fast, Modularity
5. **Verification Loop**: Passed/Failed (if failed, what was fixed)

---

## Deliverables

- [ ] [Specific output 1]
- [ ] [Specific output 2]
- [ ] [Specific output 3]

---

## Success Criteria

- [ ] [Criterion 1]
- [ ] [Criterion 2]
- [ ] [Criterion 3]

---

## Merge & User Review (MANDATORY)

- [ ] Run Ralph Review (Haiku → Sonnet → Opus)
- [ ] Merge branch to main (BEFORE user review - protects work)
- [ ] POST user-review-checklist.md to user in chat
- [ ] Work through checklist WITH user
- [ ] **WAIT** for user approval
- [ ] User approves
- [ ] Cleanup branch (delete local and remote)
- [ ] Close Issue
