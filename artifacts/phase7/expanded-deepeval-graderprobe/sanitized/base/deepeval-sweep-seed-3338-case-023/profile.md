# Boundary Integrity Profile — `deepeval-sweep-seed-3338-case-023`

**Title:** DeepEval sweep case: seed-3338-case-023

**Profile verdict:** `BOUNDARY_FAIL`

## Baseline

- Result: `PASS`
- Accepted: `True`
- Reason: baseline accepted

## Metrics

| Metric | Value |
|---|---|
| Invariance preserved | 0/1 |
| Sensitivity detected | 0/0 |
| False acceptance count | 0 |
| False rejection count | 1 |
| Inconclusive count | 0 |
| Probe execution error rate | 0.000 |

_Rates are proportions on this task's executed probes. They are not a general benchmark quality score._

## Findings

### PAIR-001 — false_rejection (high)

INV-SEED_3338_CASE_023: confirmed false rejection (PASS->FAIL) after Reverse expected tool order while preserving the same unordered expected multiset and the called trajectory.

```yaml
probe: INV-SEED_3338_CASE_023
baseline: PASS
mutant: FAIL
expected_relation: preserve
transformation: replace_file
```

## Pairs

### PAIR-001 (`INV-SEED_3338_CASE_023`)

- Class: `invariance`
- Transformation: Reverse expected tool order while preserving the same unordered expected multiset and the called trajectory.
- Expected: `preserve`
- Actual: `PASS` → `FAIL`
- Relation held: `False`
- Evidence level: `SMOKE_VALIDATED`
- Behavior: `PASS` → `PASS`
- Minimal counterfactual: `no`
- Original hash: `b66d3c9687d2`
- Transformed hash: `86c87e25f09d`

## Limitation

Passing Boundary Tests does not prove an evaluator is correct.
