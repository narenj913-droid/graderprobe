# v0.2 self-review

## Scores

| Area | Score / 10 |
|---|---:|
| Problem importance | 9 |
| Novelty / differentiation | 7 |
| Core correctness | 8 |
| Evidence quality | 8 |
| Reproducibility | 8 |
| Security | 7 |
| Automation | 7 |
| Interoperability | 8 |
| Maintainability | 8 |
| Ecosystem relevance | 8 |

## What is genuinely strong

The project has a clear unit of evidence: an original candidate plus a controlled counterfactual plus an expected relation plus the observed evaluator verdict. Stage 2 strengthens that evidence when an independent behavior validator confirms the transformation's intended behavioral effect.

## What is not novel by itself

Mutation testing, metamorphic relations, subprocess isolation, benchmark auditing, and evidence manifests all have prior art. The project does not claim ownership of those concepts.

## Main weaknesses

1. The current automatic transformations are conservative heuristics, not general semantic transformations.
2. The minimalizer provides local line-edit minimality under a bounded budget, not a globally minimal source transformation.
3. The framework still relies on task maintainers to supply an independent behavior contract for stronger evidence.
4. Benchmark-specific adapters remain intentionally shallow in v0.2.

## Why it can still matter with zero users

A maintainer can run the offline demo, inspect the counterfactual pair, and reproduce the finding without credentials. The project addresses a concrete evaluation-quality problem and integrates naturally with CI.

## Most important v0.3 direction

Add a stronger benchmark adapter and richer AST-aware counterfactual generation while preserving the deterministic core and evidence-first reporting.
