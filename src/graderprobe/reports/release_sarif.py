"""SARIF export for change-aware release assurance results."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from graderprobe import __version__
from graderprobe.assurance import ReleaseAssuranceReport

SARIF_VERSION = "2.1.0"
SARIF_SCHEMA = "https://json.schemastore.org/sarif-2.1.0.json"


def release_to_sarif(report: ReleaseAssuranceReport) -> dict[str, Any]:
    rules: dict[str, dict[str, Any]] = {}
    results: list[dict[str, Any]] = []

    def add_result(rule_id: str, level: str, message: str, path: str | None, props: dict[str, Any]) -> None:
        rules.setdefault(
            rule_id,
            {
                "id": rule_id,
                "name": rule_id.rsplit("/", 1)[-1],
                "shortDescription": {"text": message[:120]},
            },
        )
        result: dict[str, Any] = {
            "ruleId": rule_id,
            "level": level,
            "message": {"text": message},
            "properties": props,
        }
        if path:
            result["locations"] = [{"physicalLocation": {"artifactLocation": {"uri": path}}}]
        results.append(result)

    if report.deleted_task_paths:
        for path in report.deleted_task_paths:
            add_result(
                "graderprobe/release-task-removed",
                "warning",
                f"Benchmark task removed in release: {path}",
                path,
                {"kind": "deleted_task"},
            )

    for item in report.comparisons:
        if item.decision == "BLOCK":
            level = "error"
            rule = "graderprobe/release-regression"
        elif item.decision == "WARN":
            level = "warning"
            rule = "graderprobe/release-warning"
        else:
            continue
        message = (
            f"{item.task_id}: {item.decision}; base={item.base_verdict}, "
            f"head={item.head_verdict}, comparability={item.comparability}, "
            f"false_acceptance_delta={item.false_acceptance_delta}, "
            f"false_rejection_delta={item.false_rejection_delta}"
        )
        add_result(
            rule,
            level,
            message,
            item.task_path,
            {
                "taskId": item.task_id,
                "driftSeverity": item.drift_severity,
                "comparability": item.comparability,
                "commonProbeCount": item.common_probe_count,
                "probeSetDelta": item.probe_set_delta,
                "requiredChecks": list(item.required_checks),
                "baseCohortId": item.base_cohort_id,
                "headCohortId": item.head_cohort_id,
            },
        )

    if report.decision == "BLOCK" and not results:
        add_result(
            "graderprobe/release-regression",
            "error",
            "Release assurance blocked the release.",
            None,
            {"releaseFingerprint": report.release_fingerprint},
        )

    return {
        "$schema": SARIF_SCHEMA,
        "version": SARIF_VERSION,
        "runs": [
            {
                "tool": {"driver": {"name": "GraderProbe Release Assurance", "version": __version__, "rules": list(rules.values())}},
                "results": results,
                "properties": {
                    "releaseDecision": report.decision,
                    "baseRef": report.base_ref,
                    "headRef": report.head_ref,
                    "baseCommit": report.base_commit,
                    "headCommit": report.head_commit,
                    "releaseFingerprint": report.release_fingerprint,
                },
            }
        ],
    }


def write_release_sarif(report: ReleaseAssuranceReport, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(release_to_sarif(report), indent=2) + "\n", encoding="utf-8")
    return path
