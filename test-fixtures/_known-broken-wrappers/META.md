# Known-Broken Wrappers — Meta-Validation Manifest

These are deliberately-broken variants of active wrappers. The CI step
"Self-test meta-validation" swaps each file into place, runs
`sst3-self-test.sh`, asserts non-zero exit, then restores the active
wrapper. They prove fixtures actually catch the bugs they claim to.

| Broken file                          | Bug class                                  | Fixture that MUST fail        |
|--------------------------------------|--------------------------------------------|-------------------------------|
| `sst3-code-large.sh`                 | Markdown branch removed (#447 Phase 3)     | `code-large-md`               |
| `sst3-doc-frontmatter.sh`            | EXIT-trap stderr sentinel removed (Phase 2)| `doc-frontmatter-clean`       |

## Live-wrapper drift class (Issue #456 Phase 2 — NOT a swap-loop fixture)

Issue #456 added a new bug class: **missing `source sst3-bash-utils.sh`** in an active end-user wrapper, which makes the wrapper's inner engine unreachable from non-interactive `bash --noprofile --norc -c '...'` shells (the `.bashrc` PATH augment never reaches non-interactive subshells per Ubuntu stock `~/.bashrc:5-9` early-return). The drift class targets LIVE wrappers, NOT swap-loop fixtures — the swap loop above requires an active wrapper of the same name to swap against, and a "missing-source" drift class has no active counterpart by definition. Detection is via `_self_test_driver.py:_check_wrapper_bash_utils_drift()` + the `check-wrapper-bash-utils-source` pre-commit hook (declared BEFORE `sst3-self-test` in `.pre-commit-config.yaml`); exempt wrappers (system-PATH-only) are listed in `../scripts/.bash-utils-exempt-list`. No row added to the table above because no swap-loop fixture exists for this class — it is verified by synthesised drift testing only.

## Adding a new broken-variant

1. Drop the broken `sst3-*.sh` here.
2. Add a row above mapping `Broken file` → `Bug class` → `Fixture(s) that must fail`.
3. Verify locally:
   ```bash
   cp test-fixtures/_known-broken-wrappers/sst3-<name>.sh scripts/sst3-<name>.sh.broken
   mv scripts/sst3-<name>.sh scripts/sst3-<name>.sh.bak
   mv scripts/sst3-<name>.sh.broken scripts/sst3-<name>.sh
   bash scripts/sst3-self-test.sh; echo "exit=$?"   # MUST be 1, not 0
   mv scripts/sst3-<name>.sh.bak scripts/sst3-<name>.sh
   ```
4. CI loop in `.github/workflows/validate.yml` picks it up automatically
   from the table above.

## Why not git cherry-pick a real pre-fix version?

Cherry-picking a pre-R4 commit would (a) drag in unrelated changes from
that commit's diff, and (b) break compile/lint/style as those wrappers
evolved. Hand-written minimal-broken variants isolate the single bug
class they prove the fixture catches.
