from __future__ import annotations

import unittest
from pathlib import Path

from graderprobe.probes.minimize import minimize_by_diff_hunks
from graderprobe.runner import RunConfig, run_task
from graderprobe.task import load_task
from graderprobe.types import EvidenceLevel, FindingType, ProfileVerdict


ROOT = Path(__file__).resolve().parents[1] / "corpus" / "tasks"


class Stage2BehaviorTests(unittest.TestCase):
    def test_healthy_invariance_gets_smoke_evidence(self) -> None:
        profile = run_task(
            load_task(ROOT / "healthy-control" / "task.yaml"),
            config=RunConfig(validate_behavior=True, validate_behavior_all=True),
        )
        invariance = [p for p in profile.pairs if p.probe.probe_class.value == "invariance"]
        self.assertTrue(invariance)
        self.assertTrue(all(p.evidence_level is EvidenceLevel.SMOKE_VALIDATED for p in invariance))
        self.assertTrue(all(p.relation_held for p in invariance))

    def test_false_acceptance_is_strengthened_by_behavior_validation(self) -> None:
        profile = run_task(
            load_task(ROOT / "under-constrained-auth" / "task.yaml"),
            config=RunConfig(validate_behavior=True),
        )
        findings = [p for p in profile.pairs if p.finding.type is FindingType.FALSE_ACCEPTANCE]
        self.assertEqual(len(findings), 2)
        self.assertTrue(all(p.evidence_level is EvidenceLevel.SMOKE_VALIDATED for p in findings))
        self.assertTrue(all("confirmed false acceptance" in p.finding.summary for p in findings))
        self.assertEqual(profile.verdict, ProfileVerdict.BOUNDARY_FAIL)

    def test_false_rejection_is_validated_as_behavior_preserving(self) -> None:
        profile = run_task(
            load_task(ROOT / "over-strict-naming" / "task.yaml"),
            config=RunConfig(validate_behavior=True),
        )
        findings = [p for p in profile.pairs if p.finding.type is FindingType.FALSE_REJECTION]
        self.assertTrue(findings)
        self.assertTrue(any("confirmed false rejection" in p.finding.summary for p in findings))

    def test_minimizer_finds_smaller_preserving_counterfactual(self) -> None:
        original = "x = 0\ny = 0\nz = 0\n"
        transformed = "x = 0\ny = 1\nz = 2\n"
        calls = []

        def predicate(candidate: str) -> bool:
            calls.append(candidate)
            return "y = 1" in candidate and "z = 2" not in candidate

        result = minimize_by_diff_hunks(original, transformed, predicate, budget=12)
        self.assertIsNotNone(result)
        assert result is not None
        self.assertIn("y = 1", result.minimized)
        self.assertNotIn("z = 2", result.minimized)
        self.assertGreaterEqual(result.attempts, 1)


    def test_lazy_validation_skips_clean_pairs(self) -> None:
        profile = run_task(
            load_task(ROOT / "healthy-control" / "task.yaml"),
            config=RunConfig(validate_behavior=True, validate_behavior_all=False),
        )
        self.assertTrue(all(p.transformed_behavior is None for p in profile.pairs))

    def test_auto_sensitivity_requires_behavior_validator_in_runner(self) -> None:
        task = load_task(ROOT / "healthy-control" / "task.yaml")
        profile = run_task(
            task,
            config=RunConfig(include_auto_probes=True, include_auto_sensitivity=True, validate_behavior=True, validate_behavior_all=True),
        )
        auto = [p for p in profile.pairs if p.probe.id.startswith("AUTO-")]
        self.assertTrue(auto)
        auto_sensitive = [p for p in auto if p.probe.probe_class.value == "sensitivity"]
        self.assertTrue(auto_sensitive)
        self.assertTrue(all(p.evidence_level is EvidenceLevel.SMOKE_VALIDATED for p in auto))


if __name__ == "__main__":
    unittest.main()
