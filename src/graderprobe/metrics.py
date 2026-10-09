"""Meaningful rates. No proprietary composite score is the default output."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from graderprobe.findings import Finding
from graderprobe.types import FindingType, ProbeClass


@dataclass
class BoundaryMetrics:
    invariance_executed: int
    invariance_preserved: int
    sensitivity_executed: int
    sensitivity_detected: int
    false_acceptance_count: int
    false_rejection_count: int
    inconclusive_count: int
    probe_execution_error_rate: float
    invariance_preservation_rate: float | None
    sensitivity_detection_rate: float | None
    optional_boundary_stability: float | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "invariance_executed": self.invariance_executed,
            "invariance_preserved": self.invariance_preserved,
            "sensitivity_executed": self.sensitivity_executed,
            "sensitivity_detected": self.sensitivity_detected,
            "false_acceptance_count": self.false_acceptance_count,
            "false_rejection_count": self.false_rejection_count,
            "inconclusive_count": self.inconclusive_count,
            "probe_execution_error_rate": self.probe_execution_error_rate,
            "invariance_preservation_rate": self.invariance_preservation_rate,
            "sensitivity_detection_rate": self.sensitivity_detection_rate,
            "optional_boundary_stability": self.optional_boundary_stability,
            "optional_boundary_stability_note": (
                "Optional summary only. Not a benchmark quality score. "
                "Defined as the unweighted mean of invariance preservation "
                "and sensitivity detection rates when both are defined."
            ),
        }


def rate(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return numerator / denominator


def compute_metrics(
    findings: Iterable[Finding],
    *,
    probe_classes: dict[str, ProbeClass],
) -> BoundaryMetrics:
    findings = list(findings)
    inv_exec = 0
    inv_held = 0
    sen_exec = 0
    sen_held = 0
    fa = fr = inc = err = 0
    total = 0
    for finding in findings:
        cls = probe_classes.get(finding.probe_id)
        if cls is None:
            continue
        total += 1
        if finding.type is FindingType.EXECUTION_ERROR:
            err += 1
            continue
        if finding.type is FindingType.INCONCLUSIVE:
            inc += 1
            continue
        if cls is ProbeClass.INVARIANCE:
            inv_exec += 1
            if finding.type is FindingType.RELATION_HELD:
                inv_held += 1
            elif finding.type is FindingType.FALSE_REJECTION:
                fr += 1
        elif cls is ProbeClass.SENSITIVITY:
            sen_exec += 1
            if finding.type is FindingType.RELATION_HELD:
                sen_held += 1
            elif finding.type is FindingType.FALSE_ACCEPTANCE:
                fa += 1
        if finding.type is FindingType.INCONCLUSIVE:
            inc += 1

    inv_rate = rate(inv_held, inv_exec)
    sen_rate = rate(sen_held, sen_exec)
    stability = None
    if inv_rate is not None and sen_rate is not None:
        stability = (inv_rate + sen_rate) / 2.0
    err_rate = (err / total) if total else 0.0
    return BoundaryMetrics(
        invariance_executed=inv_exec,
        invariance_preserved=inv_held,
        sensitivity_executed=sen_exec,
        sensitivity_detected=sen_held,
        false_acceptance_count=fa,
        false_rejection_count=fr,
        inconclusive_count=inc,
        probe_execution_error_rate=err_rate,
        invariance_preservation_rate=inv_rate,
        sensitivity_detection_rate=sen_rate,
        optional_boundary_stability=stability,
    )


def wilson_interval(successes: int, n: int, z: float = 1.96) -> tuple[float, float] | None:
    """Wilson score interval. Only used when n is large enough to be honest."""
    if n < 30:
        return None
    p = successes / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = (z / denom) * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5)
    return (max(0.0, centre - half), min(1.0, centre + half))
