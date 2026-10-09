"""SARIF 2.1.0 export for GitHub code-scanning integration."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from graderprobe import __version__

SARIF_VERSION = "2.1.0"
SARIF_SCHEMA = "https://json.schemastore.org/sarif-2.1.0.json"


def profile_to_sarif(profile: dict[str, Any], *, uri_base: str = "", include_info: bool = False) -> dict[str, Any]:
    """Convert a GraderProbe profile JSON object into a compact SARIF log."""
    results: list[dict[str, Any]] = []
    rules: dict[str, dict[str, Any]] = {}
    for finding in profile.get("findings") or []:
        ftype = str(finding.get("type", "finding"))
        severity = str(finding.get("severity", "warning"))
        probe_id = str(finding.get("probe_id") or finding.get("id") or "finding")
        rule_id = f"graderprobe/{ftype}"
        rules.setdefault(
            rule_id,
            {
                "id": rule_id,
                "name": _rule_name(ftype),
                "shortDescription": {"text": _rule_name(ftype)},
            },
        )
        if ftype == "relation_held" or severity == "info":
            if not include_info:
                continue
            level = "note"
        elif severity == "high":
            level = "error"
        else:
            level = "warning"
        location = _location(finding, profile, uri_base=uri_base)
        result: dict[str, Any] = {
            "ruleId": rule_id,
            "level": level,
            "message": {"text": str(finding.get("summary") or rule_id)},
            "properties": {
                "probeId": probe_id,
                "findingType": ftype,
                "severity": severity,
            },
        }
        if location:
            result["locations"] = [location]
        results.append(result)

    return {
        "$schema": SARIF_SCHEMA,
        "version": SARIF_VERSION,
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "GraderProbe",
                        "version": __version__,
                        "rules": list(rules.values()),
                    }
                },
                "results": results,
                "properties": {
                    "taskId": profile.get("task_id"),
                    "profileVerdict": profile.get("verdict"),
                },
            }
        ],
    }


def write_sarif(profile: dict[str, Any] | str | Path, path: str | Path, *, include_info: bool = False) -> Path:
    if not isinstance(profile, dict):
        profile = json.loads(Path(profile).read_text(encoding="utf-8"))
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(profile_to_sarif(profile, include_info=include_info), indent=2) + "\n", encoding="utf-8")
    return path


def _rule_name(ftype: str) -> str:
    return f"GraderProbe {ftype.replace('_', ' ')}"


def _location(finding: dict[str, Any], profile: dict[str, Any], *, uri_base: str = "") -> dict[str, Any] | None:
    evidence = finding.get("evidence") or {}
    target = evidence.get("target")
    if not target:
        return None
    uri = str(target).replace("\\", "/")
    if uri_base:
        uri = uri_base.rstrip("/") + "/" + uri.lstrip("/")
    return {"physicalLocation": {"artifactLocation": {"uri": uri}}}


def profiles_to_sarif(profiles: list[dict[str, Any]], *, uri_base: str = "") -> dict[str, Any]:
    """Combine multiple GraderProbe profile JSON objects into one SARIF log."""
    combined = profile_to_sarif({}, uri_base=uri_base)
    run = combined["runs"][0]
    rules: dict[str, dict[str, Any]] = {}
    results: list[dict[str, Any]] = []
    for profile in profiles:
        one = profile_to_sarif(profile, uri_base=uri_base)["runs"][0]
        driver = one["tool"]["driver"]
        for rule in driver.get("rules", []):
            rules[rule["id"]] = rule
        results.extend(one.get("results", []))
    run["tool"]["driver"]["rules"] = list(rules.values())
    run["results"] = results
    return combined
