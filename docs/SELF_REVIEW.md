# Skeptical maintainer review (v0.8.0)

This is an internal engineering assessment, not an eligibility or acceptance claim.

| Axis | Score | Rationale |
|---|---:|---|
| Problem importance | 9.5 | Evaluator defects can distort model capability conclusions; the project now protects the entire maintainer change lifecycle. |
| Novelty / differentiation | 9.0 | Paired decision-boundary testing is combined with persistent contract locks and frozen-candidate attribution, rather than being only a generic eval runner. |
| Core correctness | 8.5 | Typed verdicts, baseline gates, independent behavior checks, controlled execution, replay and evidence are implemented and regression-tested. |
| Evidence quality | 9.5 | Pair evidence, artifact hashes, replay, release fingerprints, causal cohort IDs, SARIF, and commit-level provenance make findings inspectable. |
| Reproducibility | 9.0 | Offline fixtures, deterministic ordering, replay bundles, frozen cohorts, and locked contracts support independent reproduction. |
| Security | 8.5 | Path/symlink checks, secret stripping, process cleanup, optional Docker controls, and explicit threat-model limitations are documented. |
| Ecosystem integration | 9.5 | GitHub Actions, SARIF, release assurance, contract locks, Harbor inspection, and optional OpenAI semantic escalation target real maintainer workflows. |
| Maintainability | 8.5 | Python package is modular, typed, schema-backed, and deliberately avoids a hosted service or unnecessary frontend. |
| Documentation | 9.5 | Prior art, differentiation, limits, methodology, application notes, API-credit usage, release semantics and causal controls are documented. |
| Ecosystem potential | 9.5 | The repository can function as a change-control layer for benchmark/evaluator repositories, not merely a one-off research script. |

## Hard remaining gaps

- External adoption is still unproven. No users, stars, downloads, partnerships, or endorsements may be claimed before they exist.
- A real public-benchmark case study is the highest-value external evidence still missing.
- Semantic review remains advisory and must never become the deterministic oracle.
- Full-corpus subprocess execution is still environment-sensitive; CI now separates fast deterministic gates from heavy integration work.

## Release decision

Technically strong enough for a public v0.8 release. For an open-source support application, the remaining bottleneck is external evidence rather than adding more code.
