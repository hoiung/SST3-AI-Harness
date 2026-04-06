# SST3 Regression Test Suite

Comprehensive regression tests for SST3 workflow system to prevent quality degradation.

## What

This test suite validates SST3 quality across 8 dimensions:
1. **Discoverability** - All files reachable from CLAUDE.md
2. **Stage Execution** - All 5 stages have complete checklists
3. **Subagent Quality** - Launch instructions are clear
4. **Monitoring** - Self-monitoring systems work
5. **Recovery** - Self-healing playbooks are complete
6. **Communication** - Templates and protocols defined
7. **Quality Validation** - 5-dimension framework intact
8. **Cross-Repo** - Works in all repositories

**Baseline**: 92/100 quality score (from Issue #131)

## Get

```bash
# Run all tests
cd /path/to/your/dotfiles
python SST3/tests/regression-suite.py

# Run specific category
python SST3/tests/regression-suite.py --category discoverability

# Verbose output
python SST3/tests/regression-suite.py --verbose

# Compare against baseline
python SST3/tests/regression-suite.py --baseline
```

## Install

**Prerequisites**:
- Python 3.8+
- No external dependencies (uses standard library only)

**Structure**:
```
SST3/tests/
├── regression-suite.py                    # Main test runner
├── test_checklist_quality.py              # Checklist quality tests (NEW)
├── test_execution_validation.py           # Execution validation tests (NEW)
├── test_semantic_quality.py               # Semantic quality tests (NEW)
├── test_path_portability.py               # Path portability tests (NEW)
├── test_template_quality.py               # Template quality tests (NEW)
├── test_edge_cases.py                     # Edge case tests (NEW)
├── test_framework_validation.py           # Framework validation tests (NEW)
├── test_discoverability.py                # CLAUDE.md → files tests
├── test_stage_execution.py                # All 5 stages validation
├── test_subagent_quality.py               # Subagent instructions
├── test_monitoring.py                     # Self-monitoring validation
├── test_recovery.py                       # Self-healing validation
├── test_communication.py                  # Templates and protocols
├── test_quality_validation.py             # 5-dimension framework
├── test_cross_repo.py                     # Multi-repo validation
└── README.md                              # This file

Test Results (written to SST3-metrics/test-results/):
├── baseline-measurements.json             # Current baseline
├── latest-results.json                    # Most recent run
└── execution-history/                     # Timestamped runs
```

## Test Categories

### 1. Discoverability (15% weight)
- Validates all SST3 files discoverable from CLAUDE.md
- Tests discovery chain: CLAUDE.md → WORKFLOW.md → stages → features
- Ensures no broken references
- Cross-repo path validation

### 2. Stage Execution (20% weight)
- Validates all 5 stages have complete checklists
- Checks DO/DON'T sections present
- Verifies Common Mistakes documented
- Ensures Self-Check sections exist

### 3. Subagent Quality (10% weight)
- Validates launch templates complete
- Checks model selection criteria clear
- Ensures temp/ location specified
- Verifies handoff protocols defined

### 4. Monitoring (10% weight)
- Checks token budget calculations
- Tests alert level triggers
- Verifies freeze detection parameters

### 5. Recovery (10% weight)
- Validates self-healing guide complete
- Checks recovery playbooks present
- Tests rollback procedures
- Verifies failed experiments tracking

### 6. Communication (10% weight)
- Validates templates complete
- Checks Issue update formats
- Tests PR creation protocols
- Verifies handover procedures

### 7. Quality Validation (15% weight)
- Validates 5-dimension framework
- Checks PASS/FAIL examples present
- Tests anti-patterns documented
- Verifies quality scripts exist

### 8. Cross-Repo (10% weight)
- Validates works in 3 repos
- Checks relative path resolution
- Tests template propagation
- Verifies multi-language support

## Baseline

**Established**: Issue #131 (2025-11-11)
**Score**: 92/100
**Components**:
- Discoverability: 100%
- Stage Execution: 95%
- Subagent Quality: 90%
- Monitoring: 85%
- Recovery: 90%
- Communication: 95%
- Quality Validation: 90%
- Cross-Repo: 95%

**Acceptable Range**: 90-94 (±2 points)
**Failing Threshold**: <85 (requires investigation)

## Maintenance

**When to update tests**:
1. SST3 workflow changes (new stages, modified checklists)
2. New quality dimensions added
3. Baseline changes (after validated improvements)

**How to update baseline**:
```bash
# 1. Run tests to get current score
python SST3/tests/regression-suite.py

# 2. If score improved with evidence, update baseline
python SST3/tests/regression-suite.py --update-baseline

# 3. Document in Issue why baseline changed
# Results written to: SST3-metrics/test-results/baseline-measurements.json
```

## CI/CD Integration

**GitHub Actions** (future):
```yaml
name: SST3 Regression Tests
on: [pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: python SST3/tests/regression-suite.py
```

**Pre-commit Hook** (optional):
```bash
# .git/hooks/pre-commit
python SST3/tests/regression-suite.py || exit 1
```

## Learn

- **Issue #133**: Test suite creation
- **Issue #131**: Baseline establishment (92% quality)
- **Issue #119**: Self-monitoring functions
- **quality-validation.md**: 5-dimension framework

---

**Created**: 2025-11-11 (Issue #133)
**Maintained By**: SST3 self-healing process
