# External case: DeepEval #3338

Status: **public-source reproduction; maintainer validation pending**

## Source

- Project: DeepEval
- Repository: https://github.com/confident-ai/deepeval
- Issue: https://github.com/confident-ai/deepeval/issues/3338
- Issue state observed: Open
- Reported source revision: `d65c8da`
- Reported path: `ToolCorrectnessMetric` unordered, non-exact mode
- Reported execution mode: deterministic; no LLM call

The public issue states that the unordered mode is documented as order-insensitive, but its greedy one-to-one pairing makes the score depend on the order of `expected_tools` when partial input-parameter scores are involved.

## Public reproduction reproduced locally

The issue reports this exact score pair:

- original expected order: `0.5`
- reversed expected order: `0.6667`

The local faithful reproduction model uses the two expected tool calls, the two called tool calls, the input-parameter similarity values reported in the issue, and a threshold of `0.6` so the documented score instability becomes a verdict instability. This synthetic reproduction verifies that GraderProbe can detect the reported failure mode; by itself it is not proof that an installed upstream wheel or checkout reproduced it.

GraderProbe observed:

```text
Baseline: PASS
Probe:    FAIL
Expected relation: preserve
Finding: confirmed false rejection (PASS->FAIL)
Severity: HIGH
```

The independent behavior validator treats the expected tool list as an unordered multiset and computes an optimal one-to-one assignment. It accepts both baseline and transformed candidates, so the verdict flip is attributable to the reproduced evaluator logic rather than a semantic change in the task data.

## Reproduction command

```bash
PYTHONPATH=src python -m graderprobe run \
  corpus/external-cases/deepeval-3338/task.yaml \
  --out /tmp/deepeval-3338-profile \
  --workers 1 \
  --execution-slots 1 \
  --fail-on high
```

Expected GraderProbe exit code: `3` (`BOUNDARY_FAIL`).

## Evidence files

- Task contract: `corpus/external-cases/deepeval-3338/task.yaml`
- Baseline candidate: `corpus/external-cases/deepeval-3338/solution.py`
- Counterfactual: `corpus/external-cases/deepeval-3338/alternatives/reversed_expected.py`
- Reproduced evaluator: `corpus/external-cases/deepeval-3338/evaluator.py`
- Independent semantic validator: `corpus/external-cases/deepeval-3338/behavior_validator.py`
- Historical local profile snapshot: `artifacts/phase2/deepeval-3338-profile.json` (the upstream-trial artifacts separately record that the dependency was unavailable in that earlier environment).

## Claim boundary

This artifact establishes that GraderProbe can reproduce and detect the behavior described in a current public DeepEval issue. It does **not** establish that the current upstream package produces the result in our environment, because the package itself was not cloned or executed here. Upstream execution and maintainer confirmation are the next evidence step.
