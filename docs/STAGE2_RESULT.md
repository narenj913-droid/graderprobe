# Stage 2 result

Implemented:
- independent behavior validator contract
- validation-aware finding classification
- deterministic auto invariance and heuristic auto sensitivity probes
- evidence levels
- budgeted diff-hunk minimization
- selected corpus tasks upgraded with independent validators

The core remains offline and provider-neutral. Model-assisted probing remains optional.


## Verified examples

- `healthy-control`: independent behavior validation strengthened 7 invariance and 4 sensitivity checks; the profile remains `BOUNDARY_OK`.
- `under-constrained-auth`: two sensitivity probes were independently validated as behaviorally invalid while the evaluator returned `PASS`; both are reported as confirmed false-acceptance candidates.
- `over-strict-naming`: a behavior-preserving implementation rewrite remains valid under the independent validator while the evaluator rejects it, strengthening the false-rejection diagnosis.

The minimizer uses bounded execution and reports the exact budget and minimality claim. It does not claim global source-level minimality.

By default, behavior validation is lazy to avoid doubling subprocess cost on clean probes; use the all-validation mode for exhaustive evidence coverage.
