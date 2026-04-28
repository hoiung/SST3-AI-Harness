#!/usr/bin/env python3
"""SST3 wrapper-lane self-test driver (#447 Phase 4).

Reads every `dotfiles/test-fixtures/*/expected.json`, runs the named
wrapper (or `driver` script) with cwd set to the fixture's `input/` subdir,
captures stdout + stderr + exit code, and applies the assertions in
`expected.json`. Emits NDJSON to stdout — one record per fixture, plus a
terminating `{kind:"self-test-complete", ...}` sentinel via EXIT trap.

The fixture contract — both supported:

A. Imperative — fixture supplies its own driver:
    {
      "fixture": "command-injection",
      "driver": "run.sh",
      "exit_code": 0,                 # required driver exit
      "stdout_must_contain": [...]    # substrings driver stdout MUST carry
    }

B. Declarative — driver invokes wrapper directly:
    {
      "fixture": "code-large-py",
      "wrapper": "sst3-code-large.sh",
      "args": ["50", "python"],
      "cwd": "input",                 # relative to fixture dir; default "input"
      "expect": {
        "exit_code": 0,
        "stdout_kind_records": ["large-fn"],   # NDJSON kinds that MUST appear
        "stdout_min_records": 1,                # minimum NDJSON line count
        "stdout_must_contain_files": ["src/big.py"],
        "stderr_must_match": "<regex>",
        "stderr_must_contain": ["sst3-code-large:"]
      }
    }

Drift types (per Issue #447 Phase 4):
    recall_drift          stdout NDJSON record count below baseline (assertion miss)
    silent_zero           expected non-empty stdout was empty
    sentinel_missing      stderr sentinel absent (`stderr_must_contain` miss)
    extra_match           unexpected file or symbol surfaced (negative-match miss)
    exit_drift            wrapper exit code != expected
    error_contract_break  stderr error format diverged from contract regex
    truncation            stdout shorter than baseline by >X% (NDJSON parse failure)

Wrapper-drift types (per Issue #456 Phase 2 — live-wrapper PATH-bootstrap audit):
    wrapper-drift-missing-source   active end-user wrapper does NOT source
                                   sst3-bash-utils.sh and is not on the
                                   .bash-utils-exempt-list (engine
                                   unreachable from non-interactive bash)
    wrapper-drift-source-position  wrapper sources sst3-bash-utils.sh AFTER
                                   a `command -v <engine>` check (PATH not
                                   yet augmented when engine is probed)

Exit codes (process-level):
    0   all fixtures pass
    1   one or more fixtures drifted
    2   driver crashed (caller, malformed expected.json, missing wrapper)
    64  bad CLI args
    127 engine missing on dev host (wrapper exits 127)
"""

from __future__ import annotations

import argparse
import atexit
import json
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

SCRIPTS_DIR = Path(__file__).resolve().parent
FIXTURES_DIR = SCRIPTS_DIR.parent / "test-fixtures"
REPO_ROOT = SCRIPTS_DIR.parent.parent if SCRIPTS_DIR.parent.name == "SST3" else SCRIPTS_DIR.parent

DRIFT_TYPES = (
    "recall_drift",
    "silent_zero",
    "sentinel_missing",
    "extra_match",
    "exit_drift",
    "error_contract_break",
    "truncation",
)

# Per-fixture timeout — wrapper-lane fixtures are tiny; 30s is generous.
FIXTURE_TIMEOUT_SEC = 30


def _emit(record: dict[str, Any]) -> None:
    print(json.dumps(record, separators=(",", ":")))
    sys.stdout.flush()


_state = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "drift_fixtures": [],
    "wrapper_drift_count": 0,
}


def _exit_sentinel() -> None:
    _emit(
        {
            "kind": "self-test-complete",
            "total": _state["total"],
            "passed": _state["passed"],
            "failed": _state["failed"],
            "drift": _state["drift_fixtures"],
            "wrapper_drift_count": _state["wrapper_drift_count"],
        }
    )


atexit.register(_exit_sentinel)


def _sigterm(_signum, _frame):
    _emit(
        {
            "kind": "self-test-killed",
            "total": _state["total"],
            "passed": _state["passed"],
            "failed": _state["failed"],
            "drift": _state["drift_fixtures"],
        }
    )
    sys.exit(143)


signal.signal(signal.SIGTERM, _sigterm)


def _run(cmd: list[str], cwd: Path) -> tuple[int, str, str, float]:
    t0 = time.monotonic()
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=FIXTURE_TIMEOUT_SEC,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return 124, "", f"TIMEOUT after {FIXTURE_TIMEOUT_SEC}s", time.monotonic() - t0
    return proc.returncode, proc.stdout, proc.stderr, time.monotonic() - t0


def _check_imperative(spec: dict, fixture_dir: Path) -> dict:
    """Driver-script style fixture — the fixture's run.sh enforces its own
    assertions. We just check exit code and that any declared stdout markers
    appear in driver output."""
    driver = fixture_dir / spec["driver"]
    if not driver.exists():
        return {
            "drift": "exit_drift",
            "reason": f"driver script {driver} missing",
        }
    rc, out, err, dur = _run(["bash", str(driver)], fixture_dir)
    expected_rc = spec.get("exit_code", 0)
    if rc != expected_rc:
        return {
            "drift": "exit_drift",
            "reason": f"exit={rc} expected={expected_rc}",
            "stderr_tail": err[-400:] if err else "",
            "stdout_tail": out[-400:] if out else "",
            "duration_sec": round(dur, 3),
        }
    for needle in spec.get("stdout_must_contain", []):
        if needle not in out:
            return {
                "drift": "recall_drift",
                "reason": f"stdout missing required substring: {needle!r}",
                "stdout_tail": out[-400:] if out else "",
                "duration_sec": round(dur, 3),
            }
    for needle in spec.get("stderr_may_contain", []):
        # stderr_may_contain is informational — non-presence is NOT a fail.
        # Recorded only.
        pass
    return {"drift": None, "duration_sec": round(dur, 3)}


def _parse_ndjson(text: str) -> list[dict]:
    out = []
    for line in text.splitlines():
        line = line.strip()
        if not line or not line.startswith("{"):
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            return []  # truncation signal — caller treats as drift
    return out


def _check_declarative(spec: dict, fixture_dir: Path) -> dict:
    wrapper = SCRIPTS_DIR / spec["wrapper"]
    if not wrapper.exists():
        return {"drift": "exit_drift", "reason": f"wrapper {wrapper} missing"}
    cwd_rel = spec.get("cwd", "input")
    cwd = (fixture_dir / cwd_rel).resolve() if cwd_rel else fixture_dir
    if not cwd.exists():
        return {"drift": "exit_drift", "reason": f"cwd {cwd} missing"}
    args = [str(a) for a in spec.get("args", [])]
    rc, out, err, dur = _run(["bash", str(wrapper), *args], cwd)
    expect = spec.get("expect", {})
    expected_rc = expect.get("exit_code", 0)
    if rc != expected_rc:
        # 127 = engine missing — surfaced separately by the driver process exit.
        return {
            "drift": "exit_drift",
            "reason": f"exit={rc} expected={expected_rc}",
            "stderr_tail": err[-400:] if err else "",
            "stdout_tail": out[-400:] if out else "",
            "duration_sec": round(dur, 3),
        }
    records = _parse_ndjson(out) if out.strip() else []
    if "stdout_min_records" in expect:
        if len(records) < expect["stdout_min_records"]:
            return {
                "drift": "silent_zero" if not records else "recall_drift",
                "reason": f"records={len(records)} expected>={expect['stdout_min_records']}",
                "stdout_tail": out[-400:] if out else "",
                "duration_sec": round(dur, 3),
            }
    if expect.get("stdout_must_be_empty"):
        if out.strip():
            return {
                "drift": "extra_match",
                "reason": f"stdout non-empty when empty expected; got {len(out)} bytes",
                "stdout_tail": out[-400:],
                "duration_sec": round(dur, 3),
            }
    for kind in expect.get("stdout_kind_records", []):
        if not any(r.get("kind") == kind for r in records):
            return {
                "drift": "recall_drift",
                "reason": f"no record with kind={kind!r} in {len(records)} records",
                "stdout_tail": out[-400:] if out else "",
                "duration_sec": round(dur, 3),
            }
    for fname in expect.get("stdout_must_contain_files", []):
        # Search across the canonical key alternatives wrappers use:
        # `file` (default), `doc` (sync-related-code), `claimed_path` (sync-*),
        # `path` (variant). If none match record-by-record, fall back to a
        # raw-substring check on stdout — covers wrappers that flatten
        # paths into composite messages.
        keys = ("file", "doc", "claimed_path", "path", "url")
        record_hit = any(
            fname in (r.get(k) or "") for r in records for k in keys
        )
        if not record_hit and fname not in out:
            return {
                "drift": "recall_drift",
                "reason": f"no record references file substring {fname!r}",
                "stdout_tail": out[-400:] if out else "",
                "duration_sec": round(dur, 3),
            }
    for needle in expect.get("stdout_must_contain", []):
        if needle not in out:
            return {
                "drift": "recall_drift",
                "reason": f"stdout missing substring: {needle!r}",
                "stdout_tail": out[-400:] if out else "",
                "duration_sec": round(dur, 3),
            }
    if "stderr_must_contain" in expect:
        for needle in expect["stderr_must_contain"]:
            if needle not in err:
                return {
                    "drift": "sentinel_missing",
                    "reason": f"stderr missing required substring: {needle!r}",
                    "stderr_tail": err[-400:] if err else "",
                    "duration_sec": round(dur, 3),
                }
    if "stderr_must_match" in expect:
        if not re.search(expect["stderr_must_match"], err):
            return {
                "drift": "error_contract_break",
                "reason": f"stderr did not match regex: {expect['stderr_must_match']!r}",
                "stderr_tail": err[-400:] if err else "",
                "duration_sec": round(dur, 3),
            }
    return {"drift": None, "duration_sec": round(dur, 3), "record_count": len(records)}


def _run_fixture(fixture_dir: Path) -> dict:
    expected_path = fixture_dir / "expected.json"
    if not expected_path.exists():
        return {
            "fixture": fixture_dir.name,
            "drift": "exit_drift",
            "reason": "expected.json missing",
        }
    try:
        spec = json.loads(expected_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return {
            "fixture": fixture_dir.name,
            "drift": "error_contract_break",
            "reason": f"expected.json parse error: {e}",
        }
    if "driver" in spec:
        result = _check_imperative(spec, fixture_dir)
    elif "wrapper" in spec:
        result = _check_declarative(spec, fixture_dir)
    else:
        return {
            "fixture": fixture_dir.name,
            "drift": "error_contract_break",
            "reason": "expected.json has neither 'driver' nor 'wrapper' key",
        }
    result["fixture"] = fixture_dir.name
    result["wrapper"] = spec.get("wrapper") or spec.get("driver")
    return result


def _read_exempt_list() -> set[str]:
    """Read scripts/.bash-utils-exempt-list — one basename per line,
    `#` for inline justification comments. Returns empty set if file missing."""
    path = SCRIPTS_DIR / ".bash-utils-exempt-list"
    if not path.exists():
        return set()
    out: set[str] = set()
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if line:
            out.add(line)
    return out


_SOURCE_RE = re.compile(r"^\s*(\.|source)\s+.*sst3-bash-utils\.sh")
# Engine list = PATH-augmented inner engines (Issue #456 Phase 3 grep pattern).
# System-PATH tools (jq / rg / git / python3 / bash) intentionally excluded — they
# resolve via /usr/bin without the bash-utils PATH augment, so a `command -v jq`
# inside a SIGTERM handler before the source line is NOT a position drift.
_ENGINE_CHECK_RE = re.compile(
    r"\bcommand\s+-v\s+(ast-grep|lychee|coverage|markdownlint(-cli2)?|yamllint|pip-audit|cargo)\b"
)


def _check_wrapper_bash_utils_drift() -> None:
    """Walk scripts/sst3-*.sh wrappers; emit wrapper-drift NDJSON records.

    Existence rule: any wrapper missing `source ... sst3-bash-utils.sh` AND
    not on the exempt-list emits wrapper-drift-missing-source.

    Position rule: any wrapper that DOES source bash-utils must do so BEFORE
    the first `command -v <engine>` line; otherwise emits
    wrapper-drift-source-position.

    The helper sst3-bash-utils.sh itself is excluded from the audit.
    Increments _state["wrapper_drift_count"] for each finding.
    """
    exempt = _read_exempt_list()
    for wrapper in sorted(SCRIPTS_DIR.glob("sst3-*.sh")):
        name = wrapper.name
        if name == "sst3-bash-utils.sh":
            continue
        try:
            lines = wrapper.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            _emit(
                {
                    "kind": "wrapper-drift-read-error",
                    "wrapper": name,
                    "reason": str(exc),
                }
            )
            _state["wrapper_drift_count"] += 1
            continue
        source_line: int | None = None
        engine_check_line: int | None = None
        for idx, line in enumerate(lines, start=1):
            if source_line is None and _SOURCE_RE.search(line):
                source_line = idx
            if engine_check_line is None and _ENGINE_CHECK_RE.search(line):
                engine_check_line = idx
        if source_line is None:
            if name in exempt:
                continue
            _emit({"kind": "wrapper-drift-missing-source", "wrapper": name})
            _state["wrapper_drift_count"] += 1
            continue
        if engine_check_line is not None and engine_check_line < source_line:
            _emit(
                {
                    "kind": "wrapper-drift-source-position",
                    "wrapper": name,
                    "source_line": source_line,
                    "engine_check_line": engine_check_line,
                }
            )
            _state["wrapper_drift_count"] += 1
    _emit(
        {
            "kind": "wrapper-drift-check",
            "scanned": sum(
                1 for _ in SCRIPTS_DIR.glob("sst3-*.sh") if _.name != "sst3-bash-utils.sh"
            ),
            "exempt": len(exempt),
            "drifted": _state["wrapper_drift_count"],
        }
    )


def _collect_fixtures(only: str | None) -> list[Path]:
    if not FIXTURES_DIR.exists():
        return []
    out = []
    for child in sorted(FIXTURES_DIR.iterdir()):
        if not child.is_dir():
            continue
        if child.name.startswith("_"):
            continue  # _baseline-hashes.json, _known-broken-wrappers, etc.
        if only and child.name != only:
            continue
        if (child / "expected.json").exists():
            out.append(child)
    return out


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="SST3 wrapper-lane self-test driver")
    parser.add_argument(
        "--only",
        help="run a single fixture by name (default: run every fixture)",
    )
    parser.add_argument(
        "--strict-engines",
        action="store_true",
        help="fail (exit 127) when any wrapper exits 127; default is to record + continue",
    )
    parser.add_argument(
        "--wrapper-drift-only",
        action="store_true",
        help="run only the live-wrapper bash-utils drift audit (skip fixtures); used by check-wrapper-bash-utils-drift.sh pre-commit hook (Issue #456)",
    )
    args = parser.parse_args(argv)

    if args.wrapper_drift_only:
        _check_wrapper_bash_utils_drift()
        return 1 if _state["wrapper_drift_count"] > 0 else 0

    fixtures = _collect_fixtures(args.only)
    if not fixtures:
        _emit({"kind": "no-fixtures", "fixtures_dir": str(FIXTURES_DIR)})
        return 0

    engine_missing_seen = False
    for fx in fixtures:
        _state["total"] += 1
        result = _run_fixture(fx)
        if result.get("drift") is None:
            _state["passed"] += 1
            _emit({"kind": "fixture-pass", **result})
        else:
            _state["failed"] += 1
            _state["drift_fixtures"].append(fx.name)
            _emit({"kind": "fixture-drift", **result})
            # exit_drift with rc=127 = engine missing; track separately.
            if result.get("reason", "").startswith("exit=127 "):
                engine_missing_seen = True

    _check_wrapper_bash_utils_drift()

    if _state["failed"] == 0 and _state["wrapper_drift_count"] == 0:
        return 0
    if engine_missing_seen and args.strict_engines:
        return 127
    return 1


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as exc:  # noqa: BLE001 — driver-crash signal
        _emit({"kind": "self-test-crash", "error": str(exc), "type": type(exc).__name__})
        sys.exit(2)
