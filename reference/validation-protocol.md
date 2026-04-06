**⚠️ READ IN FULL - DO NOT SKIP SECTIONS ⚠️**
**This document contains critical procedures that must be followed sequentially. Selective reading causes execution failures.**

# Self-Healing Validation Protocol

## 3-Issue Observation Period

When Stage 5 (Post-Implementation Review) adds self-healing content:

1. **Mark as VALIDATING**
   - Commit message: "Self-healing update from Issue #X (VALIDATING)"
   - Add to tracking file

2. **Observe for 3 Issues**
   - Did mistake recur? (Yes/No)
   - Did instruction help? (Yes/No)
   - Did it cause confusion? (Yes/No)

3. **Auto-Decision After 3 Issues**
   - Success (3/3): Mark VALIDATED, keep
   - Partial (1-2/3): Refine, observe 3 more
   - Failure (0/3): AUTO-REVERT, document

4. **Track in failed-experiments.md**

## Validation Tracking Template

```json
{
  "change_id": "issue-119-self-monitoring",
  "issue_origin": 119,
  "change_description": "Added subagent-monitoring.md [archived]",
  "date_added": "2025-11-09",
  "validation_status": "VALIDATING",
  "observations": [
    {"issue": 120, "helped": true, "confusion": false},
    {"issue": 121, "helped": true, "confusion": false},
    {"issue": 122, "helped": true, "confusion": false}
  ],
  "final_decision": "VALIDATED",
  "decision_date": "2025-11-15"
}
```

See: STANDARDS.md "Rollback Cleanup"
