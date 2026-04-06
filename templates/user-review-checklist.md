# User Review Checklist - MANDATORY Post-Implementation Walkthrough

**Purpose**: Validate implementation quality through collaborative user review
**Mode**: PLANNING MODE ONLY - This checklist MUST be posted to Issue as comment
**Timing**: After merge to main, before Issue closure
**Cannot Skip**: Required for all Issues

---

## 1. Scope Verification

**Did we build what was requested?**

| Aspect | Planned (from Issue) | Actually Built | Match? | Notes |
|--------|---------------------|----------------|--------|-------|
| Core Feature | [What was the main ask?] | [What was implemented?] | Yes/No/Partial | [Explain any gaps] |
| Acceptance Criteria | [List each criterion from Issue] | [Status of each] | Yes/No/Partial | [Any deviations] |
| File Changes | [Expected files] | [Actual files modified/created] | Yes/No/Partial | [Missing/extra files] |
| Integration Points | [Expected touchpoints] | [Actual integrations] | Yes/No/Partial | [Any orphaned code] |
| Data Migrations / Corrections | [List each data item to change] | [Verified each row/query ran and affected expected count] | Yes/No/Partial | [Row counts or query output] |

**Data Correction Verification** (if scope includes data fixes):
- [ ] For each data correction item: run a COUNT or SELECT to confirm expected rows were changed
- [ ] `SELECT COUNT(*) FROM table WHERE condition` — compare before/after counts
- [ ] If correction was a script: show script output with rows affected, not just "ran successfully"

**If ANY "No" or "Partial"**:
- Determine if acceptable (scope change documented in Issue) or defect (needs fix)
- Create follow-up Issue if significant work remains
- Document rationale for scope changes

---

## 2. Context Checkpoint - What Future Sessions Need

**What should be preserved for AI session handoffs?**

### Format (Post to Issue as comment before compaction)
```markdown
## Context Checkpoint - Issue #[NUMBER]

### What Was Built
[1-2 sentence summary of implementation]

### Key Files Modified/Created
- `path/to/file1.py` - [what changed and why]
- `path/to/file2.md` - [what changed and why]

### Critical Context for Future Sessions
1. [Most important architectural decision and rationale]
2. [Any non-obvious dependencies or requirements]
3. [Known limitations or edge cases to be aware of]

### Follow-Up Issues Created
- #[NUM] - [Brief description]

### Testing Evidence
[How to verify this works - commands to run, expected output]

### Closure Readiness
- [x] All acceptance criteria met
- [x] Cross-issue impacts resolved
- [x] Fail Fast Audit passed
- [x] Post-Implementation Review passed
- [x] User approves closure
```

### Checkpoint Timing
1. [ ] Post checkpoint BEFORE user compacts Issue
2. [ ] User compacts (removes conversation noise)
3. [ ] Re-read Issue's last comment (the checkpoint)
4. [ ] User approves closure based on checkpoint summary
5. [ ] Issue closed

---

## 3. Gap Analysis — No Excuses Gate

**What was left out and why?**

> **CRITICAL RULE**: Only confirmed false positives can be skipped. If a test finds a problem, FIX IT. "Pre-existing", "not in scope", "low priority" are NOT valid reasons to defer.

### Items Not Fixed
For each item NOT fixed, answer:
- [ ] Is this a confirmed false positive? (Yes/No)
- [ ] If No: **STOP** — fix it now before proceeding. No deferrals, no excuses.
- [ ] If Yes: Document WHY it's a false positive with evidence.

### Discovered During Implementation
- [ ] List any issues/improvements discovered during implementation
- [ ] For each: Was it fixed? (Yes = good. No = must be confirmed false positive with evidence)

### Data Correction Completeness (if applicable)
For any issue scope that included data corrections, fixes, or migrations:
- [ ] List every correction item from the issue body
- [ ] For each item: provide the verification query and its output
- [ ] "Done" is only accepted with row-count or diff evidence — not self-report

### Factual Claims Verification
For any number, ratio, or capacity claim appearing in this issue's documentation or design rationale:
- [ ] List every quantified claim made
- [ ] For each: what is the source? (command, reference, calculation)
- [ ] Self-reported estimates must be labelled as estimates, not presented as facts
- [ ] "Seems reasonable" is not a source — flag and fix

**Principle**: Everything real gets fixed. No such thing as high/low priority. The only valid skip is a confirmed false positive.

---

## 4. How It Works - Plain English Explanation

**Can you explain the implementation without jargon?**

### User-Facing Behavior
[Explain what a user would see/experience with this change. Use concrete examples.]

### Technical Flow (High-Level)
[Explain the implementation approach in 3-5 steps. Focus on the "happy path".]

### Key Design Decisions
[List 2-3 important choices made during implementation and why]

**If you can't explain it simply, the implementation might be too complex.**

---

## 5. Cross-Issue Impact - BODY Edits Required

**Did insights from this Issue need to update other Issues?**

### Run Validation Script
```bash
python SST3/scripts/check-issue-body-vs-comments.py --issue [CURRENT_ISSUE_NUMBER]
```

**If script returns violations**: Fix IMMEDIATELY before closing Issue

### Common Cross-Issue Updates
- [ ] Found bug in related Issue → Update that Issue's BODY with findings
- [ ] Discovered new requirement → Add to dependent Issue's BODY checklist
- [ ] Implementation revealed blocker → Update blocked Issue's BODY status
- [ ] Learned new pattern → Update template/guide Issue's BODY

**CRITICAL RULE**: Insights go in BODY, not comments
- Comments are for discussion (temporal, context-dependent)
- Body is for facts (permanent, search-discoverable)
- If information changes task definition, it MUST update the body

### Validation Steps
1. [ ] Run check-issue-body-vs-comments.py script
2. [ ] Review script output for Issues needing body edits
3. [ ] Edit each flagged Issue's body (NOT comment) with insights
4. [ ] Re-run script to confirm exit code 0

---

## 6. Discoverability Check

**Can future sessions find and understand this work?**

### File Discoverability
- [ ] New files follow naming conventions (check SST3/STANDARDS.md)
- [ ] Files are in logical locations (scripts in scripts/, templates in templates/)
- [ ] No orphaned temp files left behind

### Code Discoverability
- [ ] Complex logic has inline comments explaining "why" not "what"
- [ ] Magic numbers/strings extracted to named constants

### Documentation Discoverability
- [ ] README updated if public interface changed
- [ ] Related Issues cross-linked in this Issue's body

### Search Discoverability
- [ ] Issue title is descriptive (can you find it searching?)
- [ ] Key terms appear in Issue body (not just comments)
- [ ] Tags/labels applied appropriately

**Test**: If you searched for this feature in 6 months, would you find this Issue?

---

## 7. Fail Fast Audit (CRITICAL - 80% of failures come from here)

**Did the implementation add any of these anti-patterns?**

| Anti-Pattern | What to Look For | Found? | Location |
|--------------|------------------|--------|----------|
| Backwards compatibility hacks | `@deprecated`, `_oldVar` renames, re-exports "for compatibility", shim layers | Yes/No | [file:line] |
| Default fallbacks | `or default`, `if None: use X`, `getattr(x, 'y', default)`, `.get('key', 'default')` | Yes/No | [file:line] |
| Silent failures | `except: pass`, `except Exception: continue`, returns None instead of raising | Yes/No | [file:line] |
| Hardcoded backend settings | Magic numbers, embedded paths/URLs in Python - should be YAML config | Yes/No | [file:line] |
| Hardcoded frontend settings | Inline styles, magic colors/sizes in JSX - should be CSS variables | Yes/No | [file:line] |
| Non-modular / duplicated logic | Same calculation in multiple places - should consolidate | Yes/No | [file:line] |
| Fake/mock/placeholder data | Hardcoded test data, mock responses in prod code | Yes/No | [file:line] |
| SQL value correctness | Enum/status string literals in queries — `side='SLD'`, `status='CANCELED'` — verify against actual DB enum values or allowed values for that column | Yes/No | [file:line] |
| None propagation chain | Value from one function passed through 2+ functions without null guard — crash deferred to deepest callee | Yes/No | [file:line] |
| Dead try/except | `try/except` wrapping code that cannot raise the caught exception — verify callee actually raises | Yes/No | [file:line] |
| Frontend null path | JSX rendering user-supplied or API-supplied values without null/undefined check — tooltip content, label, count fields | Yes/No | [file:line] |
| Duplicate CSS class | Same class applied twice on same element — `className="foo foo"` or spread props + explicit class overlap | Yes/No | [file:line] |

**If ANY "Yes" found**: Fix before closing Issue. No follow-up Issues for anti-patterns — fix NOW.

### Audit Steps
1. [ ] Search for `@deprecated`, `compat`, `backwards` (compatibility hacks)
2. [ ] Search for `or `, `.get(`, `getattr(` patterns (default fallbacks)
3. [ ] Search for `except:` or `except Exception:` (silent failures)
4. [ ] Search backend for magic numbers not in YAML config
5. [ ] Search frontend for inline styles not using CSS variables
6. [ ] Search for duplicated calculations/logic across files
7. [ ] Review each finding - fix or justify (justification is rare)
8. [ ] SQL value check: for every string literal in a WHERE/INSERT/UPDATE, confirm value matches DB enum or allowed values
      `grep -rn "side=\|status=\|type=\|action=" src/ --include="*.py"` — for each, run `SELECT enum_range(NULL::<type>)` or check migration
9. [ ] None propagation: for each function that can return None, trace ALL callers — does each guard before passing result onward?
      `grep -rn "def get_\|def fetch_\|def find_\|-> Optional" src/ --include="*.py"` — for each, check every callsite
10. [ ] Dead try/except: for each `try/except` block, read the wrapped function and confirm it can raise the caught exception type
      `grep -rn "^    try:" src/ --include="*.py" -A 5`
11. [ ] Frontend null safety: every JSX expression that renders API/prop data — check for missing `?.` or `?? ''` guards
      `grep -rn "tooltip\|title={\|label={\|count={\|value={" src/ --include="*.tsx" --include="*.jsx"`
12. [ ] Duplicate CSS: check for same class name appearing twice in one `className` string, or spread + explicit overlap
      `grep -rn "className=" src/ --include="*.tsx" --include="*.jsx" | grep -E '"[^"]*\b(\w+)\b[^"]*\b\1\b[^"]*"'`

---

## 8. Modular Architecture Review

**Is the implementation maintainable and extensible?**

| Criteria | What to Check | Pass? | Evidence |
|----------|---------------|-------|----------|
| Backend config externalized | Settings in YAML config files, not hardcoded in Python | Yes/No | [config file path] |
| Frontend config externalized | Colors/sizes in CSS variables, not inline styles in JSX | Yes/No | [CSS file path] |
| Extensible | Can add features without major refactor | Yes/No | [architecture notes] |
| Removable | Can disable/remove component without breaking system | Yes/No | [dependency check] |
| Clear interfaces | Functions/classes have defined contracts | Yes/No | [API docs] |
| Single responsibility | Each component does one thing well | Yes/No | [component list] |
| Config fully consumed | Every key defined in YAML config is actually read by code — no orphan config keys | Yes/No | [grep evidence] |

**Config Consumption Audit**:
```bash
# Extract all config keys defined in YAML (adjust path as needed)
grep -rEn "^\s+\w+:" config/*.yaml

# For each key, verify it appears in backend code
# Example: grep -rn "config\['key_name'\]\|config\.get('key_name')\|\.key_name" src/
```
- [ ] Every config key in YAML has at least one consumer in code
- [ ] If a key has no consumers: remove it or fix the missing wiring — orphan config is dead code

---

## 9. Post-Implementation Review Gate (Stage 5)

> **MANDATORY**: This section enforces Stage 5 of the 5-stage workflow. Subagent swarm review, not inline main agent review.

### Subagent Swarm Review Confirmation
- [ ] Post-implementation review done by subagent swarm (NOT inline by main agent)
- [ ] Phase-by-phase review against issue body scope + goal alignment + design doc
- [ ] **Wiring check**: Every new function/class actually called from correct caller — no orphaned implementations
      TECHNIQUE: For each new `def function_name` or `class ClassName`, run:
      `grep -rn "function_name\|ClassName" src/` — confirm callsite exists per required entry point
      For startup-required functions: explicitly check `__init__`, `startup()`, `on_connect()`, `main()` — not just feature paths
- [ ] **SQL schema check**: Every column name in every new/modified SQL query exists in the actual table schema, and every string literal value matches DB enum/allowed values
      TECHNIQUE: `\d table_name` in psql — compare query columns against schema output
      For enums: `SELECT enum_range(NULL::<enum_type>)` — compare against literal values in queries
- [ ] **Bottleneck scan**: No DB queries in loops, no N+1, no unbounded iteration, no redundant fetches of the same data
      TECHNIQUE: If the same table is queried 2+ times within one function/request path, justify or consolidate
      `grep -n "SELECT\|\.execute\|\.query" file.py` — flag duplicate table access
- [ ] **Memory leak scan**: No unclosed connections, no growing collections, no missing cleanup
- [ ] **Deduplication check**: Checked against EXISTING codebase (not just within new code)
- [ ] **STANDARDS.md re-read**: Confirmed during review phase (not just at session start)
- [ ] **Regression tests**: Written and run (not just CI passing)
- [ ] **Design doc alignment**: Implementation matches design/architecture from issue
- [ ] **Optimisation pass**: Could this be more efficient? If yes, fix now.
- [ ] **Issue body checkboxes**: 100% complete with evidence — every single one
- [ ] Quality mantras verified: no inefficiencies, fix optimisations, reliable/robust, dedupe, no bottlenecks, fast/safe, no memory leaks, follows STANDARDS.md
- [ ] Fix ALL problems found — no deferrals, no excuses unless confirmed false positive

### Ralph Review Evidence
- [ ] Ralph Review completed: HAIKU_PASS received (evidence: ___)
- [ ] Ralph Review completed: SONNET_PASS received (evidence: ___)
- [ ] Ralph Review completed: OPUS_PASS received (evidence: ___)

---

## 10. Closure Gate - Final Checklist

**All conditions met before closing Issue?**

### Technical Completion
- [ ] All file changes implemented per issue plan
- [ ] All checkboxes in Issue marked complete with evidence
- [ ] Commit-per-file discipline followed
- [ ] Merged to main BEFORE user review (protects work)
- [ ] Pre-commit hooks pass
- [ ] Regression tests pass

### Quality Gates
- [ ] Scope Verification: All items "Yes" or justified (Section 1)
- [ ] Gap Analysis: No deferrals except confirmed false positives (Section 3)
- [ ] Cross-Issue Impact: check-issue-body-vs-comments.py exit 0 (Section 5)
- [ ] Discoverability: Can future sessions find this work? (Section 6)
- [ ] Fail Fast Audit: No violations (Section 7)
- [ ] SQL correctness: column names verified against schema, string literal values match DB enums (Section 7 + 9)
- [ ] None-chain safety: every None-returning function's callers guard before chaining (Section 7)
- [ ] Config consumption: all YAML config keys consumed by code — no orphan keys (Section 8)
- [ ] All required callsites verified: startup + every entry point calls new functions (Section 9)
- [ ] Modular Architecture: All "Yes" (Section 8)
- [ ] Post-Implementation Review: All checks pass (Section 9)

### User Approval
- [ ] User has reviewed checkpoint summary
- [ ] User explicitly approves closure
- [ ] No outstanding questions or concerns

**If ALL checkboxes complete**: Close Issue
**If ANY incomplete**: Resolve blocker. DO NOT close until all gates pass.

---

## Usage Instructions

### Usage
Post after Ralph Review passes and merge to main. Work through WITH user collaboratively. Fix all problems found — no deferrals. Get explicit user approval before closing.

---

**Template Version**: 2.1.0 (Added SQL correctness/schema checks, None-chain tracing, dead try/except, frontend null safety, duplicate CSS, config consumption audit, data correction evidence standard, startup wiring enumeration, redundant DB query detection)
**Last Updated**: 2026-04-01
