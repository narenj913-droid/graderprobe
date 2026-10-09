# Maintainer collaboration packet

## Primary target: DeepEval #3338

The issue is public, deterministic, and explicitly reports an order-dependent score in a mode documented as order-insensitive. The issue author has proposed a max-weight one-to-one assignment fix and states that regression tests are ready.

GraderProbe's role should be independent validation, not duplicate ownership of the fix:

1. Run the author's issue reproduction at the exact referenced revision.
2. Verify the same behavior through a paired counterfactual.
3. Record the GraderProbe profile and independent semantic validator.
4. Offer the evidence packet to the issue author/maintainer.
5. If the author requests code review or additional regression coverage, contribute only the smallest change needed.

Source: https://github.com/confident-ai/deepeval/issues/3338

## Why this route is chosen

Inspect AI #4721 provides a concrete precedent: it was labeled as approved for an external PR and linked external PR #4769 was merged by a maintainer. The PR shows the exact pattern worth reproducing: a precise public issue, a focused fix, documented reproduction, test evidence, explicit boundary disclosure, and maintainer review.

Source issue: https://github.com/UKGovernmentBEIS/inspect_ai/issues/4721
Source merged PR: https://github.com/UKGovernmentBEIS/inspect_ai/pull/4769

## Non-negotiables

- No fabricated maintainer quote or endorsement.
- No claim of upstream execution until an authorized run is captured.
- No scan/probe of a repository without owner authorization.
- No claim that stars, downloads, or any fixed adoption threshold guarantees selection.
