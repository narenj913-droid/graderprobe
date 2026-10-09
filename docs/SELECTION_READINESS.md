# Selection readiness

This document is an internal engineering checklist, not a claim of program eligibility or acceptance.

## What the repository can now demonstrate

- A narrow, concrete problem: evaluator decision-boundary integrity.
- Deterministic paired counterfactual testing.
- Independent behavior validation when available.
- Budgeted minimization of surviving invalid counterfactuals.
- AST-aware deterministic transformations.
- Replayable evidence with provenance and hashes.
- Git-aware release assurance across revisions.
- Frozen-candidate attribution for separating candidate drift from evaluator drift.
- Persistent evaluation-contract lock for maintainer change control.
- SARIF output and GitHub Actions integration.
- Optional bounded model-assisted semantic escalation.
- Vendor-neutral, API-free deterministic core.

## What still cannot be claimed

- Formal proof of benchmark correctness.
- Automatic semantic equivalence for arbitrary programs.
- Security isolation equivalent to a VM.
- Broad external adoption before real users exist.
- OpenAI sponsorship, endorsement, acceptance, or entitlement to a particular credit amount.

## Highest-leverage next evidence

The most valuable next evidence is external: a real maintainer should run the tool on a public benchmark or evaluator repository, report whether the findings are useful, and ideally keep the contract-lock workflow in CI. A single reproducible external case is more valuable than adding another large subsystem.
