# Stage 6 result

Stage 6 turns GraderProbe from a local counterfactual runner into a more useful maintainer-facing evaluation integrity layer.

## Added

- Git-aware `audit --changed-only` for PR/release workflows.
- SARIF 2.1.0 export for GitHub code-scanning integrations.
- A bounded optional OpenAI Responses API provider for semantic sensitivity-probe proposals.
- Replay manifests preserve the exact model-generated probe specifications so replay does not silently regenerate them.
- Harbor task-package inspection for the current `task.toml` / `tests/` / `solution/` / `environment/` structure.
- Maintainer CI workflow that audits changed tasks and can publish SARIF on pushes.

## Scope boundary

The Harbor integration is intentionally an inspector/manifest bridge, not a competing Harbor runner. Full execution of arbitrary Harbor/SWE-bench tasks remains outside v0.6 because those tasks may depend on container images and benchmark-specific environments.

The OpenAI provider is opt-in. Deterministic GraderProbe operation remains fully offline. Model proposals are suggestions, not oracles.

## API-credit use case

When enabled in a maintainer workflow, the provider can be used for narrowly scoped semantic probe proposals on benchmark/evaluator changes. The project sends only the selected task contract and bounded source excerpt, and Structured Outputs constrains the response to an allow-listed probe schema. The intended workflow is one bounded request per audited task rather than continuous or user-facing model calls.
