# Phase 2 result — public external cases

## Completed

Phase 2 established two reproducible public-source case studies from real evaluator frameworks.

### Primary: DeepEval #3338

- Current public issue observed as **Open**.
- Issue reports `current main (d65c8da)`.
- Deterministic path; no LLM call.
- Reported order-sensitive scores: `0.5` and `0.6667` for the same unordered tool multiset.
- GraderProbe reproduced the boundary as `PASS -> FAIL` across a pure reordering transformation.
- Independent semantic validator passed for both candidates.
- Result: `BOUNDARY_FAIL`, one **HIGH confirmed false rejection**.

### Corroborating: Inspect AI #4721

- Public issue describes an order-dependent outcome after a grader parse failure shrinks a panel.
- The issue's own reproduction shows the same three grader outputs changing from `C` to `I` when only their list order changes.
- GraderProbe reproduced that boundary locally and classified it as a **HIGH confirmed false rejection**.

## What this proves

1. GraderProbe's invariance model maps cleanly onto real, publicly documented evaluator failure modes.
2. It can turn a human-described evaluator bug into a machine-readable paired counterfactual with hashes, execution records, and an independent behavior validator.
3. The strongest current case is DeepEval #3338 because the issue is reported against current main and explicitly says the path is deterministic and requires no LLM call.

## What this does not prove

- No upstream repository was cloned or executed in this environment because outbound GitHub access is unavailable here.
- No maintainer has yet validated the GraderProbe reproduction.
- No external CI workflow has yet retained a GraderProbe run.
- No adoption, endorsement, popularity, or selection probability claim is made.

## Next evidence gate

Obtain repository-owner permission for an upstream run of the DeepEval #3338 reproducer, then rerun GraderProbe against the actual package/revision and capture the maintainer's verdict as an immutable evidence record.
