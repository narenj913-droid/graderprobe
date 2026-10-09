# Methodology

## Relations

Let G be a grader, c a candidate, T an intended behavioral region.

- **Invariance.** If c ∈ T and t is an implementation-preserving transform,
  expect G(t(c)) = G(c).
- **Sensitivity.** If c ∈ T and t removes a required behavior, expect
  G(c) = PASS and G(t(c)) = FAIL.

A violation of invariance is a *false-rejection candidate*. A violation of
sensitivity is a *false-acceptance candidate*. Both are candidates, not proofs:
the transform may have accidentally changed behavior, or the spec may be
ambiguous.

## Baseline safety

Before any probe:

1. The reference candidate is executed N times (N=`baseline_repeats`).
2. Disagreeing verdicts ⇒ `BASELINE_INVALID` (non-determinism).
3. `ERROR`/`TIMEOUT` ⇒ `BASELINE_INVALID` (harness/evaluator failure).
4. Verdict ≠ declared expectation ⇒ `BASELINE_INVALID` (spec/evaluator mismatch).

No boundary score is emitted in those cases.

## Verdicts

| State | Meaning |
|---|---|
| PASS | Evaluator accepted the candidate |
| FAIL | Evaluator rejected the candidate |
| ERROR | Infrastructure or unexpected exit |
| TIMEOUT | Wall clock exceeded |
| INCONCLUSIVE | Evaluator declined to grade |
| BASELINE_INVALID | Do not interpret probes |

ERROR is never silently rewritten as FAIL.

## Metrics

- `invariance_preservation_rate` = held / executed invariance probes
- `sensitivity_detection_rate` = held / executed sensitivity probes
- counts of false acceptance, false rejection, inconclusive
- `probe_execution_error_rate`

Optional `boundary_stability` = mean of the two rates when both exist. It is a
summary of *these probes*, not of the benchmark.

## Honesty

The bundled corpus has n=16. That is too small for a Wilson interval. We
report counts and proportions. Absence of a finding is not correctness.


## Independent behavior validation

A task may provide an optional `behavior_validator`. This is a second executable
contract separate from the evaluator under test. Its `PASS` verdict means the
candidate satisfies the independently encoded behavioral smoke checks; `FAIL`
means those checks are violated. For an invariance probe, both reference and
transformed candidates should validate. For a sensitivity probe, the reference
should validate and the transformed candidate should fail validation.

This does not prove semantic equivalence. It strengthens the evidence behind a
finding and can convert a "possible" defect into a stronger confirmed finding.

## Minimal counterfactuals

For eligible sensitivity false-acceptance candidates, the optional minimizer
uses bounded delta debugging over textual diff hunks. It searches for a smaller
counterfactual that still produces evaluator `PASS` while independently
validating as behaviorally invalid. The result is 1-minimal by diff hunk under
the configured execution budget, not a proof of globally minimal source code.
