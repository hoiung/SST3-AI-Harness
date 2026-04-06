"""
SST3 Limits Configuration
Single source of truth for all SST3 token and line limits.
Used by check-size-limits.py and pre-commit hooks
"""

# Folders that the auto-stage hook tracks. Single source of truth so the same
# list is consumed by auto-stage-tracked-folders.py and any future tooling
# that needs to know which "always-tracked" folders exist (#406 F1.14).
TRACKED_AUTOSTAGE_FOLDERS = ["SST3-metrics", "archive", "docs"]


# Total SST3 token limits (updated for 1M context window, #399)
# Previous caps (100K) were set for 200K context (50% budget).
# New caps (150K) are 15% of 1M — conservative, leaves 850K for actual work.
LIMITS = {
    # Overall SST3 limits
    "SST3_TOTAL_TARGET": 130000,  # 13% of 1M — was 90000
    "SST3_TOTAL_CAP": 150000,     # 15% of 1M — was 100000

    # Component-level token limits (rebalanced post-cleanup, #399)
    "SST3/workflow": 10000,    # actual ~2,239 — was 44000 (massively over-allocated)
    "SST3/standards": 20000,   # raised 2026-04-08 18000->20000 to absorb AP #9-#14 + Subagent Discipline section
    "SST3/templates": 18000,   # actual ~12,062 post-cleanup — was 14000
    "SST3/reference": 16000,   # actual ~13,168 post-cleanup — was 21000

    # Special file with LINE limit (not tokens)
    "CLAUDE.md": 500  # lines, not tokens - user-specified limit
}


def is_token_limit(key):
    """Check if a limit is measured in tokens (vs lines)."""
    return key != "CLAUDE.md"


def count_tokens(text: str) -> int:
    """Approximate token count (chars / 4). Used by check-size-limits.py and suggest-pruning.py."""
    return len(text) // 4
