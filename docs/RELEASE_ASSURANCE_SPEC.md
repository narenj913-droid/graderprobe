# Release Assurance Specification (v0.8.0)

## Purpose

Release assurance answers a narrower question than benchmark quality:

> Did a change to a benchmark/evaluator repository change what the evaluator accepts, reject, or compare?

The gate compares the same counterfactual probe identities across base and head revisions whenever possible.

## Evidence contract

A comparable task records:

- base and head Git commit IDs
- base/head task tree digests
- base/head cohort IDs
- changed artifact categories
- common probe count and probe-set delta
- baseline status
- determinism status when two or more baseline repeats are available
- invariance and sensitivity execution status
- new false-acceptance/rejection evidence
- release fingerprint

## Required checks

The required checks are derived from the changed artifact category:

| Change | Minimum checks |
|---|---|
| evaluator | baseline, invariance, sensitivity, determinism |
| environment | baseline, determinism |
| task contract | baseline, invariance, sensitivity |
| reference solution | baseline, sensitivity |
| probe definition | invariance, sensitivity |
| other | baseline |

A check gap is reported explicitly and normally produces `WARN` rather than a silent pass.

## Decision semantics

- `ALLOW`: no release-blocking regression detected by the executed evidence.
- `WARN`: additional maintainer review is required or cross-revision evidence is incomplete.
- `BLOCK`: a material regression, invalid baseline, or other release-blocking defect was detected.
- `NO_CHANGES`: no task-relevant changes were identified.

These are release workflow decisions, not claims of formal benchmark correctness.

## Cohort comparability

A cohort ID is a deterministic digest of the task tree, evaluator configuration, and behavior/provenance configuration. It is an identity aid for reproducibility and result comparison; it is not a standard certification authority.

## Semantic escalation

Optional model review is advisory. Deterministic local execution remains authoritative. Model requests are bounded, structured, and recorded with API usage when an OpenAI provider is used.

## Global change fan-out

A high-risk evaluator/environment/task-contract/reference/probe change outside individual task directories is treated as potentially shared. GraderProbe conservatively audits the current task population rather than silently returning `NO_CHANGES`. A user-supplied `--max-tasks` may cap that fan-out; when capped, the release decision is at least `WARN` because coverage is incomplete.

## Semantic review failure

When semantic review is explicitly requested and a requested model review fails, an otherwise clean release is downgraded to `WARN`. Deterministic evidence remains authoritative; semantic review failure is never converted into a benchmark finding.


## Contract lock

The v0.8 contract lock is a persistent source-control artifact containing the approved commit, task inventory, evaluator contracts, probe-set digests, and optional anchor fingerprints. Verification escalates changes on the evaluation surface to release assurance and records a deterministic lock fingerprint.

## Frozen-candidate attribution

A frozen cohort controls candidate drift by injecting byte-identical candidate artifacts into the base and head snapshots before replaying the same probe set. A changed outcome fingerprint is reported as evaluator-stack drift; a candidate hash mismatch is explicitly non-comparable.
