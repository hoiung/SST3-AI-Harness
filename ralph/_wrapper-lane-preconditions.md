# Ralph Review — Shared Wrapper-Lane Preconditions Block (#498 Cut #10)

> Canonical block for the wrapper-lane preconditions paragraph that haiku/sonnet/opus all need. Each tier file points here instead of duplicating the text.

## Preconditions (code-touching PRs, run once per review)

`bash dotfiles/SST3/scripts/sst3-code-status.sh` exits 0 and emits valid JSON `{last_updated, file_count, source_languages}`. The wrapper-lane is stateless — there is no staleness check; every query re-parses on disk. If the wrapper exits non-zero (missing inner engine), skip to the per-tier fallback clause (see [`_fallback-clause.md`](_fallback-clause.md)).

**Exit 127 semantics (post Issue #456)**: means the engine is **genuinely missing on disk** (npm/cargo/pipx install never ran). Pre-#456 the same code ALSO fired when the engine was on disk but PATH was not propagated to non-interactive shells; that PATH-propagation gap is now closed by `../dotfiles/SST3/scripts/sst3-bash-utils.sh` self-bootstrap. Run `scripts/install.sh` to install missing engines — do NOT add custom PATH workarounds in the calling agent.

**Rollout note**: required-when-available wording became authoritative with Issue #419. Reviews in-flight at #419 merge-time grandfathered UNTIL the branch's next push; any review dispatched after that push follows the full required-when-available rule.

**AP #19 `mcp_graph_available` field rule (wrapper-lane epoch — Issue #445)**: every subagent RESULT block that discusses graph queries MUST include `mcp_graph_available: yes|no` as the first line. Under the wrapper-lane this field is **always `no`** — wrappers are bash-tool calls, not MCP-protocol calls; subagents do not inherit the bash-tool set the same way. Documented grep + manual-read fallback is the EXPECTED path, not a degradation. Ralph Tier 1 uses this field with documented-fallback evidence:
- `mcp_graph_available: no` + grep / subagent fallback evidence = PASS (acceptable — documented fallback is the requirement)
- `mcp_graph_available: no` + NO fallback evidence = FAIL (silent skip)
