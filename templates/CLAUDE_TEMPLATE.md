# SST3 Solo Workflow

## 5-Stage Solo Workflow Model

**Your Role**: Orchestrate research/review via subagent swarms; implement directly. See `workflow/WORKFLOW.md` for full 5-stage workflow.

**Default: PLANNING MODE** — execute only when user says "work on #X" / "implement this". No file changes, no commits in planning mode. When unclear, ask.

**MANDATORY READING**:
1. `standards/STANDARDS.md` (ALWAYS)
2. `standards/ANTI-PATTERNS.md` (ALWAYS — 19 documented failure modes you must not repeat)
3. `{repository-name}/CLAUDE.md` (ALWAYS - replace with repo root)

**Reading Confirmation Checklist** (MUST display and complete):
- [ ] Read STANDARDS.md
- [ ] Read ANTI-PATTERNS.md
- [ ] Read {repository-name}/CLAUDE.md

**Critical behavioural rules** (full detail in STANDARDS.md + ANTI-PATTERNS.md):
- **GREP BEFORE WRITING/CODING**: before creating ANY new file, rule, memory, helper, hook, harness, function, class, component, workflow, process, design, or piece of logic — grep relevant directories with multiple synonyms. Update existing in place if found. New files only after grep confirms nothing exists. (AP #10)
- **MULTI-LAYER SUBAGENT DISCIPLINE** (AP #14): never stingy. Subagent count is DYNAMIC, scaled to cover every directory / file / claim category line-by-line — no stone left unturned. NOT 2-3 as a default. If the work has 12 claim categories, dispatch ≥12 subagents. Use LAYERS cross-checking each other from DIFFERENT angles (layer 2 ≠ layer 1 prompt). Main agent VERIFIES every subagent finding against source — never assume the subagent got it right. Every claim must be factually provable AND the proof method must be documented inline so future audits don't false-positive on it.
- **AP #9 Single-Source Edits**: every edit to a multi-research artefact must integrate ALL relevant sources in the same pass. Never apply one in isolation.
- **AP #11 Stopping vs Applying**: when an audit surfaces a documented violation, RUN the full process (false-positive sweep then apply). Don't stop to ask permission for fixes the standards already mandate. Don't apply without the sweep.
- **AP #12 No Observability**: every component needs structured logs, metrics, and audit trails AT WRITE TIME. Not after the first incident.
- **AP #13 "Proceed" ≠ "Bypass Process"**: when the user says okay / proceed / yes / go ahead, that means **proceed using the full standard process** — not skip the sweeps, gates, Ralph reviews, or guardrails. User authorisation never bypasses workflow.
- **AP #17 Keep Going Until Done**: do NOT stop mid-work to ask permission, wait for user confirmation, or "check in". Phase checkpoints post a comment to the Issue and CONTINUE. Stop ONLY for: (a) context at 80%+ of model window, (b) irreversible destructive action needing user consent (force-push, rm -rf, DROP TABLE, branch deletion), (c) genuinely stuck after investigation (not a first-response-to-friction reflex), (d) task complete. Warn at 70%, keep working until 80%. The 1M window exists to be used.
- **AP #16 Monitor, Don't Fire-and-Forget**: every script / command / subprocess / test / deployment / commit / push you launch must be verified end-to-end (tail logs, check exit code, verify output, confirm side effects). "Started" is not "done". For `run_in_background`, poll BashOutput. Be the user's eyes and ears, not just their executioner. If you cannot answer "what happened?" with specifics, you fired and forgot — go check NOW.
- **AP #18 Sample Invocation Validates Workflow**: for any change touching pipeline / data-processing / orchestration / CLI-wiring / cross-module function-arg propagation — run an actual end-to-end sample invocation (real CLI, real DB, small liquid basket 8 items) BEFORE closing. Unit + smoke tests are necessary but NOT sufficient. Mocks that accept `**kwargs` silently discard params and do NOT prove propagation — assert `call_args.kwargs[...]` explicitly. Stage 4 Verification Loop mandatory gate. See STANDARDS.md "Testing Priority — Workflow Validation Gate".

**STOP if**: No GitHub Issue exists. Create Issue using `templates/issue-template.md`.

### Solo Workflow Overview

**Context Window**: 1M tokens (Opus 4.6/Sonnet 4.6), 200K (Haiku 4.5)
**Content Budget**: ~42K tokens (STANDARDS.md + CLAUDE.md + Issue loaded at session start)
**Handover at**: 80% of model window (800K for 1M, 160K for Haiku) — STOP threshold, not routine. Warn at 70%. Keep working until 80%.
**Issue Header**: `## Solo Assignment (SST3 Automated)`
**Branch**: `solo/issue-{number}-{description}` (commit per file, no PR)
**Merge**: Direct merge to main after Ralph Review passes (BEFORE user review - protects work)

### Execution Guardrails (Built-in)

Pre-start read (CLAUDE.md + STANDARDS.md + Issue) → phase checkpoints (70%+ warn, 80%+ STOP) → post-compact re-read → verification loop until clean → user-review-checklist.md.

### Branch Safety (CRITICAL — DO NOT VIOLATE)

- **NEVER switch branches** (`git checkout main`, `git checkout -b`, `git switch`).
- **Always commit and push to the CURRENT active branch** — it will get merged later.
- If you need something on main, **ask the user** — do NOT switch yourself.
- The only exception is creating a NEW solo branch at the START of work.

### Command Interface

- `/start` — list repos, prompt selection, load CLAUDE.md, WAIT for task.
- `/SST3-solo` — load STANDARDS.md + repo CLAUDE.md, display summary, prompt for task, execute with guardrails.

Handover template: `templates/chat-handover.md` (post checkpoint to Issue FIRST).

## External Research References

**Location**: `docs/research/` in project root
**Check BEFORE external research**: Existing research references
**Capture AFTER research**: If 3+ external resources found, create/update research reference
See: `reference/research-reference-guide.md` for complete guide

## Quality Standards

**See STANDARDS.md** — Never Assume (read source before concluding), Fix Everything (no scope/language excuses, no priority deferrals), Critical Thinking (challenge with evidence). Only valid skip reason: confirmed false positive (document why).

**Voice Content Protection** (optional, opt in per project): when editing voice-sensitive prose (CV, LinkedIn, cover letters, blogs, marketing copy), wrap new prose in voice-guard markers your team uses so pre-commit and CI can scan only tagged regions. Canonical rules in `standards/STANDARDS.md` "Voice Content Protection" + AP #15. See `scripts/voice_rules.py` for the banned-word pattern to adapt to your own voice.

## Ralph Review Loop (MANDATORY)

**Subagents are PLANNING ONLY** - they review, they do NOT write code.

**Flow**: Implement → Haiku → Sonnet → Opus → **Merge to main** → User Review

| Tier | Model | Purpose | Invocation |
|------|-------|---------|------------|
| 1 | `haiku` (MANDATORY) | Surface checks | `Task(model=haiku, prompt="Review per SST3/ralph/haiku-review.md...")` |
| 2 | `sonnet` (MANDATORY) | Logic checks | `Task(model=sonnet, prompt="Review per SST3/ralph/sonnet-review.md...")` |
| 3 | `opus` (MANDATORY) | Deep analysis | `Task(model=opus, prompt="Review per SST3/ralph/opus-review.md...")` |

**On FAIL any tier**: Main agent fixes → Restart from Tier 1 (Haiku)
**On PASS all 3**: Merge to main immediately (protects work), then user review

**Checklists**: `ralph/`

## Quick Reference

### 5-Stage Workflow (ORDER-DEPENDENT — no skipping, no reordering)
```
Stage 1: Research — subagent swarm → main agent writes /tmp (findings + gaps + plan)
Stage 2: Issue Creation — main agent from /tmp, illustrations, compact breaks, quality mantras verbatim
Stage 3: Triple-Check — subagents verify scope vs audit = 100%, chat history, dead code
Stage 4: Implementation — main agent implements, Verification Loop, Ralph Review, merge, user-review-checklist
Stage 5: Post-Implementation Review — subagent swarm: wiring, goal alignment, quality scan, regression tests
```

### Solo Execution Checklist (Stage 4)
```
## Working on Issue #X
Read CLAUDE.md, STANDARDS.md, Issue
Create branch: git checkout -b solo/issue-{X}-{description}
Execute phase 1, commit per file, push, post checkpoint
Execute phase 2, commit per file, push, post checkpoint
...
Run verification loop until clean (overengineering, reuse, duplication, fallbacks, wiring, regression, quality)
Run Ralph Review (Haiku → Sonnet → Opus)
Merge to main (BEFORE user review - protects work, check for conflicts first)
Post user-review-checklist.md (from TEMPLATE, ALL sections mandatory)
User reviews and approves
Cleanup branch, close Issue
```

### Emergency Procedures
- **Context overflow**: Create handover immediately
- **Stuck**: Re-read Issue, identify blocker, post to Issue
- **User compact**: Re-read CLAUDE.md, STANDARDS.md, Issue last comment

### MCP Configuration (Global)
- **Location**: `~/.claude.json` (user scope)
- **Verify**: Run `claude mcp list` or `/mcp` inside Claude Code
- **Servers**: refer to your team's MCP stack (example: `github`, `github-checkbox`)
- **Tool Selection**: See `reference/tool-selection-guide.md`

### MCP Tools
- **Checkboxes**: `mcp__github-checkbox__update_issue_checkbox(issue_number, checkbox_text, evidence)`
- **GitHub Issues**: issue_write, add_issue_comment, search_issues, get_file_contents, create_pull_request

---
<!-- ============================================================== -->
<!-- ⚠️ DO NOT MODIFY OR DELETE ANYTHING ABOVE THIS LINE ⚠️ -->
<!-- ============================================================== -->
<!-- All content ABOVE is SST3 standard managed by dotfiles issues -->
<!-- Modifications require dotfiles repository SST3 issue approval -->
<!-- Project-specific configuration begins BELOW this boundary -->
<!-- ============================================================== -->




# Project-Specific Configuration

## Project Overview

[Brief description of the project]

## Technology Stack

- Language: [e.g., Python 3.11, TypeScript 5.x]
- Framework: [e.g., FastAPI, React, None]
- Dependencies: [key dependencies]

## Repository Structure
```
project-name/
├── src/              # Source code
├── tests/            # Test files
├── docs/             # Documentation
└── CLAUDE.md         # This file
```

## Development Setup
```bash
# Clone and setup
git clone https://github.com/username/project
cd project

# Install dependencies
[package manager commands]

# Run tests
[test commands]
```

## Project Standards

### Code Quality
- Linter: [e.g., ruff, eslint]
- Formatter: [e.g., black, prettier]
- Type checking: [e.g., mypy, TypeScript]

### Testing
```bash
# Run all tests
[test commands]

# Run specific tests
[test commands]
```

### Git Workflow
- Branch naming: `solo/issue-[number]-description`
- Commit format: `type: description (#issue)`

## Common Commands
```bash
# Development
[common commands]

# Testing
[test commands]

# Deployment
[deploy commands]
```

## Project-Specific Notes

[Any important notes specific to this project]

## Documentation Links
- Project README: `README.md`
- API Docs: [link or path]
- Architecture: [link or path]

---

*Template Version: SST3.0.0*
*Last Updated: [DATE]*
