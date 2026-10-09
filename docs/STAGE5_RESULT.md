# Stage 5 result

Stage 5 focuses on execution scalability and reproducibility without weakening
integrity claims.

## Implemented

- Process-wide execution governor to cap evaluator subprocess concurrency across
  nested task/probe workers.
- POSIX resource-limit trampoline (`graderprobe._limit_exec`) remains available
  for explicit resource-limited executions without `subprocess` `preexec_fn`.
- Safe workspace copy path that scans for symlinks before any accelerated copy
  path can run; reflink-style copying is used only for sufficiently large files
  to avoid subprocess overhead on small benchmark trees.
- Execution output and evaluator-contract SHA-256 digests on every execution
  result.
- Baseline repeat diagnostics now distinguish verdict nondeterminism from output
  drift. Stable verdict + changing logs is not mislabeled as verdict flakiness.
- Replay bundles that verify the source-tree digest and compare a semantic
  outcome fingerprint after re-running the task.
- `graderprobe replay <bundle>` CLI command.
- Audit/Run CLI controls for global evaluator slots and baseline-repeat override.
- The default local-process path stays fast: hard resource limits are opt-in;
  process-group timeout and concurrency control remain active by default.

## Evidence discipline

A replay match compares the task outcome, metrics, findings, pair verdicts and
 evidence levels. Runtime timestamps, process IDs, and captured output are not
used in the outcome fingerprint, because those are expected to vary.

Replay is local and integrity-oriented. It does not prove evaluator correctness.
A source tree drift is rejected unless the user explicitly allows it.
