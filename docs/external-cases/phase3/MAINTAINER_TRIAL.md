# Phase 3 — maintainer trial protocol

## Objective

Convert the public-source reproductions from Phase 2 into **authorized upstream executions**. The target evidence is not an endorsement. It is a maintainer- or repository-owner-run record containing the upstream revision, observed behavior, and GraderProbe result.

## Why these two targets

### DeepEval #3338

The public issue reports a deterministic, no-LLM order-sensitivity bug in `ToolCorrectnessMetric` when `should_consider_ordering=False` and `should_exact_match=False`: the score changes from `0.5` to `0.6667` when the same `expected_tools` are reversed. The issue is open and currently has no linked PR in the public issue view. The repository's current contributing guide says it uses a fork-and-pull-request workflow and asks contributors to follow existing patterns. citeturn236025search2turn830016search0

Maintainers listed by the repository include `@trevor-cai`, `@A-Vamshi`, `@jeffreyip`, and `@kritinv`. citeturn359953view0

### Inspect AI #4721

The public issue reports a three-grader `model_graded_qa` case where one parse failure leaves an even panel and `mode` breaks the tie by list insertion order. Reordering the same three grader outputs changes the verdict from `C` to `I`. The issue is labeled `maintainer-approved for external PR`, and its author says it was opened at a maintainer's invitation. citeturn236025search0

This makes Inspect AI a particularly useful second target because the project has already signaled openness to external work on that issue.

## Trial procedure

The maintainer should run the upstream issue reproduction first, without GraderProbe. Then run the corresponding GraderProbe task from this repository against the same upstream environment.

### DeepEval

```bash
poetry install
python /path/to/graderprobe/scripts/external_trials/deepeval_3338_upstream.py \
  --upstream-repo /path/to/deepeval \
  --out /tmp/graderprobe-deepeval-3338.json

PYTHONPATH=/path/to/graderprobe/src \
python -m graderprobe run \
  /path/to/graderprobe/corpus/external-trials/deepeval-3338/task.yaml \
  --out /tmp/graderprobe-deepeval-3338-profile \
  --workers 1 --execution-slots 1 --fail-on high
```

The first command records the actual upstream version/revision. The second command should return exit code `3` only when the upstream implementation actually produces the boundary failure described by the task. A resolved upstream implementation should instead return `0` and should be recorded as **fixed/not reproduced**, not as a failure of the trial.

### Inspect AI

```bash
python /path/to/graderprobe/scripts/external_trials/inspect_ai_4721_upstream.py \
  --upstream-repo /path/to/inspect_ai \
  --out /tmp/graderprobe-inspect-4721.json

PYTHONPATH=/path/to/graderprobe/src \
python -m graderprobe run \
  /path/to/graderprobe/corpus/external-trials/inspect-ai-4721/task.yaml \
  --out /tmp/graderprobe-inspect-4721-profile \
  --workers 1 --execution-slots 1 --fail-on high
```

No LLM API key is required for either published reproduction.

## Minimum evidence to return

```text
project
issue URL
upstream repository path
upstream commit
package version
baseline output
transformed output
GraderProbe verdict
GraderProbe version
profile.json hash
maintainer/repository-owner confirmation
```

Do not request a positive endorsement. A statement such as “reproduced”, “not reproduced because fixed”, or “not accepted as an issue” is equally valuable evidence when attached to an immutable revision.

## Evidence status

As of 2026-10-06, this repository contains the trial bundle but **no upstream execution or maintainer confirmation yet**. Public issue evidence is not being relabeled as independent validation.
