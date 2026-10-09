# Stage 8 result — contract lock and frozen-candidate attribution

Stage 8 turns change assurance into persistent maintainer infrastructure.

## Evaluation-contract lock

`graderprobe.lock.json` records an approved Git revision, task inventory, task digests, evaluator contracts, probe-set digests, and optional behavioral anchor fingerprints. `graderprobe verify-lock` treats evaluation-surface changes as reviewable release changes rather than silently accepting drift.

A documentation-only change can pass without evaluation execution. Changes to evaluators, graders, verifiers, environments, probes, task contracts, or related surfaces are escalated to release assurance.

## Frozen-candidate causal attribution

A frozen cohort injects byte-identical candidate artifacts into base and head repository snapshots and replays the same probe set. When the candidate hash is unchanged but the profile outcome fingerprint changes, the tool reports `EVALUATOR_DRIFT`. Candidate byte drift is reported as `CANDIDATE_DRIFT` and remains non-comparable.

The tool intentionally avoids claiming formal causality or benchmark correctness. It records a controlled comparison and its evidence.

## Why this is strategically important

The project now addresses a maintainer lifecycle rather than only a one-off audit:

`approve evaluation contract -> lock -> PR change -> detect affected surface -> replay controls -> require evidence -> update lock after review`

This provides a concrete OSS maintenance workflow that can run locally and in GitHub Actions.

## Honest status

The repository still has no fabricated users, stars, downloads, partnerships, endorsements, or acceptance claims. External adoption must be earned after publication.
