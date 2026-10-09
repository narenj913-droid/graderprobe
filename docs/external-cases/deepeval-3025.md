# DeepEval #3025 — public-source case

Source: https://github.com/confident-ai/deepeval/issues/3025

The public issue reports that `DAGMetric` can produce different scores for the same reachable verdicts depending on node declaration order and sync versus async execution. The issue states that it reproduces on `main` at `c6d82ce`, with a deterministic fake judge and no API key.

## Trial design

The bundle preserves the issue's two reachable scoring branches and deterministic judge. The baseline uses `DEEP_FIRST=True` and `ASYNC_MODE=True`, which the issue reports as a score of `1.0`. The threshold is `0.75`, making the reported `0.5` counterfactuals explicit PASS/FAIL boundaries for GraderProbe.

Two transformations are recorded:

1. Switch async execution to sync while keeping the declaration order.
2. Reverse the declaration order while keeping async execution.

The independent validator checks that all variants preserve the same three judge/graph configuration dimensions and do not replace the semantics with a different task.

## Evidence boundary

This remains a public-source trial bundle until an authorized maintainer/developer runs `scripts/external_trials/deepeval_3025_upstream.py` from a real DeepEval checkout. The runner records the exact upstream git HEAD and refuses revision checking unless explicitly requested. No upstream validation is claimed by this repository until such a run is captured.
