"""Compact terminal Boundary Integrity Profile."""

from __future__ import annotations

from graderprobe.profile import BoundaryIntegrityProfile
from graderprobe.types import FindingType


def render_terminal(profile: BoundaryIntegrityProfile) -> str:
    m = profile.metrics
    lines = [
        "BOUNDARY INTEGRITY PROFILE",
        f"Task: {profile.task_id}",
        f"Title: {profile.task_title}",
        "",
        "Baseline:",
        f"  {profile.baseline.verdict.value}"
        + ("" if profile.baseline.ok else f"  ({profile.baseline.reason})"),
        "",
    ]
    if not profile.baseline.ok:
        lines += [
            "Verdict: BASELINE_INVALID",
            "No boundary score is reported because baseline validation failed.",
            "",
        ]
        return "\n".join(lines)

    inv = f"{m.invariance_preserved}/{m.invariance_executed}"
    sen = f"{m.sensitivity_detected}/{m.sensitivity_executed}"
    lines += [
        "Invariance probes:",
        f"  {inv} preserved PASS/verdict",
        "Sensitivity probes:",
        f"  {sen} correctly changed to FAIL",
        "",
        f"Potential false acceptance: {m.false_acceptance_count}",
        f"Potential false rejection: {m.false_rejection_count}",
        f"Inconclusive: {m.inconclusive_count}",
        f"Probe execution error rate: {m.probe_execution_error_rate:.3f}",
    ]
    if m.optional_boundary_stability is not None:
        lines.append(
            f"Optional boundary stability: {m.optional_boundary_stability:.1%} "
            "(mean of invariance preservation and sensitivity detection; not a quality score)"
        )
    lines += ["", "Findings:"]
    notable = [
        f
        for f in profile.findings
        if f.type in {FindingType.FALSE_ACCEPTANCE, FindingType.FALSE_REJECTION, FindingType.BASELINE_INVALID}
    ]
    if not notable:
        lines.append("  none")
    for item in notable:
        lines.append(f"  {item.probe_id}  {item.severity.value.upper()}")
        lines.append(f"    {item.summary}")
    lines += ["", f"Verdict: {profile.verdict.value}", ""]
    return "\n".join(lines)
