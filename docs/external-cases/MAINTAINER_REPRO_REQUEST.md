# Maintainer reproduction request — Phase 2

## Purpose

This is the next evidence step. It asks the upstream repository maintainer to run the public issue reproduction against the real upstream package/revision and, if practical, run GraderProbe on that same working tree.

## DeepEval #3338

Public issue: https://github.com/confident-ai/deepeval/issues/3338

The issue reports a deterministic, no-LLM reproduction on `current main (d65c8da)` where `ToolCorrectnessMetric` in unordered/non-exact mode scores the same tool multiset differently when `expected_tools` is reversed: `0.5` vs `0.6667`.

Requested confirmation:

1. Run the issue's published Python reproduction on the reported revision or the nearest unchanged revision.
2. Confirm the observed score pair.
3. Optionally run the bundled GraderProbe task against the same implementation and confirm that it detects an invariance violation.
4. State whether the result matches the issue's intended semantics or whether upstream behavior has changed.

No API key is required for this reproduction.

## Suggested message

> Hi — I’m working on GraderProbe, an open-source counterfactual testing tool for AI evaluators. I reproduced the behavior documented in DeepEval #3338 as a local, faithful harness: reversing the same unordered `expected_tools` changes the score from 0.6667 to 0.5 and crosses a 0.6 threshold, while an independent order-insensitive oracle says the semantics are unchanged.
>
> I have deliberately not called this an upstream validation. Would you be willing to run the public #3338 reproduction on the actual DeepEval checkout and, if convenient, the small GraderProbe case included in my repository? I only need confirmation of the observed result and the upstream revision used. No API key or production data is required.
>
> The goal is to make the evidence auditable rather than to seek an endorsement.
