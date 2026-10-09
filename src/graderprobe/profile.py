"""Boundary Integrity Profile assembly."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from graderprobe.baseline import BaselineReport
from graderprobe.evidence import PairEvidence
from graderprobe.findings import Finding
from graderprobe.metrics import BoundaryMetrics, compute_metrics
from graderprobe.types import FindingType, ProfileVerdict, Severity, TaskSpec


@dataclass
class BoundaryIntegrityProfile:
    task_id: str
    task_title: str
    baseline: BaselineReport
    pairs: list[PairEvidence]
    metrics: BoundaryMetrics
    findings: list[Finding]
    verdict: ProfileVerdict
    notes: list[str] = field(default_factory=list)
    environment: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "graderprobe.boundary_integrity_profile.v1",
            "task_id": self.task_id,
            "task_title": self.task_title,
            "baseline": self.baseline.to_dict(),
            "metrics": self.metrics.to_dict(),
            "verdict": self.verdict.value,
            "findings": [item.to_dict() for item in self.findings],
            "pairs": [item.to_dict() for item in self.pairs],
            "notes": self.notes,
            "environment": self.environment,
        }


def assemble_profile(
    task: TaskSpec,
    baseline: BaselineReport,
    pairs: list[PairEvidence],
    *,
    environment: dict[str, Any] | None = None,
    notes: list[str] | None = None,
) -> BoundaryIntegrityProfile:
    if not baseline.ok:
        empty = compute_metrics([], probe_classes={})
        return BoundaryIntegrityProfile(
            task_id=task.id,
            task_title=task.title,
            baseline=baseline,
            pairs=[],
            metrics=empty,
            findings=[
                Finding(
                    id="BASELINE",
                    type=FindingType.BASELINE_INVALID,
                    severity=Severity.HIGH,
                    probe_id="baseline",
                    summary=baseline.reason,
                    evidence={"reason": baseline.reason},
                )
            ],
            verdict=ProfileVerdict.BASELINE_INVALID,
            notes=notes or [],
            environment=environment or {},
        )

    probe_classes = {pair.probe.id: pair.probe.probe_class for pair in pairs}
    findings = [pair.finding for pair in pairs]
    metrics = compute_metrics(findings, probe_classes=probe_classes)
    notable = [
        item
        for item in findings
        if item.type in {FindingType.FALSE_ACCEPTANCE, FindingType.FALSE_REJECTION}
    ]
    return BoundaryIntegrityProfile(
        task_id=task.id,
        task_title=task.title,
        baseline=baseline,
        pairs=pairs,
        metrics=metrics,
        findings=findings,
        verdict=_profile_verdict(metrics, notable, findings),
        notes=notes or [],
        environment=environment or {},
    )


def _profile_verdict(
    metrics: BoundaryMetrics,
    notable: list[Finding],
    findings: list[Finding],
) -> ProfileVerdict:
    high = [item for item in notable if item.severity is Severity.HIGH]
    if high:
        return ProfileVerdict.BOUNDARY_FAIL
    if notable:
        return ProfileVerdict.BOUNDARY_WARNING
    evaluated = metrics.invariance_executed + metrics.sensitivity_executed
    if evaluated == 0:
        return ProfileVerdict.INCONCLUSIVE
    return ProfileVerdict.BOUNDARY_OK
