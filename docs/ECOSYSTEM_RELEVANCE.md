# Ecosystem relevance

AI benchmark results can misrepresent model capability when the evaluator itself has defects. OpenAI's July 8, 2026 audit of SWE-Bench Pro estimated that roughly 30% of tasks were broken and grouped the failures into over-strict tests, underspecified prompts, low-coverage tests, and misleading prompts.

GraderProbe addresses a narrower layer of this problem: the evaluator decision boundary. It compares controlled counterfactuals that should preserve a verdict with minimal changes that should invalidate it, and records the observed relation as evidence.

The project is intentionally vendor-neutral and local-first. It can be used with an evaluator regardless of which model or provider produced the candidate. It does not claim formal correctness or benchmark certification.

Its ecosystem value comes from making a previously informal review question more reproducible:

> Does this evaluator distinguish a meaningful behavioral change from an irrelevant implementation change?

The Stage 2 independent behavior-validator hook also makes stronger claims conditional on a second executable contract rather than on the evaluator under test.


## Change-aware release assurance

Version-to-version assurance is an explicit maintainer workflow: the same probe set is replayed across base and head revisions where possible, changed artifacts are classified, comparability is recorded, and a release decision is produced. This is deliberately narrower than general LLM evaluation or red-teaming platforms.
