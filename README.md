# GraderProbe

## Project version

`v0.8.0` adds persistent evaluation-contract locks and frozen-candidate causal attribution on top of counterfactual boundary testing.

An evaluator can be wrong even when its tests pass.

GraderProbe tests the evaluator's decision boundary by checking two things:

1. changes that should **not** change the verdict (invariance probes)
2. changes that **should** change the verdict (sensitivity probes)

It is an open-source counterfactual testing framework for validating the
behavioral boundary of AI evaluators and benchmark graders. This repository is
currently a source snapshot (not a claim of PyPI distribution or external
adoption); public maintainer validation remains pending. It is vendor-neutral.
It does not require OpenAI, Anthropic, Google, or any other model provider. The
offline demo makes zero API calls.

This is not a chatbot, not a coding agent, not a leaderboard, and not a generic
benchmark runner.

## Why

A grader can fail in two different ways:

- **False acceptance** — a behaviorally incorrect solution passes
- **False rejection** — a behaviorally correct solution fails because the grader
  checked an implementation detail, a formatting artifact, or some other
  irrelevant property

Traditional testing asks: does the gold solution pass? GraderProbe asks: how
does the evaluator behave around the boundary between correct and incorrect
solutions?

## Install

Python 3.10+.

```bash
pip install -e .
graderprobe --help
```

Runtime dependencies: PyYAML and jsonschema.

## Offline demo

```bash
python -m graderprobe demo
```

A clean clone reproduces the same qualitative findings on the bundled synthetic corpus.
The demo does not call the network and evaluates at most two tasks concurrently to
reduce wall-clock time without multiplying subprocess concurrency inside a task.

## Commands

```text
graderprobe validate <task.yaml>   # structural + baseline safety
graderprobe probe <task.yaml>      # list probes
graderprobe run <task.yaml>        # execute paired counterfactuals
graderprobe audit <path>           # audit one task or a task directory
graderprobe report <profile.json>  # render stored evidence
graderprobe replay <replay.json>   # re-run and compare a recorded outcome
graderprobe demo                   # run the offline corpus
```

Exit codes: `0` ok, `2` warning, `3` threshold failure, `4` baseline invalid, `64` usage.

## Boundary Integrity Profile

The primary output is a decomposable profile, not a marketing score.

```text
BOUNDARY INTEGRITY PROFILE
Task: under-constrained-auth
Baseline: PASS
Invariance probes: 2/2 preserved
Sensitivity probes: 0/2 correctly changed to FAIL
Potential false acceptance: 2
Potential false rejection: 0
Verdict: BOUNDARY_FAIL
```

Every finding includes the pair: original candidate, transformed candidate,
expected relation, actual verdicts. When a task supplies an independent
behavior validator, GraderProbe records behavioral validation evidence and
can distinguish stronger confirmed findings from unvalidated candidates.
Sensitivity false-acceptance candidates can optionally be minimized with a
budgeted hierarchical diff search. The v0.3 engine provides targeted AST-aware
comparison/literal probes, automatic deterministic probe generation, and parallel
probe execution with deterministic result ordering. v0.4 adds optional Docker-backed
execution (read-only container root, dropped capabilities, no-new-privileges,
pids/memory/CPU limits), bounded task-level audit parallelism, scoped execution
memoization for minimization, stronger provenance, and a hardened SWE-bench-style
adapter. v0.5 adds a process-wide execution governor, safe accelerated workspace
copying, output/contract execution digests, baseline output-drift diagnostics, and
local replay bundles. Audit concurrency is globally bounded; higher parallelism is
available by configuration but should be validated on the target host.

If baseline validation fails, GraderProbe reports `BASELINE_INVALID` and does
**not** invent a boundary score.

Passing Boundary Tests does not prove an evaluator is correct.

## What this is not

See [docs/DIFFERENTIATION.md](docs/DIFFERENTIATION.md) and
[docs/PRIOR_ART.md](docs/PRIOR_ART.md). Closely related work includes mutation
testing of evals (muteval), benchmark red-teaming (BenchJack), and benchmark
auditing (BenchGuard). GraderProbe's unit of evidence is a **paired
counterfactual** against the grader: one invariance transform and one
sensitivity transform, with expected relations, isolated execution, and
machine-readable evidence.

## Trust model

Candidate code and evaluators are treated as untrusted. Execution uses a fresh
workspace, a subprocess, a timeout, stripped secrets, and optional POSIX
resource limits. An optional Docker backend adds network namespace control,
capability dropping, no-new-privileges, process limits, memory limits, and CPU
limits. Neither backend is a general-purpose VM security boundary. Read
[SECURITY.md](SECURITY.md).

## Release assurance

Compare the evaluation contract across Git revisions before publishing a benchmark or grader change:

```bash
graderprobe release-audit . --task-root corpus/tasks --base-ref HEAD~1 --auto --sarif-out graderprobe-out/release/release-assurance.sarif
```

The release gate distinguishes `ALLOW`, `WARN`, and `BLOCK` and records a release fingerprint. Optional semantic review can be enabled with `--semantic`; model output is advisory and never the release oracle.

## Frozen-candidate causal attribution

To separate evaluator drift from candidate/model drift, freeze a small positive/negative anchor cohort and compare the exact same candidate artifacts across two Git revisions:

```bash
graderprobe causal-audit . --cohort examples/frozen_cohort.json --base-ref HEAD~1 --head-ref HEAD
```

The candidate is taken from the head Git snapshot, verified byte-for-byte against the base snapshot, then injected into both evaluation snapshots. A PASS/FAIL flip with an unchanged candidate hash is reported as evaluator-drift evidence; candidate drift is explicitly non-comparable and produces `WARN`. `release-audit` can run the same cohort with `--causal-cohort`. See [docs/CAUSAL_ATTRIBUTION.md](docs/CAUSAL_ATTRIBUTION.md).


## Evaluation-contract lockfile

For benchmark maintainers, a repository can commit `graderprobe.lock.json` as an explicit snapshot of its evaluation contract. Create it from a clean Git revision:

```bash
graderprobe lock . --task-root corpus/tasks --out graderprobe.lock.json --anchors 2
```

Verify it on every release or pull request:

```bash
graderprobe verify-lock . --lock graderprobe.lock.json
```

The lock records task/evaluator/probe digests and optional behavioral anchor fingerprints. A change outside the evaluation surface can pass without execution; an evaluation-surface change is escalated to the cross-revision release assurance engine. The lock does not make legitimate changes impossible: after review, regenerate it at the new approved revision.

## Release artifacts and API usage

`release-audit` records exact base/head commits, task digests, comparability/cohort IDs, release fingerprints, and (when semantic escalation is enabled) actual API call/token usage. It can also emit SARIF 2.1.0 for GitHub code scanning. See [docs/API_CREDIT_USAGE_PLAN.md](docs/API_CREDIT_USAGE_PLAN.md) for the bounded maintainer workflow.

## GitHub Actions permissions

The reusable composite action runs deterministic probes by default. Grant only
permissions required by features enabled in the caller workflow: `contents: read`
for checkout, `security-events: write` only when uploading SARIF, and
`pull-requests: write` (or the repository's applicable issue-comment permission)
only when PR comments are enabled. Keep `comment-pr` and `upload-sarif` disabled
unless the repository owner explicitly wants those side effects.

## Maintainer integrations

GraderProbe can audit only the tasks affected by a Git change:

```bash
graderprobe audit corpus/tasks --changed-only --base-ref HEAD~1 --auto --auto-sensitive
```

It can emit SARIF 2.1.0 for GitHub code-scanning integrations:

```bash
graderprobe sarif graderprobe-out/profile.json --out graderprobe-out/results.sarif
```

For a Codex-driven maintainer review, use `scripts/codex_release_review.sh` after generating release evidence. See [docs/CODEX_CLI_INTEGRATION.md](docs/CODEX_CLI_INTEGRATION.md).

For Harbor task packages, use the read-only bridge inspector:

```bash
graderprobe harbor-inspect path/to/task --out harbor-manifest.json
```

The optional `--semantic` flag enables a bounded OpenAI Responses API provider for model-proposed sensitivity probes. Deterministic checks remain the default; model proposals are never the oracle. See [docs/API_USAGE.md](docs/API_USAGE.md).

## License

Apache-2.0. No affiliation with OpenAI or any model vendor is claimed or
implied. Users = 0 at launch; this README does not invent adoption numbers.

## Test tiers

The project keeps a fast deterministic core suite suitable for pull requests and a smaller set of subprocess-heavy integration tests. The fast suite is the default CI gate; the heavy corpus can be run separately on demand so an environmental subprocess bottleneck cannot masquerade as a product regression.

## External maintainer trials

Phase 3 includes upstream trial bundles for two public evaluator cases. These execute the installed upstream packages directly and are designed for authorized maintainer/repository-owner runs:

- `corpus/external-trials/deepeval-3338/` — DeepEval #3338
- `corpus/external-trials/inspect-ai-4721/` — Inspect AI #4721
- `scripts/external_trials/` — one-command trial runners

Trial bundles are evidence tooling, not claims of upstream validation. As of the current release, maintainer execution is still pending.

## Case study: DeepEval #3338 / PR #3339 exact-revision validation

GraderProbe was used to run an independent before/after boundary check on [DeepEval issue #3338](https://github.com/confident-ai/deepeval/issues/3338) against [pull request #3339](https://github.com/confident-ai/deepeval/pull/3339) (*"fix(tool_correctness): pair calls by optimal assignment in unordered mode"*).

- **Base commit (`d65c8da504ca`)**: Score flips between `0.500000` and `0.666667` across input order permutations; GraderProbe reports **`BOUNDARY_FAIL`** (confirmed false rejection on unordered tools). PR #3339 assignment tests fail 3/5.
- **PR #3339 head (`e24bff266a4f`)**: Score invariant at `0.666667` across all 4 permutations; GraderProbe reports **`BOUNDARY_OK`** (0 false rejections, 0 false acceptances). PR #3339 assignment tests pass 5/5.
- **Evidence details**: See [docs/PHASE5_RESULT.md](docs/PHASE5_RESULT.md) and sanitized artifact logs in [artifacts/phase5/sanitized/](artifacts/phase5/sanitized/) with verified hashes in [artifacts/phase5/sanitized/SHA256SUMS.txt](artifacts/phase5/sanitized/SHA256SUMS.txt).
- **Status note**: This was an offline, deterministic local verification with zero model API calls. It does not constitute maintainer endorsement or official upstream execution; the PR remains open upstream.


