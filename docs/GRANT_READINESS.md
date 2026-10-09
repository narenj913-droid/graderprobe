# Codex Open Source credit readiness

This is a factual planning document, not a promise of funding or a request for artificial API usage. OpenAI's Codex Open Source Fund currently describes a $1M initiative with grants up to $25,000 in API credits; the separate Codex for Open Source program describes API credits for coding, maintainer automation, release workflows, and core OSS work. Selection and grant size are discretionary.

## Strongest legitimate credit use

1. Changed-evaluator semantic escalation: deterministic checks run first; ambiguous/high-risk pull requests may receive a bounded semantic review and a small number of structured counterfactual proposals.
2. Maintainer release automation: PR/release workflows can call the semantic layer only when the evaluation contract changes, then attach SARIF and evidence artifacts.
3. Benchmark quality investigations: a maintainer can run a larger set of semantic probes on a targeted subset when deterministic analysis cannot resolve natural-language requirement/evaluator alignment.
4. Codex-driven maintenance review: the same evidence bundle can be supplied to a Codex maintainer workflow for triage or documentation, without making the model the release oracle.

## Guardrails

- Deterministic mode remains fully offline.
- Semantic escalation is bounded and change-triggered.
- Model-generated probes are proposals, not ground truth.
- Every request records request ID and returned token usage when available.
- Replay does not make another API call.
- Do not create artificial workloads just to consume credits.

## What makes the case stronger

The repository already contains the implementation path for the stated use of credits. The remaining evidence should come from real maintenance work and external benchmark/evaluator repositories, not from fabricated adoption or deliberately inflated API consumption.
