"""Paired counterfactual evidence. The pair itself is the evidence."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from graderprobe.findings import Finding, classify_pair
from graderprobe.hashes import sha256_text
from graderprobe.types import (
    ExecutionResult,
    ExpectedRelation,
    ProbeSpec,
    Verdict,
    EvidenceLevel,
)


@dataclass
class PairEvidence:
    pair_id: str
    probe: ProbeSpec
    original_candidate: str
    transformed_candidate: str
    transformation_description: str
    expected_relation: ExpectedRelation
    baseline_verdict: Verdict
    actual_verdict: Verdict
    relation_held: bool
    finding: Finding
    baseline_execution: ExecutionResult
    probe_execution: ExecutionResult
    original_hash: str
    transformed_hash: str
    original_behavior: ExecutionResult | None = None
    transformed_behavior: ExecutionResult | None = None
    evidence_level: EvidenceLevel = EvidenceLevel.UNVALIDATED
    minimal_counterfactual: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "pair_id": self.pair_id,
            "probe_id": self.probe.id,
            "probe_class": self.probe.probe_class.value,
            "method": self.probe.method.value,
            "transformation": {
                "kind": self.probe.transform.kind,
                "params": self.probe.transform.params,
                "description": self.transformation_description,
            },
            "expected_relation": self.expected_relation.value,
            "baseline_verdict": self.baseline_verdict.value,
            "actual_verdict": self.actual_verdict.value,
            "relation_held": self.relation_held,
            "finding": self.finding.to_dict(),
            "original_hash": self.original_hash,
            "transformed_hash": self.transformed_hash,
            "evidence": {
                "level": self.evidence_level.value,
                "original_behavior": None if self.original_behavior is None else self.original_behavior.to_dict(),
                "transformed_behavior": None if self.transformed_behavior is None else self.transformed_behavior.to_dict(),
                "minimal_counterfactual": self.minimal_counterfactual,
            },
            "original_candidate": self.original_candidate,
            "transformed_candidate": self.transformed_candidate,
            "baseline_execution": self.baseline_execution.to_dict(),
            "probe_execution": self.probe_execution.to_dict(),
        }


def build_pair(
    *,
    index: int,
    probe: ProbeSpec,
    original: str,
    transformed: str,
    baseline_verdict: Verdict,
    baseline_execution: ExecutionResult,
    probe_execution: ExecutionResult,
    original_behavior: ExecutionResult | None = None,
    transformed_behavior: ExecutionResult | None = None,
    evidence_level: EvidenceLevel = EvidenceLevel.UNVALIDATED,
    minimal_counterfactual: dict[str, Any] | None = None,
) -> PairEvidence:
    pair_id = f"PAIR-{index:03d}"
    finding = classify_pair(
        probe=probe,
        baseline=baseline_verdict,
        actual=probe_execution.verdict,
        pair_id=pair_id,
        original_behavior=original_behavior,
        transformed_behavior=transformed_behavior,
        evidence_level=evidence_level,
    )
    held = finding.type.value == "relation_held"
    return PairEvidence(
        pair_id=pair_id,
        probe=probe,
        original_candidate=original,
        transformed_candidate=transformed,
        transformation_description=probe.description,
        expected_relation=probe.expected_relation,
        baseline_verdict=baseline_verdict,
        actual_verdict=probe_execution.verdict,
        relation_held=held,
        finding=finding,
        baseline_execution=baseline_execution,
        probe_execution=probe_execution,
        original_hash=sha256_text(original),
        transformed_hash=sha256_text(transformed),
        original_behavior=original_behavior,
        transformed_behavior=transformed_behavior,
        evidence_level=evidence_level,
        minimal_counterfactual=minimal_counterfactual,
    )
