"""Demo findings must arise from actual execution, not canned tables."""

from __future__ import annotations

import unittest

from graderprobe.corpus import corpus_dir, load_corpus
from graderprobe.runner import run_task
from graderprobe.types import FindingType, ProfileVerdict, Verdict


class DemoCorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profiles = {task.id: run_task(task) for task in load_corpus()}

    def test_over_strict_false_rejection(self) -> None:
        profile = self.profiles["over-strict-naming"]
        self.assertTrue(profile.baseline.ok)
        types = {pair.probe.id: pair.finding.type for pair in profile.pairs}
        self.assertEqual(types["INV-01"], FindingType.FALSE_REJECTION)

    def test_under_constrained_false_acceptance(self) -> None:
        profile = self.profiles["under-constrained-auth"]
        types = {pair.probe.id: pair.finding.type for pair in profile.pairs}
        self.assertEqual(types["SEN-01"], FindingType.FALSE_ACCEPTANCE)

    def test_implementation_specific_rejects_builtin(self) -> None:
        profile = self.profiles["implementation-specific-sort"]
        types = {pair.probe.id: pair.finding.type for pair in profile.pairs}
        self.assertEqual(types["INV-01"], FindingType.FALSE_REJECTION)

    def test_edge_case_blind_accepts_zero_on_empty(self) -> None:
        profile = self.profiles["edge-case-blind"]
        types = {pair.probe.id: pair.finding.type for pair in profile.pairs}
        self.assertEqual(types["SEN-01"], FindingType.FALSE_ACCEPTANCE)

    def test_wrong_side_boundary(self) -> None:
        profile = self.profiles["wrong-side-boundary"]
        types = {pair.probe.id: pair.finding.type for pair in profile.pairs}
        self.assertEqual(types["SEN-01"], FindingType.FALSE_ACCEPTANCE)

    def test_formatting_sensitive(self) -> None:
        profile = self.profiles["formatting-sensitive"]
        types = {pair.probe.id: pair.finding.type for pair in profile.pairs}
        self.assertEqual(types["INV-01"], FindingType.FALSE_REJECTION)

    def test_alt_algorithm_rejected(self) -> None:
        profile = self.profiles["alt-algorithm-reject"]
        types = {pair.probe.id: pair.finding.type for pair in profile.pairs}
        self.assertEqual(types["INV-01"], FindingType.FALSE_REJECTION)

    def test_missing_required_behavior(self) -> None:
        profile = self.profiles["missing-required-behavior"]
        types = {pair.probe.id: pair.finding.type for pair in profile.pairs}
        self.assertEqual(types["SEN-01"], FindingType.FALSE_ACCEPTANCE)

    def test_insecure_accepted(self) -> None:
        profile = self.profiles["insecure-accepted"]
        types = {pair.probe.id: pair.finding.type for pair in profile.pairs}
        self.assertEqual(types["SEN-01"], FindingType.FALSE_ACCEPTANCE)

    def test_wrong_state_transition(self) -> None:
        profile = self.profiles["wrong-state-transition"]
        types = {pair.probe.id: pair.finding.type for pair in profile.pairs}
        self.assertEqual(types["SEN-01"], FindingType.FALSE_ACCEPTANCE)

    def test_refactor_rejected(self) -> None:
        profile = self.profiles["refactor-rejected"]
        types = {pair.probe.id: pair.finding.type for pair in profile.pairs}
        self.assertEqual(types["INV-01"], FindingType.FALSE_REJECTION)

    def test_nondeterministic_baseline_invalid(self) -> None:
        profile = self.profiles["nondeterministic-eval"]
        self.assertEqual(profile.verdict, ProfileVerdict.BASELINE_INVALID)
        self.assertIn("non-deterministic", profile.baseline.reason)

    def test_broken_environment_baseline_invalid(self) -> None:
        profile = self.profiles["broken-environment"]
        self.assertEqual(profile.verdict, ProfileVerdict.BASELINE_INVALID)
        self.assertIn(profile.baseline.runs[0].verdict, {Verdict.ERROR})

    def test_misleading_nl_baseline_invalid(self) -> None:
        profile = self.profiles["misleading-nl"]
        self.assertEqual(profile.verdict, ProfileVerdict.BASELINE_INVALID)
        self.assertEqual(profile.baseline.runs[0].verdict, Verdict.FAIL)

    def test_ambiguous_inconclusive(self) -> None:
        profile = self.profiles["ambiguous-requirement"]
        self.assertTrue(profile.baseline.ok)
        self.assertEqual(profile.baseline.verdict, Verdict.INCONCLUSIVE)
        self.assertEqual(profile.verdict, ProfileVerdict.INCONCLUSIVE)

    def test_healthy_ok(self) -> None:
        profile = self.profiles["healthy-control"]
        self.assertEqual(profile.verdict, ProfileVerdict.BOUNDARY_OK)

    def test_no_score_when_baseline_invalid(self) -> None:
        profile = self.profiles["broken-environment"]
        self.assertIsNone(profile.metrics.invariance_preservation_rate)
        self.assertEqual(profile.pairs, [])

    def test_corpus_dir_exists(self) -> None:
        self.assertTrue(corpus_dir().is_dir())


if __name__ == "__main__":
    unittest.main()
