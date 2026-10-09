# Frozen-candidate causal attribution

Evaluation results can change because the candidate/model changed, because the evaluator changed, or because the execution environment changed. A raw score delta cannot distinguish these causes.

GraderProbe provides a conservative control: a small frozen cohort of candidate artifacts is copied byte-for-byte into both the base and head Git snapshots. The head probe set is replayed against both snapshots. The system records candidate hashes and outcome fingerprints.

## Interpretation

- `STABLE`: identical candidate bytes and matching outcome fingerprints.
- `EVALUATOR_DRIFT`: identical candidate bytes but different outcome fingerprints.
- `CANDIDATE_DRIFT`: candidate bytes differ; the comparison is non-comparable and warns rather than assigning causality.
- `TASK_MISSING`: an anchor cannot be evaluated in one snapshot.

This is causal evidence under the recorded controls, not a proof that every changed outcome has a single root cause.

## Cohort format

```json
{
  "schema": "graderprobe.frozen_cohort.v1",
  "anchors": [
    {
      "task": "corpus/tasks/example/task.yaml",
      "candidate": "corpus/tasks/example/solution.py",
      "label": "positive-anchor"
    }
  ]
}
```

The cohort should be small and intentionally representative. It is not a substitute for a full benchmark run.
