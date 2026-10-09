# Optional API usage

GraderProbe is local-first. The core engine, deterministic probes, execution, evidence, replay, and reports do not require an API key.

The optional `--semantic` path exists for maintainers who want a small amount of model assistance on semantic probe design. It uses one bounded Responses API call per audited task, asks for at most three proposals, constrains the output with Structured Outputs, and allow-lists the transform kinds that can be executed.

Recommended maintainer policy:

```text
changed evaluator/task files
        ↓
cheap deterministic audit
        ↓
semantic escalation only when useful
        ↓
≤ 3 model proposals
        ↓
local validation + execution
        ↓
SARIF + evidence + replay
```

Do not send secrets. Do not send unrelated repository content. Keep the source excerpt bounded. Treat model output as a proposal, not as ground truth.

The implementation uses the OpenAI Responses API with Structured Outputs when `--semantic` is enabled. Set `OPENAI_API_KEY` and `GRADERPROBE_OPENAI_MODEL` (or pass an explicit `--model`). The repository intentionally does not hard-code a model name; maintainers should choose a model available to their account.

The intended use is core open-source maintainer work: benchmark/evaluator pull-request review, maintainer automation, release validation, and targeted semantic checks.
