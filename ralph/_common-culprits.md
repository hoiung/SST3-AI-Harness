# Ralph Review — Shared 5-Culprits Reference (#406 F3.4)

> **Architectural design**: Each Ralph tier scans for the same 5 patterns at *increasing depth*. The depth-layering is intentional (per ANTI-PATTERNS.md #8 + Verified Intentional Design). This file holds the shared framing so the category numbers and names stay in sync; each tier file keeps its own depth-appropriate bullets.

## The 5 Categories

Each tier checks these patterns. Bullets in the per-tier files differ by depth, not by category.

| # | Category | Surface (Haiku) | Logic (Sonnet) | Architectural (Opus) |
|---|---|---|---|---|
| 1 | Duplicate Code (DRY/Modularity) | Visible copy-paste | Same logic in N files | Same pattern implemented differently |
| 2 | On-the-fly Calculations (Hardcoded Settings) | Magic numbers in calculations | Inline business formulas | Calculation constants varying by env |
| 3 | Hardcoded Settings | Embedded URLs/paths/credentials | R-multiples, percentages, timeouts | User-configurable values in code |
| 4 | Obsolete/Dead Code (LMCE) | Commented-out blocks, dead TODOs | Never-called functions, unused imports | Modules never instantiated, dead endpoints |
| 5 | Silent Fallbacks (Fail Fast) | `catch{}` swallow, `\|\| default` | `.get(k, {})` chains, `try/except: pass` | Cascading defaults masking root cause |

## Tier Files
- `haiku-review.md` — surface checks (60% of issues)
- `sonnet-review.md` — logic-trace checks (30% of remaining)
- `opus-review.md` — architectural checks (10% of remaining)

## Rule
Tier-specific bullet content lives in the tier files. The category numbers/names live HERE — change them once, propagate by re-reading.
