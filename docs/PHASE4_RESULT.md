# Phase 4 Result — Selection Evidence + External Collaboration Pack

Snapshot: 2026-10-06

## Completed

- Added a source-backed selection evidence review separating accepted-recipient reports, no-response reports, official criteria, and project-specific gaps.
- Added a concise DeepEval #3338 comment that offers independent validation without claiming endorsement.
- Added a contribution strategy that avoids duplicating the issue author's proposed fix and prioritizes before/after verification.
- Added current application drafts constrained to the form's 500-character fields.
- Added an explicit selection-readiness gate that treats 30% as an internal target, not a statistical claim.

## External research anchors

- Current Codex for Open Source application: https://openai.com/form/codex-for-oss/
- DeepEval #3338: https://github.com/confident-ai/deepeval/issues/3338
- DeepEval #3025: https://github.com/confident-ai/deepeval/issues/3025
- Inspect AI #4721: https://github.com/UKGovernmentBEIS/inspect_ai/issues/4721
- Inspect AI #4769 precedent: https://github.com/UKGovernmentBEIS/inspect_ai/pull/4769
- Discourse acceptance report: https://community.openai.com/t/codex-for-open-source-2026/1376418
- Super Productivity acceptance report: https://github.com/openai/codex/issues/42620
- Public no-response reports: https://news.ycombinator.com/item?id=48497195
- OpenAI Evals model-graded/meta-eval guidance: https://github.com/openai/evals/blob/main/docs/build-eval.md

## Verification

Focused validation completed after Phase 4 docs were added:

- tests/test_external_cases.py: PASS (2)
- tests/test_phase3_deepeval_3025.py: PASS (2)
- tests/test_phase3_trial_bundle.py: PASS (3)
- tests/test_public_reliability.py: PASS (2)
- Python compileall: PASS
- GitHub workflow YAML parse: PASS

A wheel build was not performed because the environment did not provide the `build` module. This is an environment/tooling limitation, not evidence that packaging is broken.

## Current external-evidence boundary

Still pending:

- authorized upstream execution by DeepEval maintainer/authorized developer
- external repository CI adoption
- maintainer endorsement
- merged upstream contribution from GraderProbe

Do not claim any of those until a public or maintainer-provided artifact exists.
