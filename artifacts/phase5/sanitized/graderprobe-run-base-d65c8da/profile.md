# Boundary Integrity Profile — `deepeval-3338-upstream-trial`

**Title:** DeepEval

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

INV-UPSTREAM-EXPECTED-ORDER-01: confirmed false rejection (PASS->FAIL) after Reverse expected_tools while preserving the same unordered multiset.

```yaml
probe: INV-UPSTREAM-EXPECTED-ORDER-01
baseline: PASS
mutant: FAIL
expected_relation: preserve
transformation: replace_file
```

## Pairs

### PAIR-001 (`INV-UPSTREAM-EXPECTED-ORDER-01`)

- Class: `invariance`
- Transformation: Reverse expected_tools while preserving the same unordered multiset.
- Expected: `preserve`
- Actual: `PASS` → `FAIL`
- Relation held: `False`
- Evidence level: `SMOKE_VALIDATED`
- Behavior: `PASS` → `PASS`
- Minimal counterfactual: `no`
- Original hash: `c2e006c0dd33`
- Transformed hash: `81dbdb5e09a8`

## Limitation

Passing Boundary Tests does not prove an evaluator is correct.
