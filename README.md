# SST3-AI-Harness

**SST3 = Single Source of Truth v3.** AI Agent Orchestration & Governance Methodology for LLM-Powered Software Delivery.

A production-grade framework for orchestrating multi-agent LLM workflows with built-in quality gates, automated governance, and structured delivery processes. Developed through three generations of iteration (SST1 → SST2 → SST3) and battle-tested across 10,000+ commits in production systems. The "Single Source of Truth" principle is the methodology's backbone: every rule, standard, template, and anti-pattern lives in exactly one canonical place, with automated drift checks preventing divergence across mirrored copies.

---

## What This Is

SST3 is a **production agent harness** and **AI delivery methodology**: a complete system for managing dynamically scaled concurrent LLM agents (Claude Opus/Sonnet/Haiku) as a coordinated engineering team. In industry terms, Agent = Model + Harness. SST3 is the harness: the orchestration, governance, and enforcement layer that turns raw LLM capability into reliable production output. It provides:

- **5-Stage Delivery Lifecycle**: Research → Issue Creation → Triple-Check → Implementation → Post-Implementation Review
- **3-Tier Automated Review (Ralph)**: Haiku surface checks → Sonnet logic review → Opus architectural audit, with machine-readable pass/fail tokens
- **14 Pre-Commit Enforcement Hooks**: Token budget monitoring, template drift detection, debug code scanning, fallback prevention, hardcoded parameter detection
- **Structured Context Management**: Handover protocols, crash recovery checkpoints, context budget tracking across 1M-token sessions
- **Self-Healing Operations**: 8 documented failure scenarios with recovery procedures, derived from real production incidents

SST3 treats LLMs as an **execution layer** for Generative AI (GenAI) workflows. Not autocomplete, but a managed team of agentic AI agents operating under governance constraints.

## Read the Journey

Two companion blog posts carry the story and philosophy this README deliberately keeps short:

- [**SST3-AI-Harness. Why I Built a Hero Suit for AI.**](https://hoiboy.uk/posts/sst3-ai-harness-reshapeable-knife/): the reshapeable-knife metaphor, the cowboy problem, trust model, and why this works for marketing, HR, finance, and R&D as much as engineering.
- [**Why I Spend More Tokens Refining Scope Than Writing Code**](https://hoiboy.uk/posts/why-scope-beats-code/): SST2 lessons, the PM reasoning behind scope-first, and how poor scope compounds into technical debt.

## Why This Exists

Most AI-assisted development uses LLMs as line-level autocomplete. SST3 takes a different approach: the human is the **orchestrator** who designs the work, and LLM agents execute it under quality constraints, the same way a technical lead directs a cross-functional team.

This matters because:
- **Without governance**, LLM agents produce inconsistent quality, drift from scope, and silently introduce regressions
- **Without structure**, context is lost between sessions, leading to rework and contradictory decisions
- **Without enforcement**, standards exist on paper but are not followed in practice

SST3 solves all three through automated quality gates, structured delivery processes, and pre-commit enforcement that makes compliance the path of least resistance.

## Why We Chose This Route

Three lessons from SST2 shaped SST3:

- Multiple writer-agents collided. SST3 elects one orchestrator; subagents read-only.
- Context died mid-work. SST3 enforces checkpoint-before-handover on the Issue.
- Fixes applied in isolation broke other paths. SST3 integrates all sources per edit.

Quality over parallel throughput. Full story in [Why I Spend More Tokens Refining Scope Than Writing Code](https://hoiboy.uk/posts/why-scope-beats-code/).

## Why Scope First

- Tokens spent refining scope cost less than tokens spent fixing the wrong thing twice.
- Gaps compound. Small misses become fragile foundations that crack months later.
- Pay in planning or pay ten times more in cleanup. SST3 picks the first one every time.

Full PM reasoning in [Why I Spend More Tokens Refining Scope Than Writing Code](https://hoiboy.uk/posts/why-scope-beats-code/).

## What's Different About Our Approach

Most agent frameworks focus on "how do I chain prompts" or "how do I assign tasks to multiple agents". SST3 starts from a different question: **how do I stop the AI from shipping garbage, even when I'm not watching?** That question shapes every design choice below.

### One main orchestrator agent writes. Subagents are PLANNING ONLY.

The main orchestrator agent is the single writer. It holds full context, makes the calls, writes every line of code, and owns every commit. Subagents are dispatched in parallel to research, explore, audit, and review. They read, analyse, and report findings back. **They never write code.** This separation is load-bearing:

- The orchestrator keeps a coherent mental model across the whole issue without context pollution from parallel edits.
- Subagents get narrow, focused prompts on specific questions (review a directory, verify a claim, audit against a standard) and cheaper models (Haiku, Sonnet) can be used without risking production code quality.
- Subagents cross-check each other from different angles. Layer 2 is NOT allowed to use the same prompt as Layer 1.
- The main orchestrator agent verifies every subagent finding against the source before acting on it. Trust but verify, always.

This is explicitly the opposite of "let N agents write code in parallel and merge the winner". That path produces inconsistent styles, duplicate implementations, and silent conflicts. SST3 treats subagents like a research team, not a coding team.

### Subagent count is dynamic, not stingy (AP #14)

If the task has 12 claim categories, dispatch 12 subagents (or more). If it's an audit across 8 directories, one subagent per directory. Default stinginess of "2-3 subagents" misses 40-60% of issues. The 1M-token context window exists precisely to let the orchestrator absorb high-volume subagent output. Use it.

### Planning mode by default

The main orchestrator agent starts in PLANNING MODE. No file changes, no commits. It only shifts to execution when the user explicitly says "work on #X" or "implement this". This prevents the "AI ran ahead and wrote a whole feature you didn't ask for" failure mode. Alignment first, then action.

### Issue-driven, evidence-enforced

Every piece of work starts with a GitHub Issue. Every phase checkpoint posts a comment to the Issue. Every checkbox tick requires evidence (commit hash, test output, file diff) through a custom MCP server that literally blocks tick-without-proof. If the AI can't produce the evidence, the checkbox stays unchecked. This is accountability and ownership, baked into the workflow. (Something the UK government could learn a thing or two about, frankly.)

### Handover protocol, so context never dies

Long-running work risks two failure modes: context fills up, or the session crashes. SST3 mitigates both with a handover protocol. Before a context break (routine or emergency), the main orchestrator agent posts a checkpoint to the GitHub Issue FIRST, then writes a handover document. On recovery, the next session re-reads STANDARDS.md, CLAUDE.md, the Issue, and the last checkpoint. It picks up exactly where it left off, with no "the AI forgot what it was doing" rework. The Issue is the single source of truth for progress.

### Verification loop before Ralph Review

Stage 4 (Implementation) doesn't hand off to Ralph Review until the main orchestrator agent has independently verified:
- Every acceptance criterion maps to a specific file:line in the diff
- Every new function has a caller
- Every config key is read somewhere
- Every database column exists
- Every nullable path has a guard
- No silent fallbacks, no mocked tests that swallow arguments

Only then does Ralph run. Reviewer time is precious. Don't waste it on things the writer should have checked themselves.

### Ralph Review: three models, increasing depth

Named after Ralph Wiggum (if Ralph can spot it, it's really wrong). Haiku handles surface checks (missing files, debug prints, naming). Sonnet traces logic (null propagation, scope drift, silent fallbacks). Opus audits architecture (wiring across modules, contract mismatches, overengineering). Any tier emits a machine-readable PASS token or the loop restarts from Haiku with the fixes applied. No shortcuts. No "looks good to me" without evidence.

### Branch safety, commit-per-file, direct merge after Ralph

Work happens on a solo branch (`solo/issue-{N}-description`). The main orchestrator agent **NEVER switches branches** mid-work. That's one of the loudest ways to lose uncommitted changes. Commits are per-file, with descriptive messages. After all three Ralph tiers pass, the merge to `main` happens immediately (protecting the work from a late conflict), then the human review checklist gets posted. This order matters: merge protects work, then human reviews for judgement calls the Ralph tiers aren't built to catch.

### Keep going until done (AP #17)

The AI does NOT stop mid-work to ask permission or "check in". Phase checkpoints post to the Issue and continue. The only valid reasons to stop are: context at 80%+ of model window, irreversible destructive action needing user consent (force-push, `rm -rf`, DROP TABLE), genuinely stuck after investigation (not first-response-to-friction), or task complete. Premature stopping is its own anti-pattern with its own rule.

### Single Source of Truth, drift-checked automatically

Every rule, standard, template, script, and anti-pattern lives in ONE canonical place inside `dotfiles/SST3/`. Other repos (this one, `ebay-seller-tool`, `hoiboy-uk`) vendor byte-identical copies. Pre-commit hooks use `cmp -s` to fail any commit where a vendored copy has drifted from canonical. No "which version is the real one?" ambiguity. That IS the "Single Source of Truth v3" in the name, applied at the file-system level.

## Hero Suit, Not Hero

The harness amplifies your existing expertise. It does not replace it. It is a reshapeable knife, shaped to the hand holding it: chef, surgeon, butcher, samurai. The tool is the same; the craft is yours. Full metaphor and the SME/junior logic in [the reshapeable-knife post](https://hoiboy.uk/posts/sst3-ai-harness-reshapeable-knife/).

## Not Just for Engineering

SST3 is not an IT tool. It's a methodology for wrapping AI with guardrails, and guardrails apply to every department that produces work under a quality standard.

- **Marketing**: brand voice profile, banned-vocab lists, SEO checklists, approval gates before a campaign ships. Same structure as the voice guard that runs over this very README.
- **HR**: job description templates, interview rubrics, bias sweeps, tone-of-voice guides. SME sets the rules, AI drafts, the harness enforces, human reviews in minutes instead of hours.
- **Finance and accounting**: regulatory disclosures, audit-trail compliance, report templates where a wrong figure ends careers. Fail-fast enforcement and evidence-enforced approvals are non-optional here.
- **R&D**: research protocols, literature-review methodology, hypothesis validation checklists. The senior researcher's judgement becomes the rules; AI accelerates grunt work inside the method, not around it.

The pattern is always the same: SMEs set the standards, AI produces the first pass, the harness enforces compliance, humans review the output. Same shape whether the output is code, ad copy, a financial disclosure, or a research protocol.

## Trust Model

80:20 rule. About 80% of AI output is usable after light review; the 20% grey zone is what the harness is for. Full reasoning in [the reshapeable-knife post](https://hoiboy.uk/posts/sst3-ai-harness-reshapeable-knife/).

## Who It Helps

- **SMEs**: force multiplier. Your judgement becomes reusable guardrails.
- **Juniors**: learning tool only. Training wheels, not a replacement for reps. Read the source, ask why, don't outsource your craft.

Full guidance in [the reshapeable-knife post](https://hoiboy.uk/posts/sst3-ai-harness-reshapeable-knife/).

## Embrace, Don't Resist

Automate the repeatable. Spend your edge where humans still win: creativity, intuition, weird leaps. Full argument in [the reshapeable-knife post](https://hoiboy.uk/posts/sst3-ai-harness-reshapeable-knife/).

## Key Metrics

| Metric | Value |
|--------|-------|
| Commits produced | 10,000+ across 3 repositories |
| Issues tracked | 1,860+ at 99.4% close rate |
| Automated tests | 11,100+ including E2E against live broker APIs |
| Concurrent agents | Dynamically scaled parallel agent swarms (research, review, implementation) |
| Quality gate pass rate | 3-tier Ralph Review on every merge |
| Pre-commit hooks | 14 automated checks across 3 repos |
| Methodology generations | 3 (SST1 → SST2 → SST3), each driven by real failures |
| Framework components | 77 files: standards, templates, scripts, tests, MCP server |

## Architecture

```
SST3-AI-Harness/
├── workflow/              # 5-stage Solo delivery lifecycle
├── standards/             # Engineering standards + anti-patterns
├── templates/             # Issue, review, handover templates
├── reference/             # Self-healing, tool selection, quality guides
├── ralph/                 # 3-tier automated review system
├── scripts/               # 23 enforcement + automation scripts
├── tests/                 # 14 test files + regression suite
├── mcp-servers/           # Custom MCP server (github-checkbox)
├── claude/                # Custom statusline + config
├── .pre-commit-config.yaml # 14-hook enforcement config
└── .github/workflows/     # CI/CD pipeline
```

## The 5-Stage Workflow

Each stage has explicit entry/exit criteria. Stages cannot be reordered or skipped.

| Stage | What Happens | Who Does It |
|-------|-------------|-------------|
| **1. Research** | Parallel subagent swarm explores codebase, maps dependencies, identifies risks | Subagents (Haiku/Sonnet) |
| **2. Issue Creation** | Structured issue with acceptance criteria, phase checkpoints, quality mantras | Main orchestrator agent from research findings |
| **3. Triple-Check** | Independent verification that scope matches research: no gaps, no drift | Subagent verification swarm |
| **4. Implementation** | Execute phases, commit per file, verification loop, Ralph Review, merge | Main orchestrator agent + Ralph subagents |
| **5. Post-Implementation** | Phase-by-phase review against scope, wiring checks, regression tests | Subagent review swarm |

The main orchestrator agent orchestrates the workflow. Subagents handle research, exploration, and review. They read and analyse but never write code. This separation ensures the orchestrator maintains full context while subagents provide independent verification.

## Ralph Review: AI Governance

Ralph is a 3-tier automated quality review system. Every merge requires all three tiers to pass.

| Tier | Model | Focus | What It Catches |
|------|-------|-------|-----------------|
| **1. Haiku** | Claude Haiku | Surface checks | Missing files, unchecked boxes, debug code, naming violations |
| **2. Sonnet** | Claude Sonnet | Logic checks | Silent fallbacks, scope drift, duplicate modules, dead code |
| **3. Opus** | Claude Opus | Architecture | Overengineering, standard violations, contract mismatches, design flaws |

Each tier outputs a machine-readable token (`HAIKU_PASS`, `SONNET_PASS`, `OPUS_PASS`). If any tier fails, the main orchestrator agent fixes the issues and restarts from Tier 1. This creates a **responsible AI** feedback loop. Quality is enforced automatically, not by honour system.

### What Ralph Catches (The 5 Common Culprits)

Every tier scans for these at increasing depth:

1. **Duplicate Code**: same logic in multiple places (DRY violation)
2. **On-the-fly Calculations**: inline formulas that should be configuration
3. **Hardcoded Settings**: magic numbers and embedded config values
4. **Obsolete/Dead Code**: old code that should have been deleted
5. **Silent Fallbacks**: defaults that hide errors instead of failing loudly

## Enforcement Layer

SST3 does not rely on agents remembering to follow standards. Compliance is enforced through 14 pre-commit hooks that run on every commit:

| Hook | What It Enforces |
|------|-----------------|
| `sst3-pre-commit-checks` | Token budget, Python syntax |
| `check-claude-template-propagation` | CLAUDE.md consistency across repos |
| `auto-stage-tracked-folders` | Auto-stage SST3 metrics and docs |
| `check-devprojects-clean` | No rogue files in workspace |
| `no-temp-folder` | No temp/ directories committed |
| `check-crossrepo-paths` | Cross-repo path format compliance |
| `check-issue-assignment-change` | Solo assignment rollout safety |
| `check-hardcoded-params` | No magic numbers in Python/JS/CSS |
| Standard hooks | End-of-file, trailing whitespace, merge conflicts, JSON/YAML validation |

Additionally, `check-fallbacks.py` enforces the **Fail Fast** principle: no silent defaults, no graceful degradation that hides broken dependencies.

## Custom Tooling

### MCP Server: GitHub Checkbox Operations

A custom Model Context Protocol server (`mcp-servers/github-checkbox/`) built with FastMCP providing 6 tools for evidence-enforced checkbox operations. Agents must provide proof of completion when marking checkboxes. No self-reported "done" without evidence.

This implements **RAG-based governance**: the server queries live GitHub data before allowing state changes, ensuring audit trail integrity.

### Claude Code Statusline

A custom statusline (`claude/statusline.js`, 343 lines) that parses JSONL session transcripts in real-time, displaying token usage, git status, session duration, and CI/CD status. Provides the orchestrator with continuous situational awareness during long sessions.

## Comparison with Other Approaches

| Capability | SST3 | LangChain | CrewAI |
|-----------|------|-----------|--------|
| **Primary focus** | Delivery governance & orchestration | Chain/pipeline composition | Multi-agent role-play |
| **Quality gates** | 3-tier automated review (Ralph) | None built-in | None built-in |
| **Pre-commit enforcement** | 14 hooks | None | None |
| **Context management** | Structured handover protocol + checkpoints | Manual | Manual |
| **Self-healing** | 8 documented recovery procedures | None | None |
| **Human-in-the-loop** | Mandatory user review gates at Stage 4–5 | Optional callbacks | Optional human input |
| **Model evaluation** | Per-merge Haiku/Sonnet/Opus pass/fail | Per-call evaluation possible | None built-in |
| **Delivery methodology** | Full 5-stage lifecycle | None (tool, not methodology) | Task assignment only |

SST3 is complementary to these tools. It operates at the **methodology layer** (how you organise and govern AI-assisted work), while LangChain and CrewAI operate at the **execution layer** (how you chain prompts and assign tasks).

## Addressing the "Solo Project" Question

SST3 was developed through production use, not as a theoretical exercise. The methodology emerged from three generations of iteration, each driven by real failures documented in the [Anti-Patterns guide](standards/ANTI-PATTERNS.md).

Directing dynamically scaled concurrent AI agents is the functional equivalent of managing a cross-functional team. The governance constraints (Ralph Review, pre-commit enforcement, structured handover) are the same controls applied to any multi-contributor engineering process. The difference is the contributors are LLMs, not people, but the management discipline is identical.

**SST3 is domain-agnostic.** The framework, templates, and enforcement tools are designed to scale beyond one practitioner. Any team in any field can adopt the methodology. The delivery lifecycle, quality gates, and governance model are not tied to any specific technology or business domain.

## Target Use Cases

- **AI Agent Orchestrator / Harness Engineer**: directing concurrent LLM agents as a coordinated team with quality governance; designing the harness (orchestration + enforcement + governance) that wraps the model
- **AI Delivery Lead**: structured methodology for AI-augmented software delivery with measurable programme velocity
- **AI Governance & Responsible AI**: automated quality gates, audit trails, and compliance enforcement for LLM outputs
- **Technical Programme Management**: scalable delivery framework with built-in change management and risk controls
- **MLOps / LLMOps**: automated pipeline from issue to merge with model evaluation at every stage

## Getting Started

### Prerequisites

**Core requirements** (needed for every SST3 workflow):

- **Python 3.10+** (`python3 --version` to check)
- **Node 20+** (`node --version` to check)
- **pre-commit** (`pipx install pre-commit` or `pip install --user pre-commit`; plain `pip install pre-commit` will fail on Python 3.12+ due to PEP 668. Verify with `pre-commit --version`)
- **Claude Code CLI** (see https://docs.claude.com/claude-code for install instructions)
- **GitHub CLI `gh`** authenticated (`gh auth login`, follow the browser prompt and select HTTPS + public-repo scope at minimum)

**Optional, only for the evidence-enforced checkbox MCP server**:

- **`uv` package manager** (see https://docs.astral.sh/uv/ for install). Skip if you do not use the checkbox MCP; the rest of SST3 works without it.

### Clone the Harness

```bash
git clone https://github.com/hoiung/SST3-AI-Harness.git
cd SST3-AI-Harness
pre-commit install
```

### Adopt the Methodology

1. Read [`workflow/WORKFLOW.md`](workflow/WORKFLOW.md): the 5-stage delivery lifecycle
2. Read [`standards/STANDARDS.md`](standards/STANDARDS.md): engineering principles (Fail Fast, LMCE, JBGE)
3. Copy [`templates/CLAUDE_TEMPLATE.md`](templates/CLAUDE_TEMPLATE.md) to your project as `CLAUDE.md`. The template uses in-repo relative paths (for example `standards/STANDARDS.md`) that resolve when you place your project's `CLAUDE.md` at the repo root.
4. Use [`templates/issue-template.md`](templates/issue-template.md) for all new work

### Add Quality Gates

1. Copy [`.pre-commit-config.yaml`](.pre-commit-config.yaml) and the `scripts/` directory
2. Run `pre-commit install` to activate the 14 enforcement hooks
3. Use the [`ralph/`](ralph/) review checklists for post-implementation review

### Add AI Governance

1. Configure the [MCP server](mcp-servers/github-checkbox/) for evidence-enforced operations
2. Use the 3-tier Ralph Review (Haiku → Sonnet → Opus) on every merge
3. Follow the [`reference/self-healing-guide.md`](reference/self-healing-guide.md) for incident recovery

### Your First Issue: End-to-End Walkthrough

Work through a trivial change to learn the 5-stage flow. Suggested example: fix a typo in `README.md`.

The `/Leader` command creates the GitHub Issue for you in Stage 3. Do NOT create the Issue manually, and do NOT create the solo branch until after Stage 3 gives you the Issue number.

1. **Invoke `/Leader 1`** (Research). A subagent swarm explores the codebase and confirms the typo location and scope. Findings go to `/tmp`.
2. **Invoke `/Leader 2`** (Issue Draft). Main orchestrator drafts the Issue body against [`templates/issue-template.md`](templates/issue-template.md); subagents verify coverage.
3. **Invoke `/Leader 3`** (Sanity Check + Issue Creation). Subagents triple-check the draft against the research, then `gh` creates the Issue. You will receive the Issue number (e.g. `#42`).
4. **Create the solo branch NOW that you know the Issue number**: `git checkout -b solo/issue-42-readme-typo`.
5. **Invoke `/Leader 4`** (Implement). Main orchestrator applies the fix, commits per file, pushes, runs the Verification Loop, then runs the 3-tier Ralph Review (Haiku, Sonnet, Opus).
6. **Invoke `/Leader 5`** (Ship It). Merge to main after Ralph passes, post the user-review-checklist.
7. **Invoke `/Leader 6`** (Final Review). Subagent swarm audits the implementation end-to-end. Fix any findings, close the Issue.

Commands live at [`claude/commands/Leader.md`](claude/commands/Leader.md) and [`claude/commands/SST3-solo.md`](claude/commands/SST3-solo.md). Either user-scope them by copying to `~/.claude/commands/` or keep them repo-scoped under `.claude/commands/` in your own project.

### Branching for Your Use Case

- **Using SST3 in your own project**: clone, create `solo/issue-{N}-{description}` branches per the 5-stage workflow, merge to your own `main` once Ralph review passes.
- **Contributing back to SST3-AI-Harness**: fork the repo, run the Phase 1-5 SST3 workflow on your branch, submit a PR with links to your Ralph review evidence and Issue discussion.

### Build Your Own Skill

Want a domain-specific skill (marketing, HR, finance, R&D, etc.) that plugs into the harness? See [`reference/building-skills-guide.md`](reference/building-skills-guide.md) for the minimum viable template, section patterns, and a copy-pasteable skeleton.

### Troubleshooting

- **`gh auth status` reports unauthenticated**: run `gh auth login` and pick HTTPS. You need at least `repo` scope to create issues programmatically.
- **Pre-commit hooks fail on `cmp -s` drift check**: one of the vendored scripts has drifted from canonical. Follow the `Run: cp ...` command in the error message to resync.
- **`/Leader` commands "not found"**: Claude Code did not discover the command. Either copy `claude/commands/Leader.md` to `~/.claude/commands/Leader.md` for user scope, or place it at `.claude/commands/Leader.md` inside your project for repo scope.
- **Path errors referencing `../dotfiles/`**: you are reading the private canonical version. The public harness uses in-repo paths (`standards/`, `workflow/`, `templates/`, `ralph/`). Verify you are editing files in `SST3-AI-Harness/`, not a private dotfiles mirror.

## Repository Structure

| Directory | Contents | Purpose |
|-----------|----------|---------|
| `workflow/` | WORKFLOW.md | The 5-stage delivery lifecycle specification |
| `standards/` | STANDARDS.md, ANTI-PATTERNS.md | Engineering principles and documented failure patterns |
| `templates/` | 6 templates | Issue creation, review, handover, config propagation |
| `reference/` | 10 reference docs | Self-healing, tool selection, quality validation, research guides |
| `ralph/` | 5 files | 3-tier review checklists + plugin config |
| `scripts/` | 23 Python scripts + YAML | Enforcement hooks, automation, quality analysis |
| `tests/` | 14 test files + suite runner | Regression testing across 8 quality dimensions |
| `mcp-servers/` | Custom MCP server | Evidence-enforced GitHub checkbox operations |
| `claude/` | Statusline + config | Claude Code customisation and monitoring |

## License

MIT. See [LICENSE](LICENSE) for details.

---

*Developed by [Senh Hoi Ung](https://github.com/hoiung). SST3 represents three generations of methodology refinement, each iteration driven by real production failures and documented in the [anti-patterns guide](standards/ANTI-PATTERNS.md).*
