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

## Why This Exists

Most AI-assisted development uses LLMs as line-level autocomplete. SST3 takes a different approach: the human is the **orchestrator** who designs the work, and LLM agents execute it under quality constraints, the same way a technical lead directs a cross-functional team.

This matters because:
- **Without governance**, LLM agents produce inconsistent quality, drift from scope, and silently introduce regressions
- **Without structure**, context is lost between sessions, leading to rework and contradictory decisions
- **Without enforcement**, standards exist on paper but are not followed in practice

SST3 solves all three through automated quality gates, structured delivery processes, and pre-commit enforcement that makes compliance the path of least resistance.

## Why We Chose This Route (Lessons from SST2)

SST3 did not start as "one orchestrator, subagents read-only". The earlier generation (SST2) looked a lot like the mainstream agent frameworks out there today. One main orchestrator, a pool of specialised agents with different skills, coordination protocols between them, every agent free to make file changes. Basically the LangChain / CrewAI shape, with my own guardrails, standards, and anti-patterns bolted on.

It was disastrous.

Some of that was my inexperience at the time. Some of it was the tooling available then. Some of it was the 200K context window Claude had in late 2024, which was simply not enough for a multi-agent swarm to hold a shared mental model of a production codebase. The agents would go in different directions, make overlapping edits, step on each other's work, and produce a codebase that was technically alive but architecturally incoherent.

Even with the guardrails in place, it was like letting 5 to 10 cowboy agents fire away at the same time. Each one confident. Each one making changes. Each one creating a mess somewhere that took ages to clean up later. I suspect my tradebook system still has lingering stale and contradictory code from that era. I tried to clean it up. I genuinely did. Every time I thought I was done, I'd find more. At some point it became one of those defeats you just accept: the production code has legacy technical debt I haven't fully exorcised, I've moved on, and the rule now is that new code doesn't touch the legacy mess or accidentally integrate with it. The worst part is that you only feel the pain months later, long after the agents have finished. By then you have no memory of which agent changed what, or why. Debugging becomes archaeology.

So SST3 took the opposite route. Focused. Narrow. One main orchestrator agent owns the writing, always. Subagents are dispatched like a research team, not a coding team. They read, they analyse, they report findings. They never touch the code. Each subagent is also deliberately pointed at a new angle or perspective the previous subagents haven't covered, so the main orchestrator agent ends up with a 360-degree view of the problem instead of five copies of the same answer. Each angle gets double-checked and triple-checked by layered subagents. The code still gets touched (that's the whole point), but only by the main orchestrator agent, and every piece is revised, finetuned, and optimised against those cross-angle findings, verified against [`STANDARDS.md`](standards/STANDARDS.md) and [`ANTI-PATTERNS.md`](standards/ANTI-PATTERNS.md), then put through regression tests, end-to-end (E2E) tests, and injection tests before it ships. That last layer is how the 80% working trust gets pushed up to 90-95% "good enough, won't break, won't fail in the wild". That one constraint (read-only, different angle each time) kills about 80% of the mess SST2 used to generate.

**Build it like Lego.** One piece at a time. Each piece has to be gold-quality and polished before it gets inserted. Once it fits with the surrounding pieces, move on. Never stack two half-finished bricks and hope they'll settle. This is the opposite of how many AI frameworks think about "throughput". SST3 doesn't optimise for "how many agents can I run in parallel?". It optimises for "how few clean pieces can I ship per hour, with zero rework?".

The 1M context window that arrived in 2025 made this approach practical at scale. The main orchestrator agent can hold the Issue, the standards, the research, and the full diff without spilling context. Subagents absorb the high-volume reads on its behalf. The orchestrator stays coherent. The code stays coherent. No more cowboys.

## Why You Should Spend More Tokens Refining a Quality Scope

Every harness does some form of scoping. That is the easy part. The hard part, and the part that actually separates a usable methodology from a waste of tokens, is the PROCESS you use to refine the scope into something sharp enough to act on. A loose scope is a shitty scope, no matter how many agents you throw at it.

I spend a lot of tokens, a lot of subagents, and a lot of time refining the scope before a single line of code gets written. That is deliberate, and it is the single biggest lesson from two decades of Project Management, IT engineering, running my own businesses, and leading teams through plenty of failures and a fair number of successes.

The biggest killer of any project is unclear instructions and scope that is not well defined. You can have the smartest team and the best tools in the world; if the scope is fuzzy, the output will be fuzzy. Worse, you only discover the fuzziness after you have already spent money and time building the wrong thing.

Taking the first step in the right direction is the most important decision you make. It is like having a map of where you want to get to. There are many ways to reach the destination, but you want to plan the route so you can navigate the obstacles, challenges, and gotchas that would otherwise stop you from getting there easily or quickly.

I find it far cheaper to have a clear plan that is still flexible to changes than a loose plan that gets lost or misinterpreted. The loose plan costs you later: you look up months down the line, realise you have drifted further from the goal, and then you pay twice to find your way back. Cleaning up a mess from bad code is hard, sometimes genuinely painful, and sometimes the scars never fully heal once the bad code has shipped to production.

The sneaky part is the compounding. Small gaps and poor implementations do not announce themselves on day one. They sit there quietly, and every new feature you build on top of them inherits the same weak foundation. Miss a gap this week, the next piece layers on top of it, then the one after that, and before you know it you have a snowball. You end up with a fragile production system that breaks the moment the wind changes direction. This is why the token spend on refining scope up front is a magnitude cheaper than the cleanup bill you avoid downstream.

That is what technical debt actually is. And SST3 is built to prevent it from accumulating, or at least reduce it enough that the damage does not compound into something that costs ten times more to fix or maintain later. Think ahead. Scope properly. Pay a bit more in the planning phase so you do not pay a fortune in the cleanup phase.

That is why SST3 spends more tokens on each piece. Each piece gets researched, scoped, verified, triple-checked, implemented, reviewed, and audited before it ships. Yes, it is more expensive per piece in tokens. It is dramatically cheaper overall, because you are not constantly rebuilding on top of broken foundations.

Quality over quantity. ALWAYS.

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

## Think of It as a Hero Suit

SST3 is a customisable hero suit. You are the subject matter expert. You already know your domain, your field, your craft. The harness doesn't replace that. It amplifies it.

Think of it like a reshapeable knife. The same tool in different hands serves different purposes: a chef's blade, a surgeon's scalpel, a samurai's katana, a butcher's cleaver. The knife doesn't know how to cook or operate or fight. The expert does. The tool just makes them faster and more precise.

That's what SST3 does. It's an accelerator. A catalyst that speeds up your already latent power. You direct the agents, you make the calls, you judge what's right and wrong. The harness enforces the discipline so nothing falls through the cracks while you work at speed. (Be careful of burnouts though. Working at 10x pace means you can also burn out at 10x pace.)

Here's the catch: if you're still learning your field, the harness won't save you. You'll struggle to judge whether the AI's output is right or wrong. You'll become dependent on it rather than your own intellect, experience, and knowledge. That's not the harness failing. That's trying to wear a hero suit before you've built the strength to carry it.

SST3 is built for people who already know what they do. Domain experts. Subject matter experts (SMEs). Technical leads who can look at an AI agent's output and immediately spot what's wrong. The suit fits those who've already earned the muscle. You do have to finetune it to fit you and what you want to do with it. Once finetuned, it's a well oiled machine.

And the AI skills? Those are the suit's enhancements. Weapons, shields, scanners, whatever your domain needs. But skills used alone aren't effective. A skill without the harness is a loose attachment with no frame to mount it on. SST3 is the frame. The skills plug into it, draw power from its governance and quality gates, and that's what lets them run at full potential. The harness without skills is a solid suit. Skills without the harness is a pile of parts on the floor.

You can use it to build automation, to research, to write, to analyse, all with tight guardrails that reduce hallucination and the bullshit AI spouts at times which is not factual or true. It's not perfect, but it's far better than Claude Code out the box. My principle is KISS (Keep It Simple Stupid), so this framework is built to be reliable and simple to customise without all the additional LLM wiki or graphs or other memory frameworks which add complexity and more parts to fail. (That doesn't mean I won't try them and see if they can improve SST3-AI-Harness or larger projects that work alongside the harness, but the current version works reliably.)

## Not Just for Engineering

SST3 is not an IT tool. It's a methodology for wrapping AI with guardrails, and guardrails apply to every department that produces work under a quality standard.

- **Marketing**: brand voice profile, banned-vocab lists, SEO checklists, approval gates before a campaign ships. Same structure as the voice guard that runs over this very README.
- **HR**: job description templates, interview rubrics, bias sweeps, tone-of-voice guides. SME sets the rules, AI drafts, the harness enforces, human reviews in minutes instead of hours.
- **Finance and accounting**: regulatory disclosures, audit-trail compliance, report templates where a wrong figure ends careers. Fail-fast enforcement and evidence-enforced approvals are non-optional here.
- **R&D**: research protocols, literature-review methodology, hypothesis validation checklists. The senior researcher's judgement becomes the rules; AI accelerates grunt work inside the method, not around it.

The pattern is always the same: SMEs set the standards, AI produces the first pass, the harness enforces compliance, humans review the output. Same shape whether the output is code, ad copy, a financial disclosure, or a research protocol.

## Trust Model: The 80:20 Rule

Never fully trust AI. Not 100%. Not even 90%. With SST3 wrapped around the agents, working trust sits at around 80%, meaning 80% of output is clean enough to use with light review. The remaining 20% is a grey zone where the AI tends to fudge things, and over time you learn where it usually tries. That 20% is why human review gates at Stage 4–5 are mandatory.

Before SST3, the ratio was flipped: maybe 20% usable, 80% slop. The harness turns that around. It does not hand over the keys. It keeps the keys in your hand while the AI does the driving under supervision.

## SMEs and Juniors: Who Benefits, Who Should Be Careful

**Domain experts and SMEs become force multipliers.** The harness captures your judgement as rules, templates, and anti-patterns. AI executes against your bar. You review with the eye of someone who spots wrongness in seconds. Week-long tasks compress to a day. Day-long tasks compress to an hour.

**Juniors and those still learning: the harness is a good learning tool, but it is not a substitute for the craft.** The guardrails surface the standards. Ralph Review pass/fail feedback teaches what "good" looks like. The anti-patterns list is effectively a catalogue of senior-level mistakes so juniors don't repeat them. But dependency on the harness without building underlying judgement is a trap. Training wheels should come off eventually. Use it to accelerate learning, not replace it.

## Why Embrace It

Humans have an edge AI does not. Creativity. Abstract reasoning across many angles at once. The ingenuity that put people on the moon, that built aircraft, submarines, and the light bulb. Those came from humans staring at walls and daydreaming, not algorithms. That is a uniquely human trick and it should be guarded.

The tasks that can be automated should be automated. Not because humans are lazy. Because human time is better spent on the work AI cannot do alone. Will AI take jobs? Not the way most people fear. It will shift work toward strategy, creativity, and judgement. Companies are still made of people; not the other way around. The ones that remember this will win.

If you can't adapt to this tech age, your job will eventually adapt for you. Better to be the person who learnt the harness than the person who got replaced by someone who did.

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
