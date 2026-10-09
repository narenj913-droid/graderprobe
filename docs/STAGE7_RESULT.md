# Stage 7 result

Stage 7 moves GraderProbe from task-level counterfactual testing toward change-aware evaluation maintenance infrastructure.

## Core additions

- `release-audit` compares the same counterfactual probe set across base/head Git revisions.
- Changed files are classified as evaluator, task contract, reference solution, environment, probe definition, workflow, or other.
- Shared high-risk changes outside task directories trigger conservative global task fan-out instead of being silently skipped.
- Base/head commit IDs, task digests, cohort IDs, probe-set delta, executed/required check sets, and release fingerprint are recorded.
- New false-acceptance/false-rejection evidence can block a release.
- Newly added tasks are head-audited instead of silently skipped when no base task exists.
- Deleted task paths are surfaced because removing benchmark tasks changes release comparability.
- Release SARIF 2.1.0 is emitted for GitHub Code Scanning.
- Optional OpenAI semantic review is bounded, structured, advisory, and records request IDs plus actual API token usage when returned by the API. Requested semantic-review failures downgrade an otherwise clean release to `WARN`.
- Release JSON is schema-validated.
- GitHub Actions retain the assurance bundle and can publish SARIF.
- A Codex CLI read-only review script can consume the same release evidence.

## Why this matters

The maintainer question is narrower than general model evaluation: **did a change to the benchmark/evaluator alter what the evaluator accepts, and do we have evidence to support releasing that change?** The project deliberately avoids claiming formal benchmark correctness.

## Honest status

The repository still has zero external users at this stage. No adoption, endorsement, partnership, or acceptance claims are made.

## Execution reliability hardening

A release-test hang exposed an execution-layer issue: pipe-backed stdout/stderr capture could leave the parent waiting on evaluator communication. The local process backend now captures stdout/stderr into temporary files and uses `Popen.wait(timeout=...)`, with process-group termination on timeout. This keeps the evaluator deadline independent of pipe-drain behavior.
