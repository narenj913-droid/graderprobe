# DeepEval #3338 — contribution strategy

## Do not open a fix-first PR

The issue author says they already have a regression-tested max-weight assignment fix ready and plan to open a PR. The best GraderProbe move is therefore independent validation, not duplicating the proposed implementation.

Source: https://github.com/confident-ai/deepeval/issues/3338

## Preferred sequence

1. Comment once on #3338 with the independent validation offer.
2. If the maintainer/author agrees, run the bundle against the exact upstream revision they specify.
3. Publish the immutable result in the GraderProbe evidence tree.
4. If their fix PR lands, run the same probe against parent and fixed revisions.
5. Report PASS/FAIL as a before/after boundary check.
6. Only then consider a tiny upstream test/helper contribution if explicitly useful.

## Evidence to capture

- upstream repository URL
- exact git HEAD
- GraderProbe version/commit
- command line
- baseline output
- counterfactual output
- semantic oracle result
- finding ID
- timestamp
- SHA-256 of the evidence JSON

## Success states

### Best
Maintainer/author runs the bundle and replies with the result; fixed PR is later merged; GraderProbe verifies the post-fix revision.

### Good
Maintainer/author runs the bundle and confirms the behavior, even if they choose a different fix.

### Useful
Maintainer does not run the bundle but accepts a focused test or requests the evidence for review.

### No signal
No reply. Do not spam or manufacture activity; move to the next legitimate target.
