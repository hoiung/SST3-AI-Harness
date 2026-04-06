# SST3 Scripts

Automation scripts for SST3 workflow validation and enforcement.

**Note**: Python `__pycache__/` folders are normal and safe - .gitignore prevents committing them, and token counters exclude them (only `.md` files counted).


## Quick Reference

| Script | Purpose |
|--------|---------|
| [check-crossrepo-paths.py](../dotfiles/SST3/scripts/check-crossrepo-paths.py) | Pre-commit hook for cross-repo path validation |
| [check-retrospective-location.py](../dotfiles/SST3/scripts/check-retrospective-location.py) | Validates retrospective file locations |
| check-discoverability.py | Validates CLAUDE.md → SST3 chain (4 hops max). Pre-commit + Verification Loop. Exit 0 = clean, 1 = chain broken. |
| check-issue-body-vs-comments.py | Detects scope content placed in issue comments instead of issue body. Required by user-review-checklist Section 5. Exit 0 = clean, 1 = violations. |
| check-issue-checkboxes.py | Parses issue body+comments for checkbox state. Used by Verification Loop and MCP checkbox tools. |
| quality-audit.py | Runs `quality-check.py` against all SST3 markdown files. Pre-merge validation gate. |

## meta-test-validator.py

**Purpose**: Validates that SST3 workflow changes were tested on themselves ("test the tester").

**Usage**:
```bash
python meta-test-validator.py <issue-number> [branch-name]
```

**Examples**:
```bash
# Check if Issue #109 validated its SST3 changes
python meta-test-validator.py 109 feature/issue-109-testing-integration

# Check current HEAD
python meta-test-validator.py 110
```

**What It Checks**:
- If SST3 workflow files were modified
- If the modified stages were executed in the issue
- If meta-testing was documented
- If retrospective was saved (for Stage 5 changes)

**Exit Codes**:
- `0`: Validation passed (changes were tested)
- `1`: Validation failed (changes not tested)

**Integration with CI/CD**:
Add to `.github/workflows/sst3-validation.yml`:
```yaml
- name: Validate meta-testing
  run: |
    python SST3/scripts/meta-test-validator.py ${{ github.event.pull_request.number }} ${{ github.head_ref }}
```

**When to Run**:
- Before merging PRs that modify SST3 workflow
- During Stage 5 post-implementation review (manual check)
- As GitHub Action on PR creation (automated)

**Pattern**: "Test the tester" - new processes must test themselves first.

---

## cleanup-temp.py

**Purpose**: Automated cleanup for `C:/temp/` folder (cross-repo) based on issue status and file age.

**Usage**:
```bash
# From dotfiles repo:
python SST3/scripts/cleanup-temp.py              # Dry run (preview)
python SST3/scripts/cleanup-temp.py --execute    # Actually delete
python SST3/scripts/cleanup-temp.py --age 45     # Custom threshold

# From other repos (auto_pb_swing_trader, tradebook_GAS, etc.):
python ../cleanup-temp.py (current directory)
```

**Deletion Criteria**:
- Issue linked in filename is closed (via `gh` CLI), OR
- File age > threshold (default 30 days, customizable via `--age`)
- Conservative: keeps files when issue status unknown

**Filename Convention**:
- Format: `{repo}-{issue#}-{description}.{ext}`
- Examples: `dotfiles-121-api-design.md`, `auto_pb_swing_trader-122-test-data.json`

**Protected Files**:
- `README.md`, `.gitkeep`, `.gitignore` (never deleted)

**When to Run**:
- Periodically (weekly/monthly) for manual cleanup
- When `C:/temp/` folder grows too large
- Can be run from any repo (cleans shared temp/ folder)

**Requirements**:
- Python 3.6+
- GitHub CLI (`gh`) installed and authenticated
- Repository must be in a git directory

**Safe Defaults**:
- Dry run by default (requires `--execute` flag)
- Conservative logic (keeps files when issue status unknown)
- Clear preview of what will be deleted and why

**Location**:
- Script: `cleanup-temp.py (current directory)` (single source of truth)
- Target: `C:/temp/` (cross-repo shared folder)
- Run from any repo, cleans shared temp/ folder

---

## Shared Configuration

### sst3_limits.py
**Purpose**: Single source of truth for all SST3 token and line limits
**Used by**: check-size-limits.py, pre-commit hooks
**Maintenance**: Update limits only in sst3_limits.py

**Key values**:
- SST3_TOTAL_TARGET: 130,000 tokens (see `sst3_limits.py` for current values)
- SST3_TOTAL_CAP: 150,000 tokens (see `sst3_limits.py` for current values)
- CLAUDE.md: 500 lines (not tokens)
- Individual file caps: 2,000-4,000 tokens each

---

---

## auto-rollback.py

**Purpose**: Automated rollback for failed self-healing changes (Phase 4).

**Usage**:
```bash
# Preview (dry-run, default)
python SST3/scripts/auto-rollback.py <issue-number> --dry-run

# Execute rollback
python SST3/scripts/auto-rollback.py <issue-number> --execute

# With file preservation
python SST3/scripts/auto-rollback.py <issue-number> --execute --preserve-dir "C:/path/backup"
```

**Features**:
- Detects validation failures (Stage 4/5 FAIL, 0/3 validation)
- Dry-run mode (safe preview)
- Uses git revert (reversible, not reset)
- Preserves files before rollback
- Auto-documents in Issue and failed-experiments.md
- Confirmation prompt (unless --yes)

**Integration**: Stage 5 post-implementation review checks for validation failures, triggers auto-rollback if needed.

---

## check-failed-experiments.py

**Purpose**: Prevent "Fix-Revert-Fix" infinite loops by checking if proposed fixes have already failed validation (Phase 5 - Infinite Loop Prevention).

**Usage**:
```bash
# Check if fix should be applied
python SST3/scripts/check-failed-experiments.py "Always use UTF-8 encoding" --issue 119

# Add new failed experiment entry
python SST3/scripts/check-failed-experiments.py --add-failure "UTF-8 encoding" \
    --issue 119 --reason "Breaks Windows cp1252" --alternative "Check encoding first"

# List all failed experiments
python SST3/scripts/check-failed-experiments.py --list

# Get attempt count only
python SST3/scripts/check-failed-experiments.py "UTF-8 encoding" --count

# JSON output (for automation)
python SST3/scripts/check-failed-experiments.py "UTF-8 encoding" --issue 119 --json
```

**Exit Codes**:
- `0`: Safe to apply (not in failed experiments)
- `1`: Apply with modification (1-2 prior failures)
- `2`: PERMANENT BLOCK (3+ failures)
- `3`: Error (missing log file, parse error, etc.)

**Features**:
- Checks failed-experiments logs before applying fixes
- Implements 3-attempt threshold (PERMANENT BLOCK after 3 failures)
- Suggests alternative approaches based on failure history
- Supports both temp/ (per-issue) and .sst3-local/ (project-wide) logs
- JSON output for automation and CI/CD integration
- Inline unit tests (run with `--test` flag)

**Log Architecture**:
- `temp/{issue#}-failed-experiments.log`: Per-issue failures
- `.sst3-local/failed-experiments.log`: Project-level recurring patterns
- `../dotfiles/SST3/reference/failed-experiments.md`: Template and process guide

**Integration with Stage 5**:
Stage 5 post-implementation review uses this script before adding fixes to Common Mistakes:
```python
# Before adding to Common Mistakes
decision, reason = should_apply_fix("Always validate input encoding", 119)

if decision == False:
    print(f"BLOCKED: {reason}")  # Don't add to Common Mistakes
elif decision == "with_modification":
    alternative = suggest_modification("Always validate input encoding")
    print(f"WARNING: {reason}")
    print(f"ALTERNATIVE: {alternative}")  # Add modified version
else:
    print(f"SAFE: {reason}")  # Add with 3-issue validation
```

**Examples**:
```bash
# Example 1: Check new fix (safe)
$ python check-failed-experiments.py "New optimization approach" --issue 119
STATUS: SAFE
REASON: Not in failed experiments - safe to apply with 3-issue validation
EXIT: 0

# Example 2: Fix failed once before (modify)
$ python check-failed-experiments.py "UTF-8 encoding" --issue 125
STATUS: MODIFY
REASON: Failed 1 time(s) before - apply with modification
ALTERNATIVE: Check sys.stdout.encoding first
EXIT: 1

# Example 3: Fix failed 3+ times (block)
$ python check-failed-experiments.py "UTF-8 encoding" --issue 135
STATUS: BLOCK
REASON: PERMANENT BLOCK - Failed 3+ times (Issues #119, #125, #130)
ALTERNATIVE: Check sys.stdout.encoding, use UTF-8 only if supported
EXIT: 2
```

**Testing**:
```bash
# Run inline unit tests
python SST3/scripts/check-failed-experiments.py --test
```

**Related Documentation**:
- See `../dotfiles/SST3/reference/failed-experiments.md` for process guide
- See `temp/119-infinite-loop-findings.md` for detailed analysis
- Integration with auto-rollback.py for automatic failure tracking

---

## propagate-template.py

**Purpose**: Safely propagate SST3 template updates from CLAUDE_TEMPLATE.md to all project repositories while preserving project-specific configuration.

**Usage**:
```bash
# Dry run (recommended first)
python SST3/scripts/propagate-template.py --all --dry-run

# Single repository
python SST3/scripts/propagate-template.py --repo ../tradebook_GAS

# All repositories
python SST3/scripts/propagate-template.py --all
```

**How It Works**:
- Extracts SST3 section from CLAUDE_TEMPLATE.md (above boundary marker)
- Extracts project section from target CLAUDE.md (below boundary marker)
- Merges sections with boundary preserved

**Boundary Marker**: `<!-- ⚠️ DO NOT MODIFY OR DELETE ANYTHING ABOVE THIS LINE ⚠️ -->`

**Adding Repositories**: Edit `all_repos` list in script

**Recovery**: `git checkout CLAUDE.md`

---

## auto-stage-tracked-folders.py

**Purpose**: Pre-commit hook that automatically stages files in tracked folders (SST3-metrics, archive, docs) to prevent accidentally leaving them untracked.

**Usage** (automatic via pre-commit):
```bash
# Install hook
pip install pre-commit && cd dotfiles && pre-commit install

# Manual test
python SST3/scripts/auto-stage-tracked-folders.py
```

**Tracked Folders**:
- `SST3-metrics/` - Workflow metrics and retrospectives
- `archive/` - Archived files (superseded configs, deprecated docs)
- `docs/` - Research references and documentation

**Behavior**:
- Scans tracked folders for untracked and modified files
- Automatically stages all files in these folders
- Displays list of auto-staged files
- Never blocks commits (always exits 0)

**Rationale**: These folders should always be tracked. Files here are deliberate (not temp/working files). Auto-staging prevents forgotten documentation.

**Integration**: Configured in `.pre-commit-config.yaml` (local hook)

---

## validate-issue-template-compliance.py — ARCHIVED

> **Archived to `SST3/archive/scripts/`** (2026-04-01). Validated SST2 7-stage template structure (Stage 0-6 sections). Not compatible with SST3 Solo workflow — every Solo issue would fail validation.

---

## check-crossrepo-paths.py

**Purpose**: Pre-commit hook that validates cross-repo path format in SST3 markdown files to prevent discoverability issues.

**Usage**:
```bash
# Check for violations
python SST3/scripts/check-crossrepo-paths.py

# Show suggested fixes (dry-run)
python SST3/scripts/check-crossrepo-paths.py --fix

# Verbose output
python SST3/scripts/check-crossrepo-paths.py --verbose
```

**Problem Solved**:
When SST3 docs reference other SST3 files using repo-relative paths (e.g., `` `SST3/workflow/...` ``), those paths work from dotfiles repo but BREAK from other repos (auto_pb_swing_trader, tradebook_GAS). This makes SST3 features undiscoverable from other repos, violating the discoverability requirement.

**What It Checks**:
- Scans all SST3 markdown files (workflow/, templates/, reference/, standards/)
- Finds backticked paths that reference SST3 files WITHOUT `../dotfiles/` prefix
- Catches patterns like `` `SST3/` ``, `` `../templates/` ``, `` `../reference/` ``, `` `../workflow/` ``, `` `../standards/` ``
- These should be `` `../dotfiles/SST3/...` ``

**Exceptions**:
- Paths already using `../dotfiles/SST3/` (correct format)
- CLAUDE_TEMPLATE.md (intentionally uses repo-relative paths as a template)
- Code blocks showing "wrong" examples (prefixed with ❌ or "DON'T:")

**Exit Codes**:
- `0`: No violations found
- `1`: Violations found (BLOCKS commit)

**Integration**: Configured in `.pre-commit-config.yaml` (runs on SST3 markdown file changes)

**Reference**: See [Issue #298](https://github.com/hoiung/dotfiles/issues/298) for context

---

## check-propagation.py

## check-retrospective-location.py

**Purpose**: Validate that retrospectives are saved to the correct location (dotfiles/SST3-metrics/retrospectives/) and not scattered in wrong directories.

**Usage**:
```bash
# Check all retrospectives
python SST3/scripts/check-retrospective-location.py

# Verbose output
python SST3/scripts/check-retrospective-location.py --verbose
```

**Problem Solved**:
When retrospectives are saved with relative paths from wrong working directories, they end up scattered across DevProjects root or other repos instead of centralized in dotfiles/SST3-metrics/retrospectives/. This breaks cross-repo historical analysis.

**What It Checks**:
- Scans for retrospective files across all known locations
- Verifies files are in `dotfiles/SST3-metrics/retrospectives/` directory
- Detects misplaced retrospectives in DevProjects root or other repos
- Reports correct vs incorrect locations

**Exit Codes**:
- `0`: All retrospectives in correct location
- `1`: Misplaced retrospectives found (BLOCKS commit)

**Integration**: Can be added to pre-commit hooks to prevent saving to wrong location

**Reference**: Prevents issues like [Issue #110](https://github.com/hoiung/dotfiles/issues/110) where retrospectives were saved to wrong directory

---

**Purpose**: Pre-commit hook that detects CLAUDE template changes and prevents forgotten cross-repo propagation.

**Usage** (automatic via pre-commit):
```bash
# Install hook
pip install pre-commit && cd dotfiles && pre-commit install

# Manual test
pre-commit run check-claude-template-propagation --all-files
```

**Behavior**:
- Detects CLAUDE_TEMPLATE.md or CLAUDE.md in staged files
- Runs propagation dry-run automatically
- Offers to propagate: `[y/N/skip]`
- Never blocks commits (always exits 0)
- Warns if CLAUDE.md changed without template update

**Integration**: Configured in `.pre-commit-config.yaml` (local hook)

---

## check-fallbacks.py

**Purpose**: Automated detection of silent fallback patterns to enforce STANDARDS.md "Fail Fast, No Silent Fallbacks" principle.

**Usage**:
```bash
# Scan current directory
python SST3/scripts/check-fallbacks.py .

# Scan with exclusions
python SST3/scripts/check-fallbacks.py --exclude-dir tests --exclude "*.test.py" src/

# JSON output for CI/CD
python SST3/scripts/check-fallbacks.py --severity warning --json .

# Show help
python SST3/scripts/check-fallbacks.py --help
```

**What It Detects**:

Python:
- `dict.get("key", default)` - silent fallback on missing keys
- `os.getenv("VAR", "default")` - silent fallback on missing environment variables
- `value or "default"` - silent fallback on falsy values
- `value or []`, `value or {}` - silent fallback to empty collections

JavaScript/TypeScript:
- `value || "default"` - silent fallback with OR operator
- `value ?? "default"` - silent fallback with nullish coalescing
- `value || []`, `value || {}` - silent fallback to empty collections

**Features**:
- **Severity Levels**: info, warning, error (filter with `--severity`)
- **Allowlist Support**: `.fallback-allowlist` file format: `file:line # reason`
- **Output Formats**: Human-readable (grouped by file) or JSON (`--json`)
- **Directory Scanning**: Recursive with exclusion patterns (`--exclude`, `--exclude-dir`)

**Exit Codes**:
- `0`: No violations found
- `1`: Violations found (can block commits/CI)
- `2`: Error (invalid arguments, file not found, etc.)

**Allowlist Format** (`.fallback-allowlist`):
```
# Legacy code exemptions
path/to/file.py:42 # Planned refactor in #123
src/config.py:15 # Safe default for optional feature
```

**Integration Points**:
- **Stage 4 Verification**: Can be added to verification checklist
- **Pre-commit Hooks**: Add to `.pre-commit-config.yaml` to block fallback commits
- **CI/CD**: Use `--json` output for automated reporting

**Complements**: ANTI-PATTERNS.md Pattern #7 (Silent Fallbacks & Fake Data)

**Reference**: Created for [Issue #367](https://github.com/hoiung/dotfiles/issues/367) - SST3 fallback enforcement

---

## Stage Assignment Rollout Scripts

Scripts for cross-repo Stage Assignment checkbox rollout automation (Issue #305).

### migrate-stage-assignment-marker.py

**Purpose**: One-time migration from old `## Stage Assignment` marker to new `## Stage Assignment (SST3 Automated)` marker.

**Usage**:
```bash
# Dry-run (preview changes)
python SST3/scripts/migrate-stage-assignment-marker.py --repos all --dry-run

# Test on first 3 issues
python SST3/scripts/migrate-stage-assignment-marker.py --repos dotfiles --test 3

# Execute migration
python SST3/scripts/migrate-stage-assignment-marker.py --repos all --execute
```

**Behavior**:
- **0 matches**: Skip (already migrated or rogue issue)
- **1 match**: Migrate automatically (replace entire section with new template)
- **>1 matches**: Skip and flag for subagent review

**Migration Logic**:
1. Counts occurrences of old marker at line start
2. Single occurrence → Safe to replace with new template
3. Multiple occurrences → Needs manual review (ambiguous which to replace)
4. Zero occurrences → Already migrated or needs separate handling

**Output**:
- Summary: Migrated count, skipped count
- List of issues needing subagent review (with issue numbers)
- Instructions for manual review: "Run subagent to fix issues: #X, #Y, #Z"

**Exit Codes**: `0`=success, `1`=some issues need review, `2`=error

**Related**: Issue #311 (marker migration strategy)

---

### backup-issue-bodies.py

**Purpose**: Snapshot issue bodies before rollout for safe recovery.

**Usage**:
```bash
# Backup all open issues from all repos
python SST3/scripts/backup-issue-bodies.py --repos all --output backup-$(date +%Y%m%d).json

# Backup specific repo
python SST3/scripts/backup-issue-bodies.py --repos dotfiles

# Include closed issues
python SST3/scripts/backup-issue-bodies.py --repos all --state all
```

**Exit Codes**: `0`=success, `3`=error

---

### detect-rogue-issues.py — ARCHIVED

> **Archived to `SST3/archive/scripts/`** (2026-04-01). Checked for SST2 `## Stage Assignment` marker. Solo workflow issues use `## Solo Assignment` — this script would flag every valid Solo issue as "rogue".

### freeze-detector.py — ARCHIVED

> **Archived to `SST3/archive/scripts/`** (2026-04-01). Monitored SST2 multi-subagent orchestration with timed checkpoints. Solo workflow uses subagent swarm model with different monitoring patterns.

---

### rollout-issue-assignment.py

**Purpose**: Main rollout script - updates Solo/Stage Assignment checkboxes across repos.

**Usage**:
```bash
# Preview changes (ALWAYS run first)
python SST3/scripts/rollout-issue-assignment.py --dry-run --repos all

# Test on 3 issues first
python SST3/scripts/rollout-issue-assignment.py --test 3 --repos dotfiles

# Full rollout (after verification)
python SST3/scripts/rollout-issue-assignment.py --execute --repos all

# Rollout specific section only
python SST3/scripts/rollout-issue-assignment.py --execute --repos all --section stage
```

**Flags**:
- `--dry-run`: Preview changes without editing
- `--test N`: Update first N issues only
- `--execute`: Full rollout
- `--repos`: Target repos (dotfiles, auto_pb_swing_trader, tradebook_GAS, all)
- `--section`: Which section to rollout (solo, stage, both - default: both)
- `--skip-epic`: Skip issues with 'epic' label (default: True)

**Proven Method**: Finds `## Solo Assignment` or `## Stage Assignment` marker, preserves everything above, replaces marker + below with new checkboxes from template. NO scalpel edits.

**Exit Codes**: `0`=success, `1`=partial failure, `2`=total failure

---

### verify-issue-rollout.py

**Purpose**: Verify rollout correctness - confirm only assignment sections changed.

**Usage**:
```bash
# Verify against backup
python SST3/scripts/verify-issue-rollout.py --backup backup-20251128.json

# Verify specific issues
python SST3/scripts/verify-issue-rollout.py --backup backup.json --issues 305,306,307
```

**Exit Codes**: `0`=verified, `1`=discrepancies, `3`=error

---

### check-issue-assignment-change.py

**Purpose**: Pre-commit hook that detects Issue Assignment template changes (Solo and/or Stage).

**Usage**: Runs automatically via pre-commit. Manual test:
```bash
python SST3/scripts/check-issue-assignment-change.py
```

**Behavior**:
- Detects changes to `## Solo Assignment` or `## Stage Assignment` sections in issue-template.md
- Outputs warning with next steps (points to issue-assignment-rollout.md)
- **Never blocks** (exit 0) - warning only

**Related Template**: `SST3/templates/issue-assignment-rollout.md` (rollout checklist)

---

### test_rollout_core.py

**Purpose**: Unit tests for core rollout logic.

**Usage**:
```bash
python -m pytest SST3/scripts/test_rollout_core.py -v
```

**Tests**: 11 tests covering marker replacement, idempotency, edge cases.

---

**Created**: 2025-11-09 (Issue #109, #110)
**Updated**: 2025-11-28 (Issue #305, Stage Assignment rollout automation)
**Maintained By**: SST3 self-healing process
