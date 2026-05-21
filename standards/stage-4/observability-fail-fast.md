<!-- stages: 4 -->
# Observability + Fail-Fast — Stage-4 Canonical (#498 AC 4.1)

Two coupled invariants that fire AT WRITE TIME (not after first incident).

## Observability invariants (AP #12)

Every new component MUST land with:
1. **Structured logs** — every external call site emits a structured JSON line. Fields include the operation, the input shape (NOT the full input — PII risk), the result class (success / known-failure / unknown-failure), and the wall-clock duration.
2. **Metrics** — counters for invocation count + error class; gauges for queue depth / cache size; histograms for duration percentiles. Wired into the runtime metrics export (Prometheus / OpenTelemetry / Postgres-backed counters — per repo).
3. **Audit trail** — every state mutation (DB write / file write / external API call) writes one append-only row to an audit log. The audit log is separate from operational logs; it survives log rotation.

## Fail-Fast invariants

- Error loudly. NO silent fallbacks. NO `try: ... except Exception: pass`.
- Every `except` clause names the exception class. Bare `except:` is forbidden.
- On error: log structured, emit metric, re-raise unless the function's contract is to swallow (and then the swallow is documented inline with WHY).
- Retry logic is explicit (jittered backoff, max attempts) and the final failure surface is loud.

## Why coupled

Observability without fail-fast: failures are silent, observability data shows everything-green even mid-incident. Fail-fast without observability: failures are loud but the operator has no context (which call site, which input class). Both invariants together = loud failure with diagnosable context.

## Cross-references

- `../../standards/STANDARDS.md` "Fail Fast, No Silent Fallbacks" + "Observability — No Code Without Logs, Metrics, and Audit Trails".
- `../../standards/ANTI-PATTERNS.md` AP #12 (No Observability) + AP #7 (Silent Fallbacks).
- `../../standards/stage-4/contract-verification.md` — the write-time invariants this section supplements.
