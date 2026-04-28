# SST3 Wrapper-Lane Test Fixtures

Frozen known-answer regression gate for the 19+ wrappers in `../scripts/`.

Driven by `sst3-self-test.sh` + `_self_test_driver.py`. Invoked at:

- Pre-commit (`sst3-self-test` hook) on every `../scripts/sst3-*.sh` edit.
- CI (`validate.yml` step "SST3 wrapper integrity self-test (BLOCKING)").
- `/Leader` Stage 1 entry — drift ABORTS swarm dispatch.

## Fixture Layout

Each subdirectory under `test-fixtures/` is a self-contained fixture:

```
test-fixtures/<name>/
├── input/             # synthetic source tree the wrapper operates on
│   └── ...
├── expected.json      # contract — wrapper + args + cwd + assertions
└── run.sh             # OPTIONAL — only for imperative fixtures (see below)
```

`expected.json` supports two shapes:

**A. Declarative** — driver invokes the wrapper directly:

```json
{
  "wrapper": "sst3-code-large.sh",
  "args": [20, "md"],
  "cwd": "input",
  "expect": {
    "exit_code": 0,
    "stdout_min_records": 2,
    "stdout_kind_records": ["large-fn"],
    "stdout_must_contain_files": ["big.md"],
    "stderr_must_contain": ["sst3-code-large:"],
    "stderr_must_match": "scanned \\d+ path"
  }
}
```

**B. Imperative** — fixture supplies its own `run.sh`:

```json
{
  "driver": "run.sh",
  "exit_code": 0,
  "stdout_must_contain": ["PASS: callers", "PASS: callees"]
}
```

Use B only when the assertion logic exceeds what the declarative form
expresses (multi-wrapper interaction, side-effect checks, sentinel-file
absence). Default to A — the declarative form is locked by SHA256
baseline (`_baseline-hashes.json`), so reviewers can spot drift in PRs.

## Drift Types

| Drift                | Meaning                                                     |
|----------------------|-------------------------------------------------------------|
| `recall_drift`       | NDJSON record count or kind below baseline                  |
| `silent_zero`        | Expected non-empty output was empty                         |
| `sentinel_missing`   | stderr `must_contain` substring absent                      |
| `extra_match`        | Negative-match miss (output non-empty when empty expected)  |
| `exit_drift`         | Wrapper exit code != expected                               |
| `error_contract_break` | stderr regex did not match contract                       |
| `truncation`         | NDJSON parse failure (assumes upstream stream cut)          |

## Driver Exit Codes

| Exit | Meaning                                           |
|------|---------------------------------------------------|
| 0    | All fixtures passed                               |
| 1    | One or more fixtures drifted                      |
| 2    | Driver crashed (malformed expected.json, etc)     |
| 64   | Bad CLI args                                      |
| 127  | Engine missing (with `--strict-engines`)          |

## Policy: Fixtures EXPAND ONLY — Never Relax

The instinct to "fix the test by relaxing the assertion" is the failure
mode this gate exists to prevent. Reduction of any assertion (e.g. lowering
`stdout_min_records`, removing a `stdout_must_contain_files` entry,
broadening a `stderr_must_match` regex) requires:

1. An explicit GitHub Issue documenting the assertion change + reason.
2. Reviewer sign-off on the Issue.
3. Updated `_baseline-hashes.json` SHA256 entry committed in the same change.

Adding new assertions, expanding fixture coverage, or adding new fixtures
is encouraged and does not require this process — only assertion
**reduction** is gated.

## Meta-Validation — `_known-broken-wrappers/`

Cherry-picked pre-R4 versions of selected wrappers live under
`_known-broken-wrappers/`. The CI step "Self-test meta-validation" swaps
each broken file into place, runs `sst3-self-test.sh`, asserts non-zero
exit, then restores. This proves fixtures actually catch the bugs they
claim to catch.

Adding a new known-broken wrapper:

1. Place `_known-broken-wrappers/sst3-<name>.sh` (the broken variant).
2. Add a `META.md` row mapping the broken file → fixture(s) it should fail.
3. CI loop in `validate.yml` picks it up automatically.

## Adding a New Fixture (5-step recipe)

1. `mkdir test-fixtures/<name>/input`
2. Drop synthetic source files into `input/`. Keep tiny — fixtures are
   diff-reviewed; thousand-line samples are rejected.
3. Write `expected.json` per the schema above. Start strict; loosen only
   if false positives surface during smoke.
4. Run `bash scripts/sst3-self-test.sh --only <name>` until it
   passes.
5. Run `python3 scripts/_baseline_hash_update.py` to refresh the
   SHA256 baseline (the `sst3-test-fixtures-locked` pre-commit hook
   blocks editing `expected.json` without a hash bump).

## Anchor Files

- Driver: `../scripts/_self_test_driver.py`
- Wrapper: `../scripts/sst3-self-test.sh`
- Pre-commit anchor: `block-code-review-graph-token` hook (line ~42 of `.pre-commit-config.yaml`)
- CI anchor: "Mirror drift unit + integration tests (Issue #418)" step
  in `.github/workflows/validate.yml`
