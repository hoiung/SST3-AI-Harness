# Pruning Strategy

## When to Prune
- RED alert: Component >95% of cap (IMMEDIATE)
- ORANGE alert: Component >90% (BEFORE next addition)
- Before implementing new features
- After 3+ self-healing additions

## What to Prune (Priority Order)
1. Obsolete content (safe)
2. Verbose examples → concise (careful)
3. Duplicate explanations (careful)
4. NEVER: Guardrails, Common Mistakes, Critical instructions

## Guardrail Protection
NEVER remove content with:
- NEVER, MUST, CRITICAL, MANDATORY markers
- "Common Mistakes" sections
- Housekeeping (3 contexts)
- Iteration limits
- Error prevention instructions

## Quality Gates
Every 500 tokens removed:
- Check 5 quality dimensions
- Verify guardrails intact
- Run check-size-limits.py

See: `../scripts/suggest-pruning.py` for automated suggestions
