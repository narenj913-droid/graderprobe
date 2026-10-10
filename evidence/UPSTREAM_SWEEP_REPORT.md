# DeepEval Deterministic Test Sweep Report: Base vs. PR #3339

This report documents the results of an expanded, offline, deterministic test sweep executed directly against the actual upstream `confident-ai/deepeval` repository source code across two exact git revisions.

---

## 1. Target Revisions & Upstream Status

- **Upstream Repository**: [`confident-ai/deepeval`](https://github.com/confident-ai/deepeval)
- **Pull Request**: [confident-ai/deepeval#3339](https://github.com/confident-ai/deepeval/pull/3339)
- **Current Upstream PR Status**: `OPEN` (Queried live on GitHub API; unmerged)
- **Live PR Head SHA**: `e24bff266a4fc2ab5046c18e8348f130c7d5625f`
- **Revisions Evaluated**:
  1. **Base Revision**: `d65c8da504ca566d3b9590b798c72b9ab720ce59` (the upstream base commit PR #3339 branched from)
  2. **PR Head Revision**: `e24bff266a4fc2ab5046c18e8348f130c7d5625f` (identical to current live PR head)

---

## 2. Test Execution Matrix

The following test suites were executed on both revisions using isolated detached worktrees and `PYTHONPATH` precedence. All runs were conducted offline (`DEEPEVAL_DISABLE_DOTENV=1`, no model API keys).

| Test Area / Evaluation Lane | Base (`d65c8da`) | PR Head (`e24bff2`) | Status & Delta Details |
| :--- | :---: | :---: | :--- |
| **Focused Assignment Regressions**<br>`pytest -k TestToolCorrectnessMetricAssignment`<br>*(No API Key in env)* | **5 skipped**<br>(7 deselected) | **5 skipped**<br>(7 deselected) | Upstream module guard skips suite when `OPENAI_API_KEY` is completely unset (`pytestmark = pytest.mark.skipif(...)`). |
| **Focused Assignment Regressions**<br>`pytest -k TestToolCorrectnessMetricAssignment`<br>*(Offline dummy key `mock-offline`)* | **3 failed**, 2 passed<br>(7 deselected) | **5 passed**<br>(7 deselected) | **Regression Resolved**: Base fails 3 test cases due to greedy first-match assignment; PR head passes all 5 tests (100%). |
| **Full Metric Test File**<br>`tests/test_metrics/test_tool_correctness_metric.py`<br>*(Base's original 7 tests)* | **7 passed** | N/A | Existing tests on Base pass without issue. |
| **Full Metric Test File**<br>`tests/test_metrics/test_tool_correctness_metric.py`<br>*(PR's full 12 tests against each source)* | **3 failed**, 9 passed | **12 passed**<br>(100% pass) | All 12 unit and regression tests pass cleanly on PR head. |
| **Deterministic Core Imports**<br>`tests/test_core/test_imports.py` | **15 passed** | **15 passed** | No regression in core package import integrity. |
| **Deterministic Single Turn Tests**<br>`tests/test_core/test_test_case/test_single_turn.py` | **39 passed** | **39 passed** | Deterministic test case container checks pass identically. |
| **Expanded Deterministic Sweep**<br>`tools/expanded_tool_correctness_sweep.py`<br>*(5 edge cases + 120 seeded random cases, seed 3338)* | **126 cases**<br>1,695 measurements<br>**10 failures** (92.06% inv.)<br>0 exceptions | **126 cases**<br>1,695 measurements<br>**0 failures** (100.0% inv.)<br>0 exceptions | **10 Order-Invariance Flaws Fixed**: Base produces order-dependent scores on 10 cases; PR head produces invariant scores across all 1,695 permutations. |
| **Explicit Ordering Control**<br>`should_consider_ordering=True` vs `False`<br>*(Call order reversed)* | Unordered: `1.0`<br>Ordered: `0.5`<br>**Passed** (`1.0 > 0.5`) | Unordered: `1.0`<br>Ordered: `0.5`<br>**Passed** (`1.0 > 0.5`) | **Contract Preserved**: PR #3339 preserves ordering penalization when `should_consider_ordering=True`. |
| **Exploratory Exact-Match Lane**<br>`should_exact_match=True` probe | 3 invariant,<br>1 variant | 3 invariant,<br>1 variant | Identical behavior on both revisions (`mixed-tool-names-perfect-multiset` evaluates to `[0.0, 1.0]`). See Section 5. |

---

## 3. Direct Comparison: Specific Order-Invariance Failures

The expanded sweep identified **10 specific test configurations** where Base produced order-dependent scores for identical multiset calls under `should_consider_ordering=False`. Under PR #3339, all 10 cases achieved deterministic invariance.

| Case ID | Permutations Tested | Base Score Range | Base Verdicts | PR Head Score | PR Head Invariant? |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `issue-3338-original` | 4 pairs | `0.5000` – `0.6667` | `[False, True]` | **`0.6667`** | **Yes** (True) |
| `undersupplied-repeated-name` | 6 pairs | `0.2222` – `0.3333` | `[False]` | **`0.3333`** | **Yes** (True) |
| `same-name-partial-assignment-3x3` | 36 pairs | `0.5556` – `0.7778` | `[False, True]` | **`0.7778`** | **Yes** (True) |
| `seed-3338-case-023` | 30 pairs | `0.5833` – `0.6667` | `[False, True]` | **`0.6667`** | **Yes** (True) |
| `seed-3338-case-043` | 16 pairs | `0.2083` – `0.2917` | `[False]` | **`0.2917`** | **Yes** (True) |
| `seed-3338-case-054` | 10 pairs | `0.3333` – `0.5000` | `[False]` | **`0.5000`** | **Yes** (True) |
| `seed-3338-case-059` | 25 pairs | `0.2917` – `0.4167` | `[False]` | **`0.4167`** | **Yes** (True) |
| `seed-3338-case-092` | 30 pairs | `0.3125` – `0.5000` | `[False]` | **`0.5000`** | **Yes** (True) |
| `seed-3338-case-100` | 12 pairs | `0.2500` – `0.3750` | `[False]` | **`0.3750`** | **Yes** (True) |
| `seed-3338-case-106` | 30 pairs | `0.0625` – `0.2500` | `[False]` | **`0.2500`** | **Yes** (True) |

### Key Observations:
1. **Flaky Threshold Verdicts on Base**: In 3 of the 10 failing cases (`issue-3338-original`, `same-name-partial-assignment-3x3`, `seed-3338-case-023`), the metric verdict flipped between `FAIL` (`False`) and `PASS` (`True`) at threshold `0.60` purely based on the sequence in which tools were emitted.
2. **Suboptimal Greedy Matching on Base**: In cases with repeated tool names and variable parameter overlap, Base's first-come-first-served matching prematurely bonded a call to a sub-optimal target, blocking higher-scoring alignments later in the sequence.
3. **Optimal Bipartite Matching on PR Head**: PR #3339 replaces the greedy assignment with an optimal assignment algorithm, selecting the global score-maximizing alignment regardless of tool order.

---

## 4. Full Environment & Provenance Metadata

- **Operating System**: Windows 11 Pro (`Windows-11-10.0.22631-SP0`, AMD64)
- **Python Version**: `3.13.3` (tags/v3.13.3:6280bb5, Apr 8 2025, 14:47:33) [MSC v.1943 64 bit (AMD64)]
- **Pytest Version**: `9.1.1`
- **DeepEval Package Version**: `4.2.4`
- **Source Import Provenance**:
  - Base: `D:\deepeval_sweep_workspace\worktree_base\deepeval\__init__.py`
  - PR Head: `D:\deepeval_sweep_workspace\worktree_pr\deepeval\__init__.py`
- **Environment Flags**:
  - `DEEPEVAL_DISABLE_DOTENV=1`
  - All external model API keys (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `CONFIDENT_AI_API_KEY`, `GEMINI_API_KEY`, etc.) unset during test execution.

---

## 5. Important Caveats & Safeguards

1. **Independent Offline Validation**: These findings represent independent local validation executed against the checked-out upstream repository. They do not constitute official maintainer acceptance, endorsement, or external adoption.
2. **Exploratory Exact-Match Contract**: PR #3339 specifically targets `_calculate_non_exact_match_score` (the default mode `should_exact_match=False`). In exploratory testing with `should_exact_match=True`, the exploratory case `mixed-tool-names-perfect-multiset` yielded order-dependent scores (`[0.0, 1.0]`) on **both** Base and PR Head. This confirms that `should_exact_match=True` operates under positional multiset semantics and was not altered by PR #3339.
3. **Module Skip Guard Distinctions**: The upstream test file `tests/test_metrics/test_tool_correctness_metric.py` enforces a file-level skip when `OPENAI_API_KEY` is unset. Providing an offline dummy key (`OPENAI_API_KEY="mock-offline"`) enables running the deterministic `ToolCallParams.INPUT_PARAMETERS` evaluation suite without initiating any external network requests or LLM API calls.


## Editorial correction from JSON re-analysis
The original report narrative incorrectly said 4 of 10 cases crossed the verdict threshold while naming only three. The raw base-sweep JSON confirms exactly 3 verdict-flipping cases and 7 additional cases with score drift but no verdict flip at threshold 0.60. The original result ZIP is preserved unchanged; this derivative report corrects the summary to match its machine-readable results.
