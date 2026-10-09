# Prior-art review — Stage 7

This review is maintained to keep GraderProbe differentiated from adjacent evaluation, red-team, and benchmark-quality tooling.

## OpenAI evaluation / benchmark-quality work

OpenAI has publicly documented benchmark-quality problems in SWE-bench Pro and maintains evaluation infrastructure such as Evals. GraderProbe does not try to replace those systems; it targets a narrower maintainer control: detecting evaluator decision-boundary regressions across code changes.

## Promptfoo

Promptfoo is a broad open-source evaluation and red-teaming platform and was announced for acquisition by OpenAI in March 2026. GraderProbe should not compete by becoming another general-purpose LLM evaluation suite. Its defensible scope is release/change assurance for benchmark graders using explicit counterfactual relations, cross-revision replay, comparability, and evidence.

## BenchJack / benchmark hackability

Benchmark hackability scanners focus on whether benchmarks can be exploited or gamed. GraderProbe includes false-acceptance probes but also treats false rejection and release drift as first-class concerns.

## muteval / mutation testing

Mutation testing of evaluation suites is close to GraderProbe's sensitivity side. GraderProbe combines sensitivity with invariance, independent behavior validation, bounded minimization, replay, and version-to-version release assurance.

## Harbor

Harbor is an agent-evaluation task/runtime ecosystem. GraderProbe provides a read-only task inspector and a bridge for compatible task layouts; it does not claim to replace the Harbor runner.

## Defensible contribution

The strongest defensible contribution is not a new testing theory. It is an operational maintenance layer that turns counterfactual decision-boundary checks into **release evidence**: the same probe cohort is replayed across revisions, shared high-risk changes are conservatively fanned out to the benchmark population, changes are classified, evidence is hashed, and the maintainer receives an ALLOW/WARN/BLOCK signal with machine-readable artifacts.
