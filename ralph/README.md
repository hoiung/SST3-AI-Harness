# Ralph Review Loop

Automated 3-tier quality review for SST3 workflow.

> **CRITICAL: PLANNING MODE ONLY**
> Review subagents are REVIEWERS, not implementers. They:
> - **DO**: Read files, verify evidence, check compliance, report findings
> - **DO NOT**: Write code, edit files, make commits, fix issues
>
> If issues found, subagent reports findings → Main agent fixes → Restart review.

## What

Main agent spawns 3 review subagents that each use the Ralph plugin to iterate until passing:
- **Tier 1 (Haiku)**: Surface checks - files, checkboxes, commits
- **Tier 2 (Sonnet)**: Logic checks - evidence, scope, fallbacks
- **Tier 3 (Opus)**: Deep checks - architecture, standards, review

### The 5 Common Culprits

Every tier scans for these STANDARDS.md violations at increasing depth:

| Violation | What | Standard |
|-----------|------|----------|
| **Duplicate Code** | Same logic in multiple places | DRY, Modularity |
| **On-the-fly Calculations** | Inline math/formulas that should be in config | No Hardcoded Settings |
| **Hardcoded Settings** | Magic numbers, embedded config values | STANDARDS.md |
| **Obsolete/Dead Code** | Old code that should have been deleted | LMCE |
| **Silent Fallbacks** | Defaults that hide errors | Fail Fast |

## Get

Ralph plugin already installed (user scope, cross-repo).

```bash
# Verify installation
/help  # Look for ralph-loop in available commands
```

## Install

No additional installation. Uses existing:
- `Task` tool with model parameter
- `/ralph-loop` command from ralph-loop plugin

## Usage

**Main agent invokes each tier (subagents must read STANDARDS.md + the tier checklist):**

```bash
# Tier 1: Haiku surface checks
Task(model=haiku): /ralph-loop "Review per SST3/standards/STANDARDS.md and SST3/ralph/haiku-review.md" --completion-promise "HAIKU_PASS"

# Tier 2: Sonnet logic checks
Task(model=sonnet): /ralph-loop "Review per SST3/standards/STANDARDS.md and SST3/ralph/sonnet-review.md" --completion-promise "SONNET_PASS"

# Tier 3: Opus deep checks
Task(model=opus): /ralph-loop "Review per SST3/standards/STANDARDS.md and SST3/ralph/opus-review.md" --completion-promise "OPUS_PASS"
```

**Flow:**
1. Main agent completes implementation
2. Spawns Haiku subagent with Ralph
3. If HAIKU_PASS → Spawns Sonnet
4. If SONNET_PASS → Spawns Opus
5. If OPUS_PASS → Ready for user approval
6. If ANY FAIL → Main agent fixes → Restart from Haiku

**Max iterations**: each tier is capped at **5 restart cycles**. If the same tier fails 5 times in a row, ESCALATE to user — do not loop indefinitely. The cap prevents infinite loops on architectural disagreements that need human judgement.

## Learn

- [haiku-review.md](haiku-review.md) - Tier 1 checklist
- [sonnet-review.md](sonnet-review.md) - Tier 2 checklist
- [opus-review.md](opus-review.md) - Tier 3 checklist
- [Ralph technique](https://ghuntley.com/ralph/) - Original methodology
