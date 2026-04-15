# Research Reference Guide

## Standard Location

**Path**: `docs/research/` (in project root, NOT in SST3/)

**Why**: Predictable, scannable, project-specific external research documentation.

## File Naming Convention

**Format**: `YYYY-MM-DD-topic-description-issue-NNN.md`

**Examples**:
- `2025-01-14-haiku-capabilities-issue-170.md` (Claude model evaluation)
- `2025-01-15-pandas-data-validation-issue-185.md` (pandas library patterns)
- `2025-02-01-pytest-fixture-patterns-issue-200.md` (pytest testing patterns)
- `2025-02-10-fastapi-async-handlers-issue-215.md` (FastAPI framework patterns)

**Rationale**:
- **Date-first**: Chronological sorting (`ls` naturally orders by date)
- **Topic**: Readable description for scanning
- **Issue reference**: Breadcrumb trace to source context
- **AI discoverability**: All search patterns work:
  - By topic: `grep -r "haiku" ../*/docs/research/`
  - By issue: `find ../*/docs/research -name "*issue-170*"`
  - By date: `find ../*/docs/research -name "2025-01*"`

**Sources**: Harvard Data Management, Harvard Library, Iowa State University file naming standards (see Issue #200 research).

## When to Create Research References

**Threshold**: 3+ external resources found during Stage 1 research

**Create when**:
- Library/framework evaluation compared 3+ alternatives
- API documentation spans multiple sections
- Community resources (Stack Overflow, GitHub) used repeatedly
- Solution will be reused in future features

**Keep inline when**:
- Single quick documentation lookup
- One-time problem solution
- Project-specific code patterns (use code comments instead)

## Discovery Process

**Stage 1 Workflow Integration**:
1. Check `docs/research/` directory exists
2. Scan YAML frontmatter for domain match
3. Use existing research if coverage matches need
4. Document in Issue whether research was found/used
5. Capture new research if 3+ resources threshold met

**Mandatory**: Stage 1 Item 2 enforces discovery check BEFORE external research.

## Research Lifecycle

**Status States**:

| Status | Condition | Action |
|--------|-----------|--------|
| `active` | Recently used (<6 months since `last_reviewed`) | No action |
| `review` | 6-12 months since `last_reviewed` | Warning in quarterly audit |
| `stale` | >12 months since `last_reviewed` | Move to `docs/research/archive/` |
| `deprecated` | Superseded by newer research OR dependency removed | Update status, add `superseded_by` field |
| `archived` | >24 months in archive + zero references | Consider deletion (preserve major decisions) |

**Detection Methods**:
- **Time-based**: `last_reviewed` field in YAML frontmatter
- **Event-based**: Dependency version changes, superseded by newer research
- **Reference counting**: `grep -r "filename" codebase` to check usage

**Archive Location**: `docs/research/archive/`

**Enforcement**: Stage 4 (verify preservation), Stage 5 Post-Implementation Review (audit preservation)

## File Structure

**Required sections** (see template):
- YAML frontmatter with metadata
- AI Task Lookup table (IF-THEN patterns)
- External Resources table (Need-URL-Find)
- Code Patterns with copy-paste blocks
- Integration Points table (file:line references)

**Template**: Use `../templates/research-reference-template.md`

## Maintenance Standards

**Update when**:
- New patterns discovered during implementation
- External resources changed/deprecated
- Coverage gaps found during usage

**Review frequency**: Quarterly (check last_updated field in YAML)

**Ownership**: Team maintains collectively (not single author)

## Validation Test Results (Issue #165)

**4 Test Scenarios**:
1. Existing research found → Used PANDAS.md, no external search
2. No research exists → Created REQUESTS.md from scratch
3. Partial coverage → Updated PANDAS.md, no duplicate file
4. Multiple domains → Combined PANDAS.md + PYTEST.md knowledge

**Success Metrics**:
- 4/4 scenarios passed
- Stage 1 discovery prevented duplicate research
- Research files reused across features
- No reinventing the wheel

## AI-Optimization Principles

**Tables over prose**: AI parses tables 3x faster than paragraphs

**YAML frontmatter**: Structured metadata for quick relevance scanning

**Copy-paste code blocks**: Direct reuse without modification

**File:line references**: Exact navigation to integration points

**IF-THEN lookup**: Decision support for task matching

## Cross-Repo Consistency

**dotfiles** (SST3 source):
- Contains template and this guide
- STANDARDS.md defines principle
- Stage 1 workflow enforces discovery

**project-a** (example):
- docs/research/ for trading-specific patterns
- CLAUDE.md points to research location

**project-b** (example):
- Migrated IBKR_API_REFERENCE.md → docs/research/IBKR_API.md
- CLAUDE.md includes migration notice

## Related Documentation

- Template: `../templates/research-reference-template.md`
- Standards: `../standards/STANDARDS.md` (External Research References section)
- Workflow: `../workflow/WORKFLOW.md` (Stage 1 — Research)
