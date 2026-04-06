# Quality Metrics

## Track These

### Per-Issue
- Quality check results: 5/5 dimensions passed?
- Changes applied vs. skipped
- Self-healing additions: Validated / Failed
- Bug catch rate (Stage 5)

### System-Wide
- Guardrail integrity: All preserved?
- Cross-reference accuracy: All links work?
- Script functionality: All scripts pass tests?

### Trend Analysis
- Quality score over last 10 issues
- Self-healing success rate trend
- Bug detection effectiveness

## Targets

- Quality score: >= 4.5 / 5.0
- Warning: < 4.0 / 5.0
- Critical: < 3.5 / 5.0

## Historical Baseline

*Baseline established in Issue #119*
- Pre-pruning: 29,596 tokens (84.6% of cap)
- Post-pruning: 24,192 tokens (69.1% of cap)
- Quality score: 4.8 / 5.0 (validated by Stage 5)

See: quality-audit.py for comprehensive audits
