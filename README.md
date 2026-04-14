# SST3-AI-Harness

**AI Agent Orchestration & Governance Methodology for LLM-Powered Software Delivery**

A production-grade framework for orchestrating multi-agent LLM workflows with built-in quality gates, automated governance, and structured delivery processes. Developed through three generations of iteration (SST1 → SST2 → SST3) and battle-tested across 10,000+ commits in production systems.

---

## What This Is

SST3 is a **production agent harness** and **AI delivery methodology**: a complete system for managing dynamically scaled concurrent LLM agents (Claude Opus/Sonnet/Haiku) as a coordinated engineering team. In industry terms, Agent = Model + Harness. SST3 is the harness: the orchestration, governance, and enforcement layer that turns raw LLM capability into reliable production output. It provides:

- **5-Stage Delivery Lifecycle**: Research → Issue Creation → Triple-Check → Implementation → Post-Implementation Review
- **3-Tier Automated Review (Ralph)**: Haiku surface checks → Sonnet logic review → Opus architectural audit, with machine-readable pass/fail tokens
- **14 Pre-Commit Enforcement Hooks**: Token budget monitoring, template drift detection, debug code scanning, fallback prevention, hardcoded parameter detection
- **Structured Context Management**: Handover protocols, crash recovery checkpoints, context budget tracking across 1M-token sessions
- **Self-Healing Operations**: 8 documented failure scenarios with recovery procedures, derived from real production incidents

SST3 treats LLMs as an **execution layer** for Generative AI (GenAI) workflows. Not autocomplete, but a managed team of agentic AI agents operating under governance constraints.

## Why This Exists

Most AI-assisted development uses LLMs as line-level autocomplete. SST3 takes a different approach: the human is the **orchestrator** who designs the work, and LLM agents execute it under quality constraints, the same way a technical lead directs a cross-functional team.

This matters because:
- **Without governance**, LLM agents produce inconsistent quality, drift from scope, and silently introduce regressions
- **Without structure**, context is lost between sessions, leading to rework and contradictory decisions
- **Without enforcement**, standards exist on paper but are not followed in practice

SST3 solves all three through automated quality gates, structured delivery processes, and pre-commit enforcement that makes compliance the path of least resistance.

## Think of It as a Hero Suit

SST3 is a customisable hero suit. You are the subject matter expert. You already know your domain, your field, your craft. The harness doesn't replace that. It amplifies it.

Think of it like a reshapeable knife. The same tool in different hands serves different purposes: a chef's blade, a surgeon's scalpel, a samurai's katana, a butcher's cleaver. The knife doesn't know how to cook or operate or fight. The expert does. The tool just makes them faster and more precise.

That's what SST3 does. It's an accelerator. A catalyst that speeds up your already latent power. You direct the agents, you make the calls, you judge what's right and wrong. The harness enforces the discipline so nothing falls through the cracks while you work at speed. (Be careful of burnouts though. Working at 10x pace means you can also burn out at 10x pace.)

Here's the catch: if you're still learning your field, the harness won't save you. You'll struggle to judge whether the AI's output is right or wrong. You'll become dependent on it rather than your own intellect, experience, and knowledge. That's not the harness failing. That's trying to wear a hero suit before you've built the strength to carry it.

SST3 is built for people who already know what they do. Domain experts. SMEs. Technical leads who can look at an AI agent's output and immediately spot what's wrong. The suit fits those who've already earned the muscle.

And the AI skills? Those are the suit's enhancements. Weapons, shields, scanners, whatever your domain needs. But skills used alone aren't effective. A skill without the harness is a loose attachment with no frame to mount it on. SST3 is the frame. The skills plug into it, draw power from its governance and quality gates, and that's what lets them run at full potential. The harness without skills is a solid suit. Skills without the harness is a pile of parts on the floor.

You can use it to build automation, to research, to write, to analyse, all with tight guardrails that reduce hallucination and the bullshit AI spouts at times which is not factual or true. It's not perfect, but it's far better than Claude Code out the box. My principle is KISS (Keep It Simple Stupid), so this framework is built to be reliable and simple to customise without all the additional LLM wiki or graphs or other memory frameworks which add complexity and more parts to fail. (That doesn't mean I won't try them and see if they can improve SST3-AI-Harness or larger projects that work alongside the harness, but the current version works reliably.)

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
| **2. Issue Creation** | Structured issue with acceptance criteria, phase checkpoints, quality mantras | Main agent from research findings |
| **3. Triple-Check** | Independent verification that scope matches research: no gaps, no drift | Subagent verification swarm |
| **4. Implementation** | Execute phases, commit per file, verification loop, Ralph Review, merge | Main agent + Ralph subagents |
| **5. Post-Implementation** | Phase-by-phase review against scope, wiring checks, regression tests | Subagent review swarm |

The main agent orchestrates the workflow. Subagents handle research, exploration, and review. They read and analyse but never write code. This separation ensures the orchestrator maintains full context while subagents provide independent verification.

## Ralph Review: AI Governance

Ralph is a 3-tier automated quality review system. Every merge requires all three tiers to pass.

| Tier | Model | Focus | What It Catches |
|------|-------|-------|-----------------|
| **1. Haiku** | Claude Haiku | Surface checks | Missing files, unchecked boxes, debug code, naming violations |
| **2. Sonnet** | Claude Sonnet | Logic checks | Silent fallbacks, scope drift, duplicate modules, dead code |
| **3. Opus** | Claude Opus | Architecture | Overengineering, standard violations, contract mismatches, design flaws |

Each tier outputs a machine-readable token (`HAIKU_PASS`, `SONNET_PASS`, `OPUS_PASS`). If any tier fails, the main agent fixes the issues and restarts from Tier 1. This creates a **responsible AI** feedback loop. Quality is enforced automatically, not by honour system.

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

### Adopt the Methodology

1. Read [`workflow/WORKFLOW.md`](workflow/WORKFLOW.md): the 5-stage delivery lifecycle
2. Read [`standards/STANDARDS.md`](standards/STANDARDS.md): engineering principles (Fail Fast, LMCE, JBGE)
3. Copy [`templates/CLAUDE_TEMPLATE.md`](templates/CLAUDE_TEMPLATE.md) to your project as `CLAUDE.md`
4. Use [`templates/issue-template.md`](templates/issue-template.md) for all new work

### Add Quality Gates

1. Copy [`.pre-commit-config.yaml`](.pre-commit-config.yaml) and the `scripts/` directory
2. Run `pre-commit install` to activate the 14 enforcement hooks
3. Use the [`ralph/`](ralph/) review checklists for post-implementation review

### Add AI Governance

1. Configure the [MCP server](mcp-servers/github-checkbox/) for evidence-enforced operations
2. Use the 3-tier Ralph Review (Haiku → Sonnet → Opus) on every merge
3. Follow the [`reference/self-healing-guide.md`](reference/self-healing-guide.md) for incident recovery

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
