# Stage 4 result

Stage 4 hardens execution and makes multi-task auditing more practical without
changing the central counterfactual methodology.

## Implemented

- Optional Docker execution backend with `--network`, capability dropping,
  `no-new-privileges`, pids, memory, and CPU limits.
- Explicit refusal when Docker is requested but unavailable.
- Scoped in-process execution memoization for expensive minimization loops; the
  normal probe path remains uncached by default to avoid hiding evaluator flakiness.
- Audit-level task parallelism with deterministic report ordering.
- Artifact hashing now skips symlinks rather than dereferencing them.
- SWE-bench-style adapter no longer synthesizes `true` as a fallback evaluator.
- Runtime tests for cache, sandbox schema, Docker command hardening, missing Docker,
  and task-level parallel audit.

## Deliberate non-goals

- No hosted service.
- No persistent cross-run result cache yet.
- No claim that Docker is a VM-equivalent sandbox.
- No benchmark-specific runner implementation hidden behind the adapter interface.

## Verification

The Stage 4-specific test module passes completely. Core Stage 1–3 tests are run
in focused groups; the full corpus remains subprocess-heavy and is intentionally
not presented as fully verified when the execution environment times out.
