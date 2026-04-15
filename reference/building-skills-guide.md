---
domain: authoring
type: reference
topics: [skills, claude-code, SST3, extension]
use_when: "You want to build a domain-specific skill (marketing, HR, finance, R&D, or anything else) that plugs into the SST3-AI-Harness."
last_updated: 2026-04-15
---

# Building Your Own Skill

Skills are the modular attachments that turn the SST3 harness into a specialist tool for your domain. This guide shows you the minimum viable structure, how skills plug into the harness's quality gates, and the common mistakes to avoid.

## Skill File Location Convention

This is a **recommended pattern, not a mandate**. Adapt to your team's setup.

- **User-scoped** (available everywhere you use Claude Code): `~/.claude/skills/<domain>/SKILL.md`
- **Repo-scoped** (only when Claude Code is invoked from inside that project): `<project>/.claude/skills/<domain>/SKILL.md`

Use `<domain>` as a short noun phrase that names the skill: `marketing-brief`, `hr-jd`, `finance-disclosure`, `rd-protocol`, etc. One skill = one directory.

Invoke a skill as `/skill-name <verb> <arg>` once Claude Code has discovered it.

## Required Frontmatter

Every `SKILL.md` starts with a YAML frontmatter block. Two fields are required:

```yaml
---
name: skill-name
description: One-sentence description of what this skill does and when to use it.
---
```

`name` must match the parent directory. `description` is what Claude Code shows when listing available skills, so make it genuinely informative.

## SST3 Anti-Patterns That Govern Every Skill

This is a **recommended pattern, not a mandate**, but if you skip these, you lose most of the harness's value.

- **AP #9 Single-Source Edits**: load ALL mandatory reading before you act. Never fix one lens in isolation.
- **AP #10 Duplicate Rules**: grep the repo for existing helpers, rules, or templates before creating new ones. Update in place if found.
- **AP #14 Subagent Discipline**: for audits, research, or reviews, dispatch one subagent per angle, not a default of 2-3. Each subagent covers a different angle. Main agent verifies every finding against source.
- **AP #15 Voice Prose Without Markers**: if the skill edits voice-sensitive content (CV, LinkedIn, blogs), wrap new prose in voice-guard markers so pre-commit catches AI tells.
- **AP #16 Monitor, Don't Fire-and-Forget**: verify every command, test, commit, push end-to-end. "Started" is never "done".
- **AP #17 Keep Going Until Done**: phase checkpoints post to the Issue and continue. Stop only at 80% context, destructive action needing consent, genuinely stuck, or task complete.

Full detail in [`../standards/ANTI-PATTERNS.md`](../standards/ANTI-PATTERNS.md).

## Mandatory Reading Section Pattern

Every skill should list the files Claude MUST load before any action. This is how you keep the skill aligned with your domain's source of truth. Example pattern:

```markdown
## MANDATORY READING on Invoke

1. `../standards/STANDARDS.md` (harness engineering standards, applies everywhere)
2. `reference/<domain>-profile.md` (your domain's voice/rules, if it exists)
3. `reference/<domain>-research.md` (factual authority, conditional if-exists)
4. `templates/<domain>-template.md` (output format, conditional if-exists)
```

State which source is canonical when multiple exist, and note "if this diverges from X, X wins".

## CRITICAL Rules Section Pattern

This is where you codify the non-negotiables that define your domain's quality bar. Examples:

- "CRITICAL: every number in the output must trace to a verified source."
- "CRITICAL: GREP BEFORE WRITING, every new file first checked against existing versions."
- "CRITICAL: every deliverable passes the `<your-domain>-check` guard script with exit code 0."

Two or three of these is typical. More than five is usually a sign the skill is doing too much.

## Sub-Commands Section Pattern

Each sub-command is a numbered workflow the skill executes. Structure:

```markdown
### /skill-name <verb> <arg>

Brief one-sentence description.

1. Load mandatory reading files.
2. [Domain-specific step]
3. [Domain-specific step]
4. Run guard script: `python3 scripts/<domain>_check.py <file>`
5. Verify exit code 0. If not, fix and re-run.
```

Numbered steps, not bullets. The reader should be able to copy-paste this as a checklist.

## Writing Rules Section Pattern

**Do NOT inline rules here. Point to source files.** Inlining duplicates the canonical authority and drifts over time.

```markdown
## Writing Rules

- **Voice rules**: see `reference/<domain>-profile.md` (canonical)
- **Style rules**: see `../standards/STANDARDS.md` + `reference/<domain>-style.md`
- **Quick reference checklist** (non-canonical, source of truth is the files above):
  - [ ] Check 1
  - [ ] Check 2
```

## File Locations Table Pattern

Every skill ends with a table so readers find everything in one place:

```markdown
| File | Location |
|------|----------|
| Canonical rule source | `reference/<domain>-profile.md` |
| Research docs | `reference/<domain>-research/` |
| Guard script | `scripts/<domain>_check.py` |
| Output template | `templates/<domain>-template.md` |
| Deliverables | `projects/<domain>/` |
```

## Minimum Viable Skill Template

Copy this, rename `<domain>` to your skill's name, and fill in the domain-specific pieces.

```markdown
---
name: <domain>
description: <one-sentence pitch: what the skill does, when to use it>
---

# <Domain> Skill

Brief two-sentence context on what domain this covers and why it exists.

## SST3 Anti-Patterns Governing This Skill

Before any action, respect these APs (full detail in `../standards/ANTI-PATTERNS.md`):
- **AP #9**: Load ALL mandatory reading before output
- **AP #10**: Grep before creating anything new
- **AP #14**: Scale subagents to coverage, not a default of 2-3
- **AP #16**: Verify end-to-end, never fire-and-forget
- **AP #17**: Keep going until done

## MANDATORY READING on Invoke

1. `../standards/STANDARDS.md`
2. `reference/<domain>-profile.md` (if exists, your domain's canonical rules)

## CRITICAL: <Your Non-Negotiable>

Two or three sentences on the most important rule that makes this skill work.

## Available Sub-Commands

### /<domain> <verb> <arg>

1. Load mandatory reading files.
2. [Domain-specific step]
3. [Domain-specific step]
4. Run guard script: `python3 scripts/<domain>_check.py`
5. Verify exit code 0.

## Writing Rules

- **Domain rules**: see `reference/<domain>-profile.md`
- **General standards**: see `../standards/STANDARDS.md`

## File Locations

| File | Location |
|------|----------|
| Canonical rule source | `reference/<domain>-profile.md` |
| Guard script | `scripts/<domain>_check.py` |
| Deliverables | `projects/<domain>/` |
```

Save this as `~/.claude/skills/<domain>/SKILL.md` (user-scoped) or `<project>/.claude/skills/<domain>/SKILL.md` (repo-scoped) and you have a working skill skeleton.

## How Skills Plug Into the Harness

A skill is a specialist attachment to the generalist harness. It inherits:

- **Quality gates**: if your skill's sub-command invokes the 5-stage workflow (`/Leader 1-6`), Ralph Review runs automatically on every merge.
- **Standards**: every skill references `standards/STANDARDS.md` and `standards/ANTI-PATTERNS.md`, so the same engineering principles apply to its output.
- **Voice markers** (optional): if your skill edits voice-sensitive prose, adopt the marker pattern from the harness's voice guard (wrap new prose in markers so pre-commit and CI can catch AI tells before publication).
- **Subagent discipline**: if your skill runs audits or research, follow AP #14 and dispatch one subagent per angle, never a default of 2-3.

The harness does not know your domain. Your skill does. The skill tells the harness what to enforce; the harness enforces it.

## Common Mistakes

- **Hardcoded absolute paths**: keep paths repo-relative (`standards/STANDARDS.md`, not `/home/user/projects/SST3-AI-Harness/standards/STANDARDS.md`). Skills break the moment the directory structure differs.
- **Inlining rules instead of pointing at source**: the canonical file should live in one place. Skills point at it. Inlining causes drift.
- **Personal voice markers in a shared skill**: use generic names (`<!-- voice-open -->`, not `<!-- iamhoi -->`) so other users can adopt the skill without stripping your name out.
- **Missing frontmatter**: Claude Code won't discover or list a skill without a valid `name` + `description` frontmatter.
- **Ignoring AP #14**: dispatching 2-3 subagents as a default misses 40-60% of issues on real audits. Match subagent count to scope.
- **Skipping the guard script**: if your skill's output can fail quietly (voice tells, factual errors, schema violations), the guard script is non-negotiable. Build it first, not last.

## References

- [`../standards/STANDARDS.md`](../standards/STANDARDS.md) for harness engineering standards
- [`../standards/ANTI-PATTERNS.md`](../standards/ANTI-PATTERNS.md) for the full anti-pattern catalogue
- [`../workflow/WORKFLOW.md`](../workflow/WORKFLOW.md) for the 5-stage delivery lifecycle skills operate inside
- [`research-reference-guide.md`](research-reference-guide.md) for how to structure domain research files your skill will reference
