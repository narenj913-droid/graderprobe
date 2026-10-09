# Inspect AI #4721 / #4769 — real external contribution proof

As of 2026-10-06, public Inspect AI history shows issue #4721 was explicitly labeled `acceptedIssues: maintainer-approved for external PR`. The linked external PR #4769 was opened from contributor branch `tonydzi:grader-panel-majority` and was merged by maintainer `dragonstyle` into `main` on 2026-09-01.

The PR documents an end-to-end reproduction using `mockllm`, 384 relevant tests plus 4 skips, lint/type checks on changed files, and explicit disclosure of unresolved boundaries. This is a concrete example of the maintainer path we are targeting: a precise public bug -> externally prepared reproduction/fix -> maintainer review -> merged contribution.

GraderProbe should learn from this pattern rather than merely asking for endorsements.

Source issue: https://github.com/UKGovernmentBEIS/inspect_ai/issues/4721
Source PR: https://github.com/UKGovernmentBEIS/inspect_ai/pull/4769
