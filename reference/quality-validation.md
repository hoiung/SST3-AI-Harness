# Quality Validation Framework

> Concrete PASS/FAIL criteria for SST3's 5 quality dimensions. Failure case examples drawn from Issues #124 (false PASS) and #128 (fix).

## 5 Dimensions (Check ALL)

1. Readability
2. Completeness
3. Correctness
4. Consistency
5. Effectiveness

## Rule

If ANY dimension fails: SKIP change.

---

## 1. Readability

**What to check**:
- Clear language (no ambiguity)
- Logical structure (easy to follow)
- Appropriate detail level (not too verbose/terse)

**PASS Example: Issue #128 Section 3.5.1**
```bash
# Check for BLOCKING failures
if grep -q "BLOCKING" discoverability_output.txt; then
    echo "FAIL: BLOCKING failure detected"
    exit 1
fi
```
- Concrete bash script with clear steps
- Exit code checking explained
- No jargon, directly actionable

**FAIL Example: Compressed Documentation**
- "Check discoverability" (how? what's passing criteria?)
- "Verify content preservation" (what tests? what's acceptable?)
- Assumes knowledge, multiple interpretations possible

**Common Mistakes**:
- Using jargon without definitions
- Omitting success criteria ("check X" without "X passes if...")
- Too abstract ("ensure quality" - what does that mean?)

---

## 2. Completeness

**What to check**:
- All critical information present
- No missing steps or context
- Edge cases addressed

**PASS Example: Issue #128 Section 5.5 Use Case Testing**
```markdown
**Use Case 1**: Developer needs to verify BLOCKING failures
- Can they accomplish this with new version? YES
- Evidence: Section 3.5.1 bash script + exit code check

**Use Case 2**: Developer needs to assess >100 line deletions
- Can they accomplish this with new version? YES
- Evidence: Section 5.5 comprehension testing framework

**Use Case 3**: Developer needs baseline measurements
- Can they accomplish this with new version? YES
- Evidence: Section 4.5 baseline requirement + git diff commands
```
- 3 use cases with YES/NO answers
- Evidence for each claim
- Before/after validation

**FAIL Example: Issue #124 Content Preservation**
- freeze-detection.md [archived]: 4,186 words → 207 words (95% deletion)
- Stage 4 reported: "Content Preservation: PASS"
- Reality: No use case testing, no comprehension check
- Result: Documentation destroyed, unusable

**Common Mistakes**:
- Spot-checking without comprehension testing
- Assuming "looks reasonable" means complete
- Missing edge cases (>100 line deletions need different validation)

---

## 3. Correctness

**What to check**:
- Information is accurate
- No false positives/negatives
- Clear pass/fail criteria (not subjective)

**PASS Example: Stage 4 BLOCKING Detection**
```bash
# Automated, no manual interpretation
exit_code=$(python check-discoverability.py)
if [ $exit_code -eq 1 ] && grep -q "BLOCKING" output.txt; then
    echo "FAIL: Cannot merge - BLOCKING failure"
    exit 1
fi
```
- Quantitative: exit code 0=pass, 1=fail
- Automated keyword parsing
- No manual override allowed

**FAIL Example: Issue #124 Severity Assessment**
- check-discoverability.py output: "BLOCKING: Cannot merge PR"
- Stage 4 assessment: "ACCEPTABLE (95%, pre-existing gaps)"
- Manual override of BLOCKING → incorrect result
- No quantitative criteria for "acceptable"

**Common Mistakes**:
- Subjective criteria ("looks good", "acceptable", "reasonable") — **If detected: replace with quantitative gate (exit code, regex match, percentage threshold).**
- Manual interpretation of automated results (defeats automation) — **If detected: remove the manual override path; let automation be authoritative.**
- No clear threshold — **Completeness numeric threshold: ≥3 of 5 dimensions PASS = warning, ≥4 = pass, 5 = clean. <3 = block.**

---

## 4. Consistency

**What to check**:
- Matches related sections (format, structure)
- Terminology used consistently
- No conflicting instructions

**PASS Example: Issue #128 Format Consistency**
```markdown
## Section 3.5.1: Automated Enforcement
**Purpose**: [Why this section exists]
**Implementation**: [How to do it]
- Checklist item 1
- Checklist item 2
**Common Mistakes**: [What not to do]
**References**: [Related sections]
```
- Matches surrounding section format
- Same heading hierarchy (##, ###)
- Consistent checklist structure

**FAIL Example: Mixed Terminology**
- File uses "Stage 5" and "Verification" interchangeably
- One section uses "PASS/FAIL", another uses "✓/✗"
- Checklist format varies (bullet points vs numbered vs tables)
- Creates confusion about what's required

**Common Mistakes**:
- Not checking adjacent sections for format
- Using different terms for same concept
- Varying detail levels (one section verbose, another terse)

---

## 5. Effectiveness

**What to check**:
- Will this actually solve the problem?
- Can users execute successfully?
- Prevents documented failures?

**PASS Example: Automated Scripts > Manual Checklists**
```bash
# Issue #128 replaced manual checklist...
# Manual: "Did you check for BLOCKING?" (humans say yes even when false)

# ...with automated script:
grep -q "BLOCKING" output.txt && exit 1  # Cannot be circumvented
```
- Enforcement mechanism (exit code)
- Measurable outcome (grep found keyword or not)
- Prevents Issue #124 scenario (manual override)

**FAIL Example: Manual Checklist Only**
```markdown
## Stage 4 Verification (Before Issue #128)
- [ ] Check discoverability (did you run script?)
- [ ] Check content preservation (does it look OK?)
- [ ] Check for BLOCKING failures (any issues?)
```
- No enforcement (user can check boxes falsely)
- Subjective assessment ("looks OK")
- Result: Issue #124 false PASS despite 95% deletion + BLOCKING failure

**Common Mistakes**:
- Assuming checklists prevent problems (humans override)
- No quantitative validation (can't measure if it worked)
- Missing enforcement mechanism (nothing blocks bad changes)

---

## Quality Gates

Apply validation at multiple levels. **Mandatory vs optional**:

- **Per-Change** (MANDATORY, every modification): 5 checks before applying.
- **Per-File** (MANDATORY when modifying >1 file): End-to-end review after file complete.
- **Per-Phase** (MANDATORY at phase boundaries): Quality validation after each self-healing function.
- **System-Wide** (MANDATORY pre-merge only): Comprehensive audit before merge to main.
- **Cross-Repo** (OPTIONAL, only when SST3 source changes): Parallel validation in all repos.

## Validation Checklist

```markdown
## Quality Check: [Change Description — one sentence, e.g., "Add bash script to Section 3.5.1"]

1. [ ] Readability: Clear language? Logical structure? Appropriate detail?
2. [ ] Completeness: All info present? No missing steps? Edge cases addressed?
3. [ ] Correctness: Accurate? Clear pass/fail? No subjective criteria?
4. [ ] Consistency: Matches related sections? Consistent terminology? No conflicts?
5. [ ] Effectiveness: Solves problem? Users can execute? Prevents failures?

**Result**: PASS / FAIL
**Action**: Apply / Skip / Revise

**Evidence**: [Link to examples above for each dimension]
```

---

## References

- Issue #128: Automated enforcement > manual checklists
- Failed Issue #124: What happens when validation fails

**Automated Validation**: See `../scripts/quality-check.py`
