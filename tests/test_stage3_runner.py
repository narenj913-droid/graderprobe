from __future__ import annotations

import unittest
from pathlib import Path

from graderprobe.runner import RunConfig, run_task
from graderprobe.task import load_task
from graderprobe.types import ProfileVerdict


ROOT = Path(__file__).resolve().parents[1] / "corpus" / "tasks"


class Stage3RunnerTests(unittest.TestCase):
    def test_parallel_execution_preserves_probe_order_and_verdict(self) -> None:
        task = load_task(ROOT / "healthy-control" / "task.yaml")
        profile = run_task(task, config=RunConfig(validate_behavior=True, validate_behavior_all=True, max_workers=2))
        self.assertEqual(profile.verdict, ProfileVerdict.BOUNDARY_OK)
        self.assertEqual([p.pair_id for p in profile.pairs], [f"PAIR-{i:03d}" for i in range(1, 7)])

    def test_auto_audit_finds_under_constraint(self) -> None:
        task = load_task(ROOT / "under-constrained-auth" / "task.yaml")
        profile = run_task(
            task,
            config=RunConfig(
                include_auto_probes=True,
                include_auto_sensitivity=True,
                validate_behavior=True,
                max_workers=2,
            ),
        )
        self.assertEqual(profile.verdict, ProfileVerdict.BOUNDARY_FAIL)
        self.assertGreaterEqual(profile.metrics.false_acceptance_count, 2)


if __name__ == "__main__":
    unittest.main()
