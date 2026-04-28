---
domain: sst3
type: research
related_code:
  - file: dotfiles/scripts/sst3-bash-utils.sh
  - file: dotfiles/this-path-does-not-exist-anywhere.py
  - file: dotfiles/another-fake-path.rs
last_updated: 2026-04-26
---

# Drift Doc

Frontmatter cites 3 paths via related_code; only the first exists. Wrapper
should flag 2 drift records.
