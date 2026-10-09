# Phase 3 local smoke results

Date: 2026-10-06

These results use a controlled local stub for the upstream evaluator packages. They validate the GraderProbe trial plumbing and counterfactual/oracle design. They are **not** upstream validation.

| Trial | Expected local result | Observed |
|---|---|---|
| DeepEval #3338 unordered tool matching | BOUNDARY_FAIL / 1 high false rejection | PASS |
| Inspect AI #4721 panel-order case | BOUNDARY_FAIL / 1 high false rejection | PASS (from Phase 3 harness run) |
| DeepEval #3025 sync vs async | BOUNDARY_FAIL / 1 high false rejection | PASS |
| DeepEval #3025 declaration order | BOUNDARY_FAIL / 1 high false rejection | PASS |

The Phase 3 focused regression/validation suite currently reports **9 passed**.

No maintainer endorsement, upstream run, adoption, or selection probability is claimed by this file.
