# Guardrail Detection

NEVER remove content with these patterns during pruning:

## 1. Explicit Markers
- NEVER, MUST, CRITICAL, MANDATORY
- DO NOT, ALWAYS, REQUIRED
- WARNING, DANGER, IMPORTANT

## 2. Common Mistake Sections
- "Common Mistakes"
- "Pitfalls to Avoid"
- "Anti-patterns"
- "What NOT to do"

## 3. Housekeeping Rules
3-context pattern:
1. Subagent prompt: "Document all files you CREATE/MODIFY in Issue #X"
2. Subagent final report: "Files Created/Modified" sections
3. Issue comment: Summary of changes

## 4. Iteration Limits
- "Max iterations: X"
- "Try up to N times"
- "Limit: X attempts"

## 5. Error Prevention
- "Check X before Y"
- "Verify Z exists"
- "MUST validate"

See: `../scripts/suggest-pruning.py` for automated detection
