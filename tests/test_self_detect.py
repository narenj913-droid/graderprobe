"""The project must detect four classes against a healthy evaluator.

1. A valid candidate passes.
2. A known-invalid candidate fails.
3. A harmless refactor stays valid.
4. A minimal requirement violation becomes invalid.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from graderprobe.baseline import validate_baseline
from graderprobe.runner import run_task
from graderprobe.task import load_task
from graderprobe.types import FindingType, ProfileVerdict, Verdict


def _healthy() -> Path:
    from graderprobe.corpus import corpus_dir

    return corpus_dir() / "healthy-control" / "task.yaml"


class SelfDetectionTests(unittest.TestCase):
    def test_valid_candidate_passes(self) -> None:
        task = load_task(_healthy())
        report = validate_baseline(task)
        self.assertTrue(report.ok)
        self.assertEqual(report.verdict, Verdict.PASS)

    def test_known_invalid_fails(self) -> None:
        task = load_task(_healthy())
        report = validate_baseline(task)
        self.assertIsNotNone(report.known_invalid)
        assert report.known_invalid is not None
        self.assertEqual(report.known_invalid.verdict, Verdict.FAIL)

    def test_harmless_refactor_stays_valid(self) -> None:
        profile = run_task(_healthy())
        inv = [pair for pair in profile.pairs if pair.probe.probe_class.value == "invariance"]
        self.assertTrue(inv)
        self.assertTrue(all(pair.relation_held for pair in inv))

    def test_minimal_violation_becomes_invalid(self) -> None:
        profile = run_task(_healthy())
        sen = [pair for pair in profile.pairs if pair.probe.probe_class.value == "sensitivity"]
        self.assertTrue(sen)
        self.assertTrue(all(pair.relation_held for pair in sen))
        self.assertEqual(profile.verdict, ProfileVerdict.BOUNDARY_OK)
        self.assertFalse(
            any(
                item.type in {FindingType.FALSE_ACCEPTANCE, FindingType.FALSE_REJECTION}
                for item in profile.findings
            )
        )


if __name__ == "__main__":
    unittest.main()
