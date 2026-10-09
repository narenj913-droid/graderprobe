"""Map paired verdicts onto findings. No finding exists without a pair."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from graderprobe.types import (
    ExpectedRelation,
    FindingType,
    ProbeClass,
    ProbeSpec,
    Severity,
    Verdict,
    is_evaluative,
)


@dataclass
class Finding:
    id: str
    type: FindingType
    severity: Severity
    probe_id: str
    summary: str
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "severity": self.severity.value,
            "probe_id": self.probe_id,
            "summary": self.summary,
            "evidence": self.evidence,
        }


def classify_pair(
    *,
    probe: ProbeSpec,
    baseline: Verdict,
    actual: Verdict,
    pair_id: str,
    original_behavior: Any = None,
    transformed_behavior: Any = None,
    evidence_level: Any = None,
) -> Finding:
    evidence = {
        "baseline": baseline.value,
        "mutant": actual.value,
        "expected_relation": probe.expected_relation.value,
        "transformation": probe.transform.kind,
        "description": probe.description,
        "probe_class": probe.probe_class.value,
        "method": probe.method.value,
        "target": probe.target,
        "evidence_level": getattr(evidence_level, "value", str(evidence_level or "UNVALIDATED")),
    }
    if original_behavior is not None:
        evidence["original_behavior_verdict"] = original_behavior.verdict.value
    if transformed_behavior is not None:
        evidence["transformed_behavior_verdict"] = transformed_behavior.verdict.value

    if actual in {Verdict.ERROR, Verdict.TIMEOUT}:
        return Finding(
            id=pair_id, type=FindingType.EXECUTION_ERROR, severity=Severity.MEDIUM,
            probe_id=probe.id, summary=f"{probe.id}: probe execution {actual.value}", evidence=evidence
        )
    if actual is Verdict.INCONCLUSIVE or baseline is Verdict.INCONCLUSIVE:
        return Finding(
            id=pair_id, type=FindingType.INCONCLUSIVE, severity=Severity.LOW,
            probe_id=probe.id, summary=f"{probe.id}: inconclusive verdict pair {baseline.value}->{actual.value}", evidence=evidence
        )
    if not is_evaluative(baseline) or not is_evaluative(actual):
        return Finding(
            id=pair_id, type=FindingType.INCONCLUSIVE, severity=Severity.LOW,
            probe_id=probe.id, summary=f"{probe.id}: non-evaluative pair {baseline.value}->{actual.value}", evidence=evidence
        )

    behavior_known = (original_behavior is not None and transformed_behavior is not None)
    behavior_validated = False
    behavior_unreliable = False
    if behavior_known:
        behavior_values = {original_behavior.verdict, transformed_behavior.verdict}
        behavior_unreliable = any(v in {Verdict.ERROR, Verdict.TIMEOUT, Verdict.INCONCLUSIVE} for v in behavior_values)
        if not behavior_unreliable:
            behavior_validated = True

    if probe.expected_relation is ExpectedRelation.PRESERVE:
        # If the transformation actually changed independently-checked behavior,
        # we cannot blame the evaluator for a verdict change.
        if behavior_validated and transformed_behavior.verdict is Verdict.FAIL:
            return Finding(
                id=pair_id, type=FindingType.INCONCLUSIVE, severity=Severity.LOW, probe_id=probe.id,
                summary=(f"{probe.id}: invariance transformation changed validated behavior; "
                         "evaluator reaction is inconclusive"), evidence=evidence
            )
        if actual is baseline:
            return Finding(
                id=pair_id, type=FindingType.RELATION_HELD, severity=Severity.INFO, probe_id=probe.id,
                summary=f"{probe.id}: invariance held ({baseline.value})", evidence=evidence
            )
        severity = Severity.HIGH if baseline is Verdict.PASS else Severity.MEDIUM
        prefix = "confirmed false rejection" if behavior_validated and transformed_behavior.verdict is Verdict.PASS else "possible false rejection"
        return Finding(
            id=pair_id, type=FindingType.FALSE_REJECTION, severity=severity, probe_id=probe.id,
            summary=f"{probe.id}: {prefix} ({baseline.value}->{actual.value}) after {probe.description}", evidence=evidence
        )

    # INVALIDATE: baseline PASS should become FAIL. If an independent behavior
    # validator is available, it must first confirm that the transformation is
    # actually invalid; otherwise the result is only provisional.
    if baseline is Verdict.PASS and actual is Verdict.FAIL:
        if behavior_validated and transformed_behavior.verdict is Verdict.PASS:
            return Finding(
                id=pair_id, type=FindingType.INCONCLUSIVE, severity=Severity.LOW, probe_id=probe.id,
                summary=(f"{probe.id}: sensitivity transformation did not fail independent behavior validation"),
                evidence=evidence,
            )
        return Finding(
            id=pair_id, type=FindingType.RELATION_HELD, severity=Severity.INFO, probe_id=probe.id,
            summary=f"{probe.id}: sensitivity held (PASS->FAIL)", evidence=evidence
        )
    if baseline is Verdict.PASS and actual is Verdict.PASS:
        if behavior_unreliable:
            return Finding(
                id=pair_id, type=FindingType.INCONCLUSIVE, severity=Severity.LOW, probe_id=probe.id,
                summary=f"{probe.id}: sensitivity probe has unreliable behavior validation", evidence=evidence
            )
        if behavior_validated and transformed_behavior.verdict is Verdict.PASS:
            return Finding(
                id=pair_id, type=FindingType.INCONCLUSIVE, severity=Severity.LOW, probe_id=probe.id,
                summary=f"{probe.id}: sensitivity invalidation was not confirmed by independent behavior validation", evidence=evidence
            )
        return Finding(
            id=pair_id, type=FindingType.FALSE_ACCEPTANCE, severity=Severity.HIGH, probe_id=probe.id,
            summary=(f"{probe.id}: {'confirmed' if behavior_validated else 'possible'} false acceptance "
                     f"(PASS->PASS) after {probe.description}"), evidence=evidence
        )
    if baseline is Verdict.FAIL:
        return Finding(
            id=pair_id, type=FindingType.INCONCLUSIVE, severity=Severity.LOW, probe_id=probe.id,
            summary=f"{probe.id}: sensitivity probe on FAIL baseline is inconclusive", evidence=evidence
        )
    return Finding(
        id=pair_id, type=FindingType.INCONCLUSIVE, severity=Severity.LOW, probe_id=probe.id,
        summary=f"{probe.id}: unexpected pair {baseline.value}->{actual.value}", evidence=evidence
    )


def next_severity_id(kind: str, index: int) -> str:
    prefix = "FA" if kind == "false_acceptance" else "FR" if kind == "false_rejection" else "SB"
    return f"{prefix}-{index:03d}"
