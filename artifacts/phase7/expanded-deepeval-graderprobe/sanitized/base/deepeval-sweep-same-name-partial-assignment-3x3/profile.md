# Boundary Integrity Profile — `deepeval-sweep-same-name-partial-assignment-3x3`

**Title:** DeepEval sweep case: same-name-partial-assignment-3x3

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

INV-SAME_NAME_PARTIAL_ASSIGNMENT_3X3: confirmed false rejection (PASS->FAIL) after Reverse expected tool order while preserving the same unordered expected multiset and the called trajectory.

```yaml
probe: INV-SAME_NAME_PARTIAL_ASSIGNMENT_3X3
baseline: PASS
mutant: FAIL
expected_relation: preserve
transformation: replace_file
```

## Pairs

### PAIR-001 (`INV-SAME_NAME_PARTIAL_ASSIGNMENT_3X3`)

- Class: `invariance`
- Transformation: Reverse expected tool order while preserving the same unordered expected multiset and the called trajectory.
- Expected: `preserve`
- Actual: `PASS` → `FAIL`
- Relation held: `False`
- Evidence level: `SMOKE_VALIDATED`
- Behavior: `PASS` → `PASS`
- Minimal counterfactual: `no`
- Original hash: `2f99e1b50de4`
- Transformed hash: `10d8fad03577`

## Limitation

Passing Boundary Tests does not prove an evaluator is correct.
