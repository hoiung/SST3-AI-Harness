# Ralph Review — Shared Bash Output Discipline Block (#498 Cut #10 / #406 F4.9)

> Canonical block for the Bash Output Discipline checkbox that haiku/sonnet/opus all need verbatim. Each tier file points here instead of duplicating the text.

## Checkbox

- [ ] If you ran any bash command producing > 200 lines (pytest, git diff, log tail, etc.), you wrapped it with `../dotfiles/SST3/scripts/tee-run.sh <label> -- <cmd>`. Return only the tee path + verdict in your RESULT block; do NOT paste the full output back to the main agent.
