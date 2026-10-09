# Phase 3 result — external trial infrastructure and contribution path

## Verified progress

1. Three public evaluator failure families are represented: DeepEval #3338, DeepEval #3025, and Inspect AI #4721.
2. DeepEval #3025 is isolated into two valid baseline trials so its sync/async and declaration-order axes can each produce a PASS→FAIL boundary independently under a controlled threshold.
3. Trial runners can execute directly against an authorized upstream source checkout by adding that checkout (and `src/` when present) to `PYTHONPATH`, while recording the exact git HEAD.
4. A maintainer runbook and collaboration packet now separate public-source evidence, local smoke validation, and real upstream validation.
5. Focused regression/validation suite: **9 passed**.

## Strong external precedent

Inspect AI issue #4721 was explicitly marked `acceptedIssues: maintainer-approved for external PR`; linked external PR #4769 was opened from an external contributor branch and merged by maintainer `dragonstyle` on 2026-09-01. The PR documents the reproduction, targeted tests, lint/type checks, and explicit boundary disclosures. This is direct public evidence that the external contribution route we are targeting is real. See `docs/external-cases/phase3/INSPECT_AI_4769_PROOF.md`.

## DeepEval current opportunity

DeepEval #3338 is currently public and open; its issue text gives a deterministic reproduction on `d65c8da`, explains the greedy-matching root cause, and states that a regression-tested max-weight assignment fix is ready/planned. GraderProbe should therefore act as an independent validation layer around that issue rather than pretending to own the fix.

## Evidence boundary

The local smoke artifacts are deliberately labeled as stub-based. They demonstrate that GraderProbe detects the intended boundary and that the trial bundle works. They do not demonstrate that today's real upstream packages still reproduce the historical behavior.

No external maintainer validation, external CI adoption, endorsement, or selection probability is claimed yet.

## Next evidence gate

Obtain one authorized upstream execution on DeepEval #3338, preserve the exact commit, and capture the maintainer/contributor's verdict in an immutable evidence record. After that, pursue a small external PR/CI integration only where the upstream maintainer indicates a useful path.
