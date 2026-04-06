# [DOMAIN] Research Reference

**Naming Convention**: `YYYY-MM-DD-topic-description-issue-NNN.md`
**Example**: `2025-01-14-haiku-capabilities-issue-170.md`

---
domain: [DOMAIN_NAME]
type: [library|framework|api|protocol|tool|decision|process]
topics: [list, of, related, topics]
use_when: "[Brief description of when to use this research]"
github_issue: [NNN]
created_date: YYYY-MM-DD
last_reviewed: YYYY-MM-DD
status: [active|review|deprecated|archived]
deprecation_note: "[Reason if deprecated]"
superseded_by: "[filename if replaced]"
sources:
  - url: [URL 1]
    type: [official|community|blog|stackoverflow]
    accessed_date: YYYY-MM-DD
  - url: [URL 2]
    type: [official|community|blog|stackoverflow]
    accessed_date: YYYY-MM-DD
coverage: [basic|intermediate|comprehensive]
further_reading: [URL to deeper resources]
related_code:
  - file: [path/to/file]
    lines: [start-end]
    description: "[What's there]"
dependencies:
  - name: [package-name]
    version: [semver or 'latest']
    status: [active|deprecated]
retention_policy: [time-based|event-based|permanent]
archive_trigger: "[Condition for archival]"
---

## AI Task Lookup

| IF doing... | THEN use... | Notes |
|-------------|-------------|-------|
| [Task description] | [Solution/library/pattern] | [Key gotcha or tip] |
| [Task description] | [Solution/library/pattern] | [Key gotcha or tip] |

## External Resources

| Need | URL | Find |
|------|-----|------|
| [What you're looking for] | [Direct link] | [What's at that link] |
| [What you're looking for] | [Direct link] | [What's at that link] |

## Code Patterns

### [Pattern Name]

```[language]
# Copy-paste ready code
[code block]
```

**When to use**: [Specific scenario]
**Gotchas**: [Things to watch out for]

### [Pattern Name]

```[language]
# Copy-paste ready code
[code block]
```

**When to use**: [Specific scenario]
**Gotchas**: [Things to watch out for]

## Integration Points

| File | Line | What | Why Here |
|------|------|------|----------|
| [path/to/file] | [line#] | [What's happening] | [Why this matters] |
| [path/to/file] | [line#] | [What's happening] | [Why this matters] |

---

## Guidelines for AI-Optimized Research Docs

**DO**:
- Use tables for quick scanning (AI parses efficiently)
- YAML frontmatter for metadata (structured lookup)
- Copy-paste ready code blocks (direct reuse)
- File:line references (exact navigation)
- IF-THEN lookup tables (decision support)

**DON'T**:
- Write prose paragraphs (harder to parse)
- Explain basic concepts (I already know)
- Duplicate official docs (link instead)
- Add motivational language (not needed)

**Format Priority**: Tables > Code blocks > Bullets > Paragraphs
