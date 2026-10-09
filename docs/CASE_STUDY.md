# Case study (synthetic corpus)

This is an engineering case study on n=16 original tasks. It is not an audit of
a public benchmark. Each example below is produced by actually running the
defective evaluator in isolation.

## Example A — gold passes, a bad implementation also passes

**Task:** `under-constrained-auth`

- Original: `lookup` checks `token == SECRET`, baseline `PASS`
- Counterfactual SEN-01: authorization check removed
- Expected relation: PASS → FAIL
- Actual: PASS → PASS
- Diagnosis: the evaluator only exercises the valid-token path. A candidate
  that returns data for any caller is accepted. False acceptance.

## Example B — gold passes, a valid alternative fails

**Task:** `implementation-specific-sort`

- Original: bubble sort, baseline `PASS`
- Counterfactual INV-01: `return sorted(values)` (still a correct sort)
- Expected relation: PASS → PASS
- Actual: PASS → FAIL
- Diagnosis: the evaluator counts nested `for` loops. Implementation identity
  leaked into the grade. False rejection.

## Example C — a harmless refactor changes the verdict

**Task:** `refactor-rejected`

- Original: single `fizzbuzz` function, baseline `PASS`
- Counterfactual INV-01: extract `token()` helper, behavior unchanged
- Expected relation: PASS → PASS
- Actual: PASS → FAIL
- Diagnosis: the evaluator requires `len(FunctionDef)==1`. Structure, not
  behavior.

## Example D — a one-line semantic defect does not change the verdict

**Task:** `wrong-side-boundary`

- Original: `age >= 18`, baseline `PASS`
- Counterfactual SEN-01: `age > 18` (18 is no longer adult)
- Expected relation: PASS → FAIL
- Actual: PASS → PASS
- Diagnosis: tests use 17 and 19, never 18. The boundary the spec named is
  untested. False acceptance.

See also `over-strict-naming` (identifier `total` required),
`formatting-sensitive` (quote characters), `insecure-accepted` (path jail
untested), and `broken-environment` (`BASELINE_INVALID`, no score).
