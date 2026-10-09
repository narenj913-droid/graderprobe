from __future__ import annotations

import itertools
import math
import unittest
from pathlib import Path

from graderprobe.runner import RunConfig, run_task
from graderprobe.types import (
    EvaluatorSpec,
    FindingType,
    OracleSpec,
    ProbeSpec,
    ProfileVerdict,
    TaskSpec,
    TransformSpec,
    Verdict,
)

ROOT = Path(__file__).resolve().parents[1]


def _pair_sim(exp: dict, cal: dict) -> float:
    if exp["name"] != cal["name"]:
        return 0.0
    params = exp["input_parameters"]
    if not params:
        return 1.0 if not cal["input_parameters"] else 0.0
    return sum(cal["input_parameters"].get(k) == v for k, v in params.items()) / len(params)


def optimal_score(exp: list[dict], cal: list[dict]) -> float:
    if not exp:
        return 1.0
    m = len(exp)
    n = len(cal)
    best = 0.0
    for chosen in itertools.permutations(range(n), min(m, n)):
        assignment = list(chosen) + [-1] * max(0, m - len(chosen))
        total = sum(0.0 if j < 0 else _pair_sim(exp[i], cal[j]) for i, j in enumerate(assignment))
        best = max(best, total / m)
    return best


def greedy_score(exp: list[dict], cal: list[dict]) -> float:
    if not exp:
        return 1.0
    unused = list(range(len(cal)))
    total = 0.0
    for e in exp:
        best_sim = -1.0
        best_j = None
        for j in unused:
            sim = _pair_sim(e, cal[j])
            if sim > best_sim:
                best_sim = sim
                best_j = j
        if best_j is not None:
            unused.remove(best_j)
            total += max(0.0, best_sim)
    return total / len(exp)


class Phase5DeepEval3339ValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.expected = [
            {"name": "book", "input_parameters": {"a": 1, "b": 1, "c": 2}},
            {"name": "book", "input_parameters": {"a": 1, "b": 1, "c": 1}},
        ]
        self.called = [
            {"name": "book", "input_parameters": {"a": 1, "b": 1, "c": 2}},
            {"name": "book", "input_parameters": {"a": 1, "b": 5, "c": 5}},
        ]

    def test_optimal_assignment_is_order_invariant_across_all_permutations(self) -> None:
        """Healthy control: optimal matching produces the same score for all permutations."""
        scores = []
        for exp_perm in itertools.permutations(self.expected):
            for cal_perm in itertools.permutations(self.called):
                s = optimal_score(list(exp_perm), list(cal_perm))
                scores.append(s)
        self.assertTrue(all(math.isclose(s, scores[0], abs_tol=1e-9) for s in scores))
        self.assertAlmostEqual(scores[0], 2.0 / 3.0, places=5)

    def test_greedy_assignment_is_sensitive_to_expected_order(self) -> None:
        """Bug reproduction: greedy matching flips scores depending on expected tools order."""
        s_forward = greedy_score(self.expected, self.called)
        s_reverse = greedy_score(list(reversed(self.expected)), self.called)
        self.assertAlmostEqual(s_forward, 2.0 / 3.0, places=5)
        self.assertAlmostEqual(s_reverse, 0.5, places=5)
        self.assertNotEqual(s_forward, s_reverse)

    def test_pr3339_fixed_grader_control_yields_boundary_ok(self) -> None:
        """Proves GraderProbe yields BOUNDARY_OK when evaluator is fixed (PR #3339 behavior)."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            (d / "solution.py").write_text("x = 1\n", encoding="utf-8")
            (d / "alt.py").write_text("x = 1\n# reordered\n", encoding="utf-8")
            (d / "evaluator.py").write_text("import sys\nsys.exit(0)\n", encoding="utf-8")
            task_yaml = d / "task.yaml"
            task_yaml.write_text(
                "id: fixed-deepeval-control\n"
                "description: Simulated fixed DeepEval PR #3339\n"
                "candidate_file: solution.py\n"
                "oracle:\n"
                "  reference: solution.py\n"
                "  expected_behavior: order-invariant tool matching\n"
                "  expected_baseline_verdict: PASS\n"
                "evaluator:\n"
                "  command: ['python', 'evaluator.py']\n"
                "probes:\n"
                "  invariance:\n"
                "    - id: INV-REORDER\n"
                "      description: Reorder expected tools\n"
                "      target: solution.py\n"
                "      transform: {kind: replace_file, source: alt.py}\n",
                encoding="utf-8",
            )
            from graderprobe.task import load_task
            task = load_task(task_yaml)
            profile = run_task(task, config=RunConfig(max_workers=1, execution_slots=1))
            self.assertEqual(profile.verdict, ProfileVerdict.BOUNDARY_OK)
            self.assertEqual(profile.metrics.false_rejection_count, 0)
            self.assertEqual(profile.metrics.false_acceptance_count, 0)
            self.assertEqual(profile.metrics.invariance_preserved, 1)
            self.assertTrue(all(f.type == FindingType.RELATION_HELD for f in profile.findings))


if __name__ == "__main__":
    unittest.main()
