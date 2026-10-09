from __future__ import annotations

import unittest

from graderprobe.findings import classify_pair
from graderprobe.types import (
    ExpectedRelation,
    FindingType,
    ProbeClass,
    ProbeSpec,
    TransformSpec,
    Verdict,
)


def _probe(cls: ProbeClass, relation: ExpectedRelation) -> ProbeSpec:
    return ProbeSpec(
        id="P",
        probe_class=cls,
        description="d",
        expected_relation=relation,
        transform=TransformSpec(kind="insert_comments"),
    )


class FindingTests(unittest.TestCase):
    def test_false_rejection(self) -> None:
        finding = classify_pair(
            probe=_probe(ProbeClass.INVARIANCE, ExpectedRelation.PRESERVE),
            baseline=Verdict.PASS,
            actual=Verdict.FAIL,
            pair_id="PAIR-001",
        )
        self.assertEqual(finding.type, FindingType.FALSE_REJECTION)

    def test_false_acceptance(self) -> None:
        finding = classify_pair(
            probe=_probe(ProbeClass.SENSITIVITY, ExpectedRelation.INVALIDATE),
            baseline=Verdict.PASS,
            actual=Verdict.PASS,
            pair_id="PAIR-002",
        )
        self.assertEqual(finding.type, FindingType.FALSE_ACCEPTANCE)

    def test_invariance_held(self) -> None:
        finding = classify_pair(
            probe=_probe(ProbeClass.INVARIANCE, ExpectedRelation.PRESERVE),
            baseline=Verdict.PASS,
            actual=Verdict.PASS,
            pair_id="PAIR-003",
        )
        self.assertEqual(finding.type, FindingType.RELATION_HELD)

    def test_sensitivity_held(self) -> None:
        finding = classify_pair(
            probe=_probe(ProbeClass.SENSITIVITY, ExpectedRelation.INVALIDATE),
            baseline=Verdict.PASS,
            actual=Verdict.FAIL,
            pair_id="PAIR-004",
        )
        self.assertEqual(finding.type, FindingType.RELATION_HELD)

    def test_error_not_fail(self) -> None:
        finding = classify_pair(
            probe=_probe(ProbeClass.SENSITIVITY, ExpectedRelation.INVALIDATE),
            baseline=Verdict.PASS,
            actual=Verdict.ERROR,
            pair_id="PAIR-005",
        )
        self.assertEqual(finding.type, FindingType.EXECUTION_ERROR)

    def test_every_finding_has_evidence(self) -> None:
        finding = classify_pair(
            probe=_probe(ProbeClass.INVARIANCE, ExpectedRelation.PRESERVE),
            baseline=Verdict.PASS,
            actual=Verdict.FAIL,
            pair_id="PAIR-006",
        )
        self.assertIn("baseline", finding.evidence)
        self.assertIn("mutant", finding.evidence)
        self.assertIn("transformation", finding.evidence)


if __name__ == "__main__":
    unittest.main()
