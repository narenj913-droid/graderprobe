# GraderProbe expanded DeepEval trial results

These outputs come from the real DeepEval worktrees at the exact pinned revisions:
- **Base Revision:** `d65c8da504ca566d3b9590b798c72b9ab720ce59`
- **PR Head Revision:** `e24bff266a4fc2ab5046c18e8348f130c7d5625f`

## End-to-End Trial Summary

| Side | Task | Profile | False rejection | Invariance preserved | SHA-256 |
|---|---|---|---:|---:|---|
| base | `deepeval-sweep-issue-3338-original` | `BOUNDARY_FAIL` | 1 | 0 | `70afe2f528ef540f748e1a8c97a91d683be350c46987e97335f70ded782f8b03` |
| base | `deepeval-sweep-same-name-partial-assignment-3x3` | `BOUNDARY_FAIL` | 1 | 0 | `6db643b41b5db6dd29f63f029c1ad706b264211318a5323c6226cd4a05a805c2` |
| base | `deepeval-sweep-seed-3338-case-023` | `BOUNDARY_FAIL` | 1 | 0 | `d9a0687882ec68dc1173cec89e58f1dd4244b216ce70a2f65ccf6b527d3b2d16` |
| pr_head | `deepeval-sweep-issue-3338-original` | `BOUNDARY_OK` | 0 | 1 | `2fdc1a5c6dc88978ac08f49b1c83cf6189b70c80ed928f3b3707ef6af41d5440` |
| pr_head | `deepeval-sweep-same-name-partial-assignment-3x3` | `BOUNDARY_OK` | 0 | 1 | `9f2973fa1fce06f4bff56f5756f8c0133ec29a50c8ed681f66ed7b389484563f` |
| pr_head | `deepeval-sweep-seed-3338-case-023` | `BOUNDARY_OK` | 0 | 1 | `30b5a62014069f3cb0ce1c8b83c3e32ee2dffd97954ec2a222ebac77c464ffe7` |

## Per-Case Score Transitions

| Case ID | Base Baseline (PASS) | Base Reordered (FAIL) | Base Transition | PR Head Baseline (PASS) | PR Head Reordered (PASS) | PR Head Transition |
|---|---:|---:|:---:|---:|---:|:---:|
| `issue-3338-original` | 0.666667 | 0.500000 | `0.666667 -> 0.500000` | 0.666667 | 0.666667 | `0.666667 -> 0.666667` |
| `same-name-partial-assignment-3x3` | 0.666667 | 0.555556 | `0.666667 -> 0.555556` | 0.777778 | 0.777778 | `0.777778 -> 0.777778` |
| `seed-3338-case-023` | 0.666667 | 0.583333 | `0.666667 -> 0.583333` | 0.666667 | 0.666667 | `0.666667 -> 0.666667` |

## Oracle & Boundary Semantics

- **Raw DeepEval Score Output:** Measured directly from `ToolCorrectnessMetric.measure()` on each checked-out revision with threshold 0.60. On Base, greedy first-match causes scores to drop below 0.60 upon reversing expected tools. On PR Head, optimal assignment yields invariant scores above threshold.
- **Independent Behavioral Oracle:** Each task includes an independent behavior-validator oracle (`behavior_validator.py`) calculating global maximum bipartite matching. The oracle confirms the expected property holds (true score is invariant). This oracle is not DeepEval's metric and does not represent upstream maintainer acceptance.

Expected summary: all three tasks are `BOUNDARY_FAIL` on base and `BOUNDARY_OK` on PR head.
This is an expected-target assertion, not a claim that any third party adopted or endorsed GraderProbe.
