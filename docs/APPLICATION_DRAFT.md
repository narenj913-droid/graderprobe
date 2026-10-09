# Codex for Open Source — application draft

Snapshot: 2026-10-10

These are drafts for the current form. Replace project URL, GitHub username, identity fields, and any live usage metrics with real values immediately before submission.

## Why does this repository qualify?

GraderProbe is an open-source QA layer for AI evaluators: it detects verdict changes caused by irrelevant perturbations such as ordering or scheduling. It is deterministic by default and emits reproducible evidence, causal attribution, and SARIF/CI artifacts. We independently tested DeepEval issue #3338 against its exact base and proposed-fix commits; other public-source cases are clearly marked as local reproductions pending upstream verification.

Character count: 452 / 500

## How will you use API credits for your project?

Use Codex/API credits for repeatable maintainer workflows: audit changed evaluator code, generate bounded adversarial cases, compare baseline/counterfactual results, summarize evidence, and draft focused regression/PR changes for human review. The goal is to turn evaluator-quality checks into a repeatable PR/release gate rather than generic code generation.

Character count: 359 / 500

## Anything else we should know?

The project is intentionally conservative about evidence: the DeepEval #3338 before/after run used exact upstream commits, while other case files distinguish local faithful reproductions from upstream validation. No external adoption or maintainer endorsement is claimed without an authorized external run.

Character count: 306 / 500

## Submission gate

Do not submit these fields as if external adoption already exists. The application should only claim what is visible in the public repository and linked evidence.

Before submission, refresh:
- repository URL and public visibility
- maintainer role
- current release
- real stars/downloads/usage, if any
- independent maintainer run, if obtained
- external PR/CI integration evidence, if obtained
