# Stage 3 result

Stage 3 upgrades GraderProbe from a primarily declared-probe prototype toward a
more targeted and scalable counterfactual engine.

## Delivered

- Targeted AST-aware comparison rewrite and comparison-flip transforms.
- Targeted AST-aware numeric-literal mutation.
- Automatic AST-aware invariance and sensitivity probe candidates.
- Parallel probe execution with deterministic output ordering.
- Configurable worker count (`--workers`, default 2).
- Hierarchical budgeted minimization with predicate-result caching.
- More honest minimization metadata when the execution budget is exhausted.
- Demo-level task parallelism capped at two tasks while avoiding nested concurrency.

## Verification

The following focused suites pass:

- Stage 1 hardening tests
- Stage 3 AST tests
- Stage 3 runner tests
- transformation tests
- execution tests

A healthy-control run with independent behavior validation remained `BOUNDARY_OK`.
A deliberately under-constrained authorization grader produced confirmed false-acceptance
findings. A targeted audit using two probe workers preserved deterministic pair ordering.

On the same healthy-control task, local wall-clock measurements were approximately:

- 1 worker: 13.0 s
- 2 workers: 9.0 s

This is a workload/environment measurement, not a benchmark claim.

The full 16-task demo corpus is still subprocess-heavy and was not declared fully
completed in this environment; large-scale execution remains a performance-hardening
target for the next stage.

## Scientific caution

AST-aware means the transformation is targeted structurally. It does not prove semantic
equivalence. Behavioral validation remains the source of stronger evidence. Similarly,
minimization is empirical and budgeted; it is not a proof of global minimality.
