# External case: Inspect AI #4721

Status: **historical public-source reproduction; maintainer validation pending**

## Source

- Project: Inspect AI
- Repository: https://github.com/UKGovernmentBEIS/inspect_ai
- Issue: https://github.com/UKGovernmentBEIS/inspect_ai/issues/4721
- Reported source revision in the issue: `1ea01a9`
- Code context referenced by the issue: `7973622`
- Reported execution mode: local `mockllm`, no network, no real model

The public issue describes `model_graded_qa(model=[...])` with one grader whose output cannot be parsed. The remaining two votes can tie, and `mode` then resolves the tie using model-list order. The issue supplies an end-to-end reproduction where the same three grader completions produce `C` in one order and `I` in the reverse order.

## GraderProbe reproduction

The faithful local reproduction encodes the public issue's three completions and treats reordering the same panel as an invariance transformation.

GraderProbe observed:

```text
Baseline: PASS
Probe:    FAIL
Expected relation: preserve
Finding: confirmed false rejection (PASS->FAIL)
Severity: HIGH
```

The independent validator ignores list order and confirms that the same grader multiset is preserved.

## Claim boundary

This is evidence that the public issue describes a boundary property GraderProbe can express and detect. It is not evidence that the historical upstream revision was executed by us, nor is it evidence of maintainer endorsement.
