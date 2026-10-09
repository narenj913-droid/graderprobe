# Architecture

```text
task.yaml  -->  loader/validator
                    |
                    v
            baseline safety
           (repeat N times)
                    |
          ok? --no--> BASELINE_INVALID + evidence
                    |
                   yes
                    v
         for each declared probe
            copy to temp dir
            apply transform
            run evaluator
            record pair
                    |
                    v
         classify relation held/broken
                    |
                    v
         Boundary Integrity Profile
         + CERTIFICATE.json (hashes)
```

## Layers

1. **Contract** — `task.py`, `schemas/`. Native YAML. No hidden implementation
   assumptions unless declared as constraints.
2. **Isolation** — `isolation.py`. Copy-out workspaces.
3. **Execution** — `execution.py`. Subprocess + timeout + resource limits.
   Interpreters: exit codes and `GRADERPROBE_VERDICT:` markers.
4. **Probes** — `probes/transforms.py`. Deterministic operators. Model-assisted
   probes, if ever used, are labeled `MODEL_GENERATED` and still go through
   structural validation.
5. **Evidence** — `evidence.py`, `findings.py`. The pair is the finding.
6. **Profile** — `profile.py`, `metrics.py`. Rates, not a composite score.
7. **Adapters** — local task format; command evaluator; optional SWE-bench-style
   mapping.
8. **Providers** — `NullProvider` by default. No keys required.

## Why pairs

A single mutant score (classic mutation testing) answers "did the suite catch
this fault?" It does not answer "did the suite reject a still-correct
implementation?" Invariance probes are the other half of the boundary.


## Stage 2 additions

- `TaskSpec.behavior_validator` is an optional independent executable behavior
  contract.
- `runner.py` records original/transformed behavior results alongside grader
  verdicts.
- `Finding` classification uses the independent behavior result to avoid
  blaming the evaluator when a purported invariance probe actually changes
  behavior, and to strengthen sensitivity false-acceptance findings.
- `probes/minimize.py` performs budgeted diff-hunk delta debugging for eligible
  false-acceptance counterfactuals.


## Stage 8 — persistent contract + causal controls

Two maintainer-facing controls sit above the task runner:

1. **Contract lock** records the evaluation surface at an approved Git revision, including task/evaluator/probe digests and optional anchor fingerprints. Verification escalates relevant changes to release assurance.
2. **Frozen-candidate causal audit** injects byte-identical candidate artifacts into base/head repository snapshots and replays the same head probe set against both. A changed outcome fingerprint is reported as evaluator/evaluation-stack drift; candidate byte drift is non-comparable.

These controls are evidence mechanisms, not proofs of benchmark correctness.
