# Open-source application notes

## Project value

GraderProbe is an open-source counterfactual testing layer for AI evaluators and benchmark graders. Its central unit of evidence is a paired counterfactual:

- an intended behavior-preserving transformation
- a minimal requirement-violating transformation

The framework executes the evaluator in isolation and records the observed relation, evidence level, provenance, and replay information.

## Maintainer workflow

The project now supports Git-aware changed-task auditing and SARIF output so benchmark/evaluator changes can become CI findings. This makes the project directly useful for pull-request and release maintenance rather than only local experiments.

## Optional API workflow

The deterministic engine is the default. An optional OpenAI Responses API provider can propose up to three narrowly scoped sensitivity probes per task. The provider uses Structured Outputs and an allow-list of transform kinds. Model-generated probes are preserved in replay manifests and remain proposals rather than sources of truth.

A legitimate maintainer workflow is:

```text
PR changes evaluator/task
        ↓
changed-only deterministic audit
        ↓
semantic escalation only for ambiguous/high-value cases
        ↓
bounded model probe proposals
        ↓
execute proposals
        ↓
SARIF + evidence artifact
```

This is intended for core open-source maintenance work. It is not a user-facing chatbot or general-purpose model wrapper.

No adoption, partnership, endorsement, download, or usage figures should be claimed unless independently established.


## Current program facts to keep separate from project claims

The current Codex Open Source Fund describes a $1 million initiative and says projects can receive grants of up to $25,000 in API credits. Selection remains discretionary. The separate Codex for Open Source program describes API credits for coding, maintainer automation, release workflows, and core OSS work.

The repository should never claim that this project is entitled to the maximum grant. The strongest case is to show a concrete, bounded plan for using credits in core maintainer workflows and to provide evidence that the workflow is implemented.


## Release assurance

The maintainer workflow can run a change-aware release audit that replays the same counterfactual probes across Git revisions, records exact commit IDs, detects new false acceptance/rejection evidence, and produces a release fingerprint. When semantic escalation is enabled, actual API call/token usage is recorded in the evidence bundle.

## 500-character application drafts

### Why does this repository qualify?

GraderProbe is open-source evaluation-maintenance infrastructure for a concrete failure mode: graders can accept incorrect solutions or reject valid alternatives. It adds deterministic counterfactual boundary tests, cross-revision release assurance, frozen-candidate drift attribution, replayable evidence, SARIF/CI integration, and a persistent evaluation-contract lock. The deterministic core is vendor-neutral and runs without an API key.

### How would API credits be used?

API credits would be used only for bounded semantic escalation when a maintainer PR changes an evaluator or benchmark contract and deterministic checks cannot resolve a semantic question. An OpenAI model may propose a small number of structured probes or review the change; every proposal is locally validated and executed, and the model is never the release oracle. Request IDs and returned token usage are recorded.
