# v0.1 audit — Stage 1 hardening baseline

This audit records the state observed before the first hardening pass. It is
intentionally skeptical: passing unit tests are not treated as proof of
correctness.

## Observed strengths

- The core has distinct `PASS`, `FAIL`, `ERROR`, `TIMEOUT`, `INCONCLUSIVE`, and
  `BASELINE_INVALID` states.
- Baseline invalidity gates the boundary analysis.
- Findings retain paired original/transformed evidence.
- The demo is local and does not require a model provider.
- Prior-art documentation explicitly avoids claims of priority.

## Findings before Stage 1

### Critical correctness

1. `known_invalid` is intentionally an observation, not a baseline gate. A
   defective grader accepting a known-invalid candidate is exactly the kind of
   false-acceptance signal this project is designed to surface. The baseline must
   therefore validate the reference/evaluator, then expose the control outcome to
   the probe/profile layer.
2. `RunConfig.inherit_secrets` was not propagated into evaluator execution.
3. Verdict-marker detection used substring matching, so arbitrary output could
   accidentally contain a marker.
4. Timeout handling used `subprocess.run(..., timeout=...)` while creating a
   process session, but did not explicitly terminate the complete process group.

### Path and filesystem safety

5. Workspace containment used string-prefix checks.
6. Task-tree copying followed symlinks instead of rejecting them.
7. Task documents did not enforce the repository's JSON schemas at load time.

### Environment/reproducibility

8. The schema files described constraints that were only partially duplicated
   in Python validation.
9. The package's schema files were not included as package data, making schema
   validation unsuitable for a normally installed wheel.

## Stage 1 acceptance target

The first hardening pass must establish:

- canonical path containment
- symlink rejection during task copy
- explicit secret inheritance behavior
- process-group cleanup on POSIX timeouts
- exact verdict protocol semantics
- runtime JSON-schema validation of task documents
- enforcement of declared known-invalid verdicts
- regression tests for each of the above

This stage deliberately does **not** attempt to solve the harder research
problem of automatically proving semantic equivalence. That belongs to the
next stage.

## Stage 1 result

Implemented in v0.1.1. Focused hardening tests pass (10/10). Representative
smoke tests show the healthy control remains `BOUNDARY_OK`, the
under-constrained evaluator produces real `false_acceptance` findings, and the
broken-environment control produces `BASELINE_INVALID`.

The full corpus remains intentionally subprocess-heavy; performance and probe
scalability are deferred to the next stage rather than weakening isolation or
correctness to make the current demo faster.
