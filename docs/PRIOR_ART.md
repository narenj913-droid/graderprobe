# Prior art

Researched 2026-10-04. This is a map of related systems, not a claim of
priority. GraderProbe is not "the first" anything.

| System | What it does | What it measures | What it does not measure | Overlap | Our differentiation |
|---|---|---|---|---|---|
| OpenAI Evals | Registry + runner for model evals | Model outputs vs registered checks | Whether the check itself is the right region | Runner only | We test the grader, not the model |
| OpenAI SWE-bench Verified / Pro audits | Human+pipeline audit of coding tasks | Broken tests, underspec, contamination | Systematic paired counterfactuals you can re-run locally | Same *problem* (over-strict tests) | We ship an executable method, not an audit of one benchmark |
| SWE-bench / SWE-bench Pro | Agent coding benchmark | Patch pass rate on hidden tests | Evaluator boundary integrity as a first-class output | Consumers of graders | Thin optional adapter only; not a SWE-bench clone |
| OpenAI Symphony | Spec for orchestrating coding agents from an issue tracker | Work throughput | Grader validity | None material | Different layer (orchestration) |
| BenchGuard | LLM auditors of benchmark artifacts | Spec bugs, unsolvable tasks | Paired invariance/sensitivity of a live grader | Audit | We execute the grader on counterfactuals; they audit artifacts with an LLM |
| BenchJack | Red-team agents to reward-hack benchmarks | Exploitability / hackable-task ratio | False rejection of valid alternatives | Sensitivity-like exploits | We also probe over-constraint; we do not train an attacking agent |
| muteval | Mutation testing of LLM eval suites | Would evals catch a degraded *system under test*? | Would evals reject a still-correct *implementation*? | Sensitivity of evals | muteval degrades the SUT; we transform *candidates* and require both invariance and sensitivity |
| eval-integrity (skill) | Static checklist for benchmark repos | Missing methodology scaffolding | Dynamic grader behavior | Docs | Complementary; we run code |
| RewardHackingAgents | Integrity of ML-engineering agents vs tampering/leakage | Evaluator tampering, leakage | Decision boundary of a unit grader | Integrity | Different threat (agent attacks the metric) |
| Tool-Veritas / similar tool-eval work | Tool-use correctness | Tool traces | Grader region | Low | Out of scope for v0.1 |
| Mubric | Mutation-guided rubric generation for LLM judges | Rubric sensitivity to injected defects | Code-evaluator boundaries, false rejection | Sensitivity analogy | Rubrics vs executable graders |
| KernelBench mutation analysis | Mutation adequacy of GPU-kernel oracles | Fault detection of checkers | Invariance / over-constraint | Sensitivity | Domain-specific; we generalize the pair idea |
| Metamorphic testing (Chen et al.; LLMORPH; surveys 2026) | Relation oracles among related executions | MR violations | Typically tests the *model*, not the *grader* | Method ancestor | We apply MRs to the grader's verdict |
| Classical mutation testing | Adequacy of a test suite via mutants | Kill rate | Equivalent mutants as a nuisance | Sensitivity | We *want* equivalent (invariance) mutants as a first-class class |
| Property / differential / oracle testing | Specs, multi-impl comparison | Disagreement | Evaluator-specific false rejection | Related | We compare an evaluator to declared relations, not to a second implementation |

## Naming

`eval-boundary` is a glossary term (NHI Mgmt Group, 2026) meaning "smallest
functional unit of an agentic system that can be measured." That is a different
idea. `boundary-bench` measures agents under sandbox policies. `etb-scan`
measures judge injection (Evaluator Trust Boundary). The package name
**graderprobe** was chosen to avoid those collisions.

## What we refused to duplicate

- A leaderboard
- A generic eval runner
- An LLM-as-judge calibration library
- A red-team agent that rewrites benchmarks in place

If a planned feature was "audit the repo statically," that belongs to
eval-integrity, not here.
