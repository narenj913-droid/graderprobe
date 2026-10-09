"""Markdown report with evidence for every finding."""

from __future__ import annotations

from graderprobe.profile import BoundaryIntegrityProfile
from graderprobe.types import FindingType


def render_markdown(profile: BoundaryIntegrityProfile) -> str:
    m = profile.metrics
    parts = [
        f"# Boundary Integrity Profile — `{profile.task_id}`",
        "",
        f"**Title:** {profile.task_title}",
        "",
        f"**Profile verdict:** `{profile.verdict.value}`",
        "",
        "## Baseline",
        "",
        f"- Result: `{profile.baseline.verdict.value}`",
        f"- Accepted: `{profile.baseline.ok}`",
        f"- Reason: {profile.baseline.reason}",
        "",
    ]
    if not profile.baseline.ok:
        parts += [
            "> Baseline validation failed. No boundary score is reported.",
            "",
            "Passing boundary tests does not prove an evaluator is correct.",
            "",
        ]
        return "\n".join(parts)

    parts += [
        "## Metrics",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Invariance preserved | {m.invariance_preserved}/{m.invariance_executed} |",
        f"| Sensitivity detected | {m.sensitivity_detected}/{m.sensitivity_executed} |",
        f"| False acceptance count | {m.false_acceptance_count} |",
        f"| False rejection count | {m.false_rejection_count} |",
        f"| Inconclusive count | {m.inconclusive_count} |",
        f"| Probe execution error rate | {m.probe_execution_error_rate:.3f} |",
        "",
        "_Rates are proportions on this task's executed probes. "
        "They are not a general benchmark quality score._",
        "",
        "## Findings",
        "",
    ]
    notable = [
        f
        for f in profile.findings
        if f.type is not FindingType.RELATION_HELD
    ]
    if not notable:
        parts.append("No defect candidates. This is not a proof of evaluator correctness.")
        parts.append("")
    for item in notable:
        ev = item.evidence
        parts += [
            f"### {item.id} — {item.type.value} ({item.severity.value})",
            "",
            item.summary,
            "",
            "```yaml",
            f"probe: {item.probe_id}",
            f"baseline: {ev.get('baseline')}",
            f"mutant: {ev.get('mutant')}",
            f"expected_relation: {ev.get('expected_relation')}",
            f"transformation: {ev.get('transformation')}",
            "```",
            "",
        ]
    parts += ["## Pairs", ""]
    for pair in profile.pairs:
        parts += [
            f"### {pair.pair_id} (`{pair.probe.id}`)",
            "",
            f"- Class: `{pair.probe.probe_class.value}`",
            f"- Transformation: {pair.transformation_description}",
            f"- Expected: `{pair.expected_relation.value}`",
            f"- Actual: `{pair.baseline_verdict.value}` → `{pair.actual_verdict.value}`",
            f"- Relation held: `{pair.relation_held}`",
            f"- Evidence level: `{pair.evidence_level.value}`",
            f"- Behavior: `{pair.original_behavior.verdict.value if pair.original_behavior else 'UNVALIDATED'}` → `{pair.transformed_behavior.verdict.value if pair.transformed_behavior else 'UNVALIDATED'}`",
            f"- Minimal counterfactual: `{'yes' if pair.minimal_counterfactual else 'no'}`",
            f"- Original hash: `{pair.original_hash[:12]}`",
            f"- Transformed hash: `{pair.transformed_hash[:12]}`",
            "",
        ]
    parts += [
        "## Limitation",
        "",
        "Passing Boundary Tests does not prove an evaluator is correct.",
        "",
    ]
    return "\n".join(parts)
