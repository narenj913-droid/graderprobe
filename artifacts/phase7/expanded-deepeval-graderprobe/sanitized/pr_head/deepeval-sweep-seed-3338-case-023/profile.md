# Boundary Integrity Profile — `deepeval-sweep-seed-3338-case-023`

**Title:** DeepEval sweep case: seed-3338-case-023

**Profile verdict:** `BOUNDARY_OK`

## Baseline

- Result: `PASS`
- Accepted: `True`
- Reason: baseline accepted

## Metrics

| Metric | Value |
|---|---|
| Invariance preserved | 1/1 |
| Sensitivity detected | 0/0 |
| False acceptance count | 0 |
| False rejection count | 0 |
| Inconclusive count | 0 |
| Probe execution error rate | 0.000 |

_Rates are proportions on this task's executed probes. They are not a general benchmark quality score._

## Findings

No defect candidates. This is not a proof of evaluator correctness.

## Pairs

### PAIR-001 (`INV-SEED_3338_CASE_023`)

- Class: `invariance`
- Transformation: Reverse expected tool order while preserving the same unordered expected multiset and the called trajectory.
- Expected: `preserve`
- Actual: `PASS` → `PASS`
- Relation held: `True`
- Evidence level: `UNVALIDATED`
- Behavior: `PASS` → `UNVALIDATED`
- Minimal counterfactual: `no`
- Original hash: `b66d3c9687d2`
- Transformed hash: `86c87e25f09d`

## Limitation

Passing Boundary Tests does not prove an evaluator is correct.
