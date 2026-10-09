# API credit usage plan

GraderProbe is designed to use OpenAI API credits only for core open-source maintainer workflows. Deterministic checks remain the default and model calls are bounded and recorded.

## Proposed workflow

1. **Changed-task triage** — identify evaluator/task/environment changes from a Git diff.
2. **Deterministic release assurance** — baseline, invariance, sensitivity, determinism and replay checks run locally first.
3. **Semantic escalation** — for high-risk or ambiguous changes, the optional OpenAI provider performs a bounded semantic review and may propose a small number of additional probes.
4. **Evidence-first execution** — proposed probes are validated and executed locally; the model is never the release oracle.
5. **Release artifacts** — SARIF, JSON evidence, release fingerprint, and API usage are retained with the CI run.

## Why credits are useful

The semantic layer addresses cases where deterministic transformations cannot reliably determine whether a natural-language requirement and its evaluator agree. Because escalation is changed-task-only and capped, credits are spent on ambiguous maintainer decisions rather than on routine scoring.

## Guardrails

- No user-facing chatbot.
- No background or open-ended model loops.
- Maximum three model probe proposals per task.
- Structured Outputs are required.
- Model outputs are advisory.
- Every API call records operation, request ID when available, and token usage returned by the API.
- Replay never calls the API again.

## Application-ready description

The project uses OpenAI models as a bounded semantic escalation layer inside a core maintainer workflow: when a pull request changes an evaluator or benchmark contract, GraderProbe first runs deterministic release assurance and only escalates ambiguous/high-value cases for structured semantic review and additional counterfactual proposals. The resulting evidence is executed locally and attached to the release/PR workflow.

This describes an intended use of credits; actual usage should be reported from repository evidence rather than projected numbers.

## Codex compatibility

The repository also fits Codex-driven maintainer workflows: the release assurance command is deterministic and can sit behind a Codex code-review or CI task. OpenAI's current Codex documentation supports non-interactive `codex exec` workflows with structured output, so future integrations can feed the same release evidence into a Codex-driven review loop without making Codex the deterministic oracle.
