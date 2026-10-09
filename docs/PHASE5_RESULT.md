# Phase 5 Result — Independent Exact-Revision Validation of DeepEval Issue #3338 & PR #3339

Snapshot: 2026-10-09  
Environment: Windows 11, Python 3.13.3, GraderProbe 0.8.0  
Evaluation Mode: Strictly offline deterministic local evaluation (zero LLM API calls, dummy local configuration for non-evaluative metric initialization).

---

## 1. Executive Summary

We performed an independent, exact-revision before/after validation of DeepEval issue [#3338](https://github.com/confident-ai/deepeval/issues/3338) against linked pull request [#3339](https://github.com/confident-ai/deepeval/pull/3339) (*"fix(tool_correctness): pair calls by optimal assignment in unordered mode"*).

The evaluation verified that:
1. **The defect is real and reproducible on base revision `d65c8da504`**: In greedy sequential assignment mode, permuting the order of `expected_tools` flips the evaluated score from `0.666667` (PASS) down to `0.500000` (FAIL), producing an unintended false rejection on a semantically identical unordered multiset.
2. **PR #3339 head commit `e24bff266a` causally resolves the defect**: Re-evaluating the identical permutation space yields invariant scores of `0.666667` (PASS) across all 4 ordering permutations.
3. **PR #3339 does not overfit to the issue reporter's specific example**: The PR replaces the greedy first-best matching loop with a global optimal bipartite assignment algorithm (`scipy.optimize.linear_sum_assignment` with brute-force fallback for small sets), proving general order-invariance across both `expected` and `actual` call permutations.
4. **GraderProbe boundary integrity profile flips from defect to healthy**:
   - Before (`d65c8da504`): `BOUNDARY_FAIL` with 1 confirmed HIGH-severity false rejection (`INV-UPSTREAM-EXPECTED-ORDER-01`).
   - After (`e24bff266a`): `BOUNDARY_OK` with 0 false rejections, 0 false acceptances, and invariance preservation rate of 100% (1/1).

---

## 2. Revision Pinning Matrix

| Attribute | Base Revision (Before) | PR #3339 Head Revision (After) |
| :--- | :--- | :--- |
| **Commit SHA** | `d65c8da504ca566d3b9590b798c72b9ab720ce59` | `e24bff266a4fc2ab5046c18e8348f130c7d5625f` |
| **Commit Message** | Merge pull request #3311 from AbdoAlshoki2/docs/add-missing-args | test(tool_correctness): pin order-independent pairing |
| **PR Status** | Base branch (`main`) target | PR #3339 head branch (`issue-3338-tool-correctness-order-independent-pairing`) |
| **Isolation Directory** | `%TEMP%\graderprobe-deepeval-3338-validation\before` | `%TEMP%\graderprobe-deepeval-3338-validation\after` |

---

## 3. Comparative Evidence Matrix

### 3.1 All-Permutations Evaluation (`ToolCorrectnessMetric`)

Inputs: 2 expected tool calls, 2 actual tool calls, threshold = `0.60`.

| Permutation | Base `d65c8da504` Score | Base Verdict | PR #3339 `e24bff266a` Score | PR #3339 Verdict |
| :--- | :--- | :--- | :--- | :--- |
| `expected[0, 1]`, `called[0, 1]` | `0.500000` | FAIL | `0.666667` | PASS |
| `expected[0, 1]`, `called[1, 0]` | `0.666667` | PASS | `0.666667` | PASS |
| `expected[1, 0]`, `called[0, 1]` | `0.500000` | FAIL | `0.666667` | PASS |
| `expected[1, 0]`, `called[1, 0]` | `0.666667` | PASS | `0.666667` | PASS |
| **Order Invariant?** | **FALSE** | Score flips | **TRUE** | Identical (0.666667) |

Artifacts:
- `artifacts/phase5/deepeval-3338-before-permutations.json`
- `artifacts/phase5/deepeval-3338-after-permutations.json`

### 3.2 PR #3339 Focused Unit Tests (`tests/test_tool_correctness_metric.py`)

Ran `pytest tests/test_tool_correctness_metric.py -k TestToolCorrectnessMetricAssignment`:

| Test Name | Base `d65c8da504` | PR #3339 `e24bff266a` |
| :--- | :--- | :--- |
| `test_unordered_pairing_is_order_independent_when_multiple_calls_share_name` | **FAILED** | **PASSED** |
| `test_exact_call_matches_first_over_partial_call_when_multiple_calls_share_name` | **FAILED** | **PASSED** |
| `test_exact_call_matches_first_when_candidates_are_reversed` | **FAILED** | **PASSED** |
| `test_unordered_pairing_matches_best_available_when_expected_has_surplus_calls` | **PASSED** | **PASSED** |
| `test_unordered_pairing_matches_best_available_when_actual_has_surplus_calls` | **PASSED** | **PASSED** |
| **Summary** | **3 failed, 2 passed** (2.77s) | **5 passed** (2.40s) |

Artifacts:
- `artifacts/phase5/deepeval-pr3339-tests-on-base-d65c8da.log`
- `artifacts/phase5/deepeval-pr3339-tests-on-pr3339-head.log`

### 3.3 GraderProbe Upstream Direct Trial & Boundary Profile

Ran `deepeval_3338_upstream.py` and `graderprobe run corpus/external-trials/deepeval-3338/task.yaml`:

| Metric / Dimension | Base `d65c8da504` | PR #3339 `e24bff266a` |
| :--- | :--- | :--- |
| Upstream Direct Trial Outcome | `reproduced` (baseline PASS 0.667, mutant FAIL 0.500) | `not_reproduced_or_changed` (both PASS 0.667) |
| GraderProbe Profile Verdict | **`BOUNDARY_FAIL`** | **`BOUNDARY_OK`** |
| Invariance Preserved / Executed | 0 / 1 (0.0%) | 1 / 1 (100.0%) |
| Confirmed False Rejection Count | 1 (`INV-UPSTREAM-EXPECTED-ORDER-01`) | 0 |
| Confirmed False Acceptance Count | 0 | 0 |
| Findings Severity | 1 HIGH | 0 defects (1 info relation_held) |

Artifacts:
- `artifacts/phase5/deepeval-3338-before-trial.json`
- `artifacts/phase5/deepeval-3338-after-trial.json`
- `artifacts/phase5/graderprobe-run-base-d65c8da/`
- `artifacts/phase5/graderprobe-run-after-pr3339/`

---

## 4. Causal Attribution & Fix Quality Analysis

1. **Why base was defective**:
   DeepEval evaluated unordered tools by iterating linearly through `expected_tools`, greedily binding each expected call to whichever available called tool had the highest similarity score. When multiple called tools shared the same function name with varying parameter overlaps, a greedy choice for an earlier expected tool consumed a called tool that would have yielded a higher global sum if reserved for a later expected tool.

2. **Why PR #3339 correctly fixes it**:
   PR #3339 computes pairwise similarity across all `(expected, called)` pairs and solves the maximum weight bipartite matching problem (using the Hungarian algorithm via `scipy.optimize.linear_sum_assignment` or exact permutation assignment when sets are small). Because maximum weight bipartite matching optimizes the global sum independent of input indexing, the resulting pairing is mathematically guaranteed to be permutation-invariant over both expected and actual multiset orderings.

3. **No Overfitting**:
   The fix is purely algorithmic and operates on arbitrary multisets. It does not introduce hardcoded branch conditions, special-case ordering heuristics, or test-specific constants.

---

## 5. Artifact Hashes (SHA-256 Manifest)

All generated artifacts are recorded in `artifacts/phase5/SHA256SUMS.txt`:

```
c4216d0ad447e9b9a39f82595fbde4efd869b67e6674be308b3a0909b5068276  deepeval-3338-after-permutations.json
354a3cb3661f784b1dc807cfe83f647f1b65fa383053172367e9d1e77a846f0a  deepeval-3338-after-trial.json
2912cd89c841820bb6e148d1eefb5ce0cf2aa2b56bcc60474d5a65b0ab6caff0  deepeval-3338-before-permutations.json
6b67402710df90622277cf0ab94e4ea0560ea4063816a951f564581a30cc6dc0  deepeval-3338-before-trial.json
7fb551cb25f2b413c37862098c4196156f8daff5a2d52096aa979e2090f3caa9  deepeval-pr3339-tests-on-base-d65c8da.log
a58fb0a1701afd32948b036d14345d4f093c8180f51adc90ff3cabc4ada7bb5e  deepeval-pr3339-tests-on-pr3339-head.log
3715170b3766cd89f84e74d3adc7ca4662a8521cf8e15d81a0b4339754cd2f42  graderprobe-run-after-pr3339/CERTIFICATE.json
a8cd09aa6995b73d67697fa6c7a8ca478f3dfbc009d610a4a909f43dd9810c69  graderprobe-run-after-pr3339/profile.html
6854124d0ab68cece40b07a4ef6fb0b1126d3c4fc798464d0edba60f2bd96d65  graderprobe-run-after-pr3339/profile.json
de02b5f4d92891d910be4dc95244b7372bef859d4edea1b84b7bacdb23c3b8ae  graderprobe-run-after-pr3339/profile.md
860589f7385e2238b4164e4e0333c1ceb8a84169ae5a7bf931ab37037959064b  graderprobe-run-after-pr3339/replay.json
2d6d74f07cda295302fffa16e1dfa58a73b98d2d515cb363a6997011fda5e5e9  graderprobe-run-base-d65c8da/CERTIFICATE.json
02bc48293d060fe440dcf78da82a1380a4ab2dce08e8e620095255b17ae6236d  graderprobe-run-base-d65c8da/profile.html
5cb0b06c606632d8402cf8d0d57fb409c60ebfc3f24c56363d6a2449514e964c  graderprobe-run-base-d65c8da/profile.json
b11bc22429384dc36e8797caeb139eb27ceb3dce634fa3bfcf5b59ed8268e7b4  graderprobe-run-base-d65c8da/profile.md
4eec86e8b34160f2f9f69c9f1b5443331c69ee3a1e45688b46fd6e84966cd954  graderprobe-run-base-d65c8da/replay.json
```

---

## 6. External Evidence Boundary

- **No Upstream Execution Claim**: All executions documented here were performed in an independent, local reproduction harness. Neither DeepEval maintainers nor upstream CI have executed this GraderProbe bundle.
- **No Maintainer Endorsement**: GraderProbe makes no claim of endorsement, partnership, or affiliation with Confident AI / DeepEval.
- **Posting Constraint**: Because no authenticated GitHub credentials or tokens are configured, the public comment draft is preserved locally in `docs/outreach/DEEPEVAL_PR3339_COMMENT_DRAFT.md` for human review prior to posting.
