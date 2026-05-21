# Ralph Review — Shared Doc-Only PR Exemption Block (#498 Cut #10)

> Canonical block for the doc-only exemption clause that haiku/sonnet/opus all need. Each tier file points here.

## Rule

**Documentation-only PR exemption** (run FIRST — short-circuits the wrapper-lane CODE checks below): if the PR diff touches ONLY documentation / non-code files (Markdown, YAML, JSON, TOML, shell scripts, other unsupported languages per STANDARDS.md "Structural Code Queries"), skip the CODE wrapper checks (`sst3-code-*`). Document the skip reason in RESULT: `[GRAPH: skipped — doc-only PR]`. This is a PASS path, not a fallback.

**EXCEPTION (#484 W6.3 — doc-lane is diff-triggered, NOT graph-gated)**: a doc-only PR is NOT exempt from the DOC lane — the doc-lane checkbox in the haiku tier (or sonnet/opus equivalents) still runs because the diff touches `*.md`/frontmatter (canonical rule: WORKFLOW.md Stage 1 "Doc-lane is diff-triggered, NOT graph-gated"). Run it, then proceed to the tier's standard surface/logic/architectural checks.

**Sync-lane diff-trigger (#484 W6.3)**: if the diff changes any `docs/research/*` file or its frontmatter, run `bash dotfiles/SST3/scripts/sst3-sync-related-code.sh` (or `sst3-doc-frontmatter.sh <changed-research.md>`) and confirm the research doc's `related_code` paths still resolve + frontmatter required fields intact. Record exit code in RESULT. Diff-triggered, NOT `graph_applicable`-gated. Skip-clean if no `docs/research/*` change.
