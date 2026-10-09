"""Reproducibility and replay bundles.

A replay bundle is a local, human-readable manifest. It deliberately separates
input-integrity verification from evaluator correctness: a replay confirms the
same task tree and execution configuration were used, then re-runs the audit
and compares a semantic outcome fingerprint.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from graderprobe import __version__
from graderprobe.hashes import hash_tree, merkle_like, sha256_file, sha256_json
from graderprobe.profile import BoundaryIntegrityProfile
from graderprobe.runner import RunConfig, run_task
from graderprobe.task import load_task


def outcome_fingerprint(profile: BoundaryIntegrityProfile) -> str:
    payload = {
        "schema": profile.to_dict()["schema"],
        "task_id": profile.task_id,
        "verdict": profile.verdict.value,
        "metrics": profile.metrics.to_dict(),
        "findings": [
            {
                "id": f.id,
                "type": f.type.value,
                "severity": f.severity.value,
                "probe_id": f.probe_id,
                "summary": f.summary,
            }
            for f in profile.findings
        ],
        "pairs": [
            {
                "pair_id": p.pair_id,
                "probe_id": p.probe.id,
                "expected_relation": p.expected_relation.value,
                "actual_verdict": p.actual_verdict.value,
                "relation_held": p.relation_held,
                "evidence_level": p.evidence_level.value,
            }
            for p in profile.pairs
        ],
    }
    return sha256_json(payload)


def build_replay_manifest(task: Any, profile: BoundaryIntegrityProfile, profile_path: Path, config: RunConfig, task_file: Path | None = None) -> dict[str, Any]:
    source = Path(task.source_path).resolve()
    files = hash_tree(source)
    task_file = (task_file or (source / "task.yaml")).resolve()
    return {
        "schema": "graderprobe.replay_bundle.v1",
        "graderprobe_version": __version__,
        "task_id": task.id,
        "task_file": str(task_file),
        "source_root": str(source),
        "source_tree_digest": merkle_like(files),
        "task_file_sha256": sha256_file(task_file) if task_file.is_file() else None,
        "profile_path": str(Path(profile_path).resolve()),
        "profile_sha256": sha256_file(profile_path) if profile_path.is_file() else None,
        "outcome_fingerprint": outcome_fingerprint(profile),
        "model_probes": [
            {
                "id": p.probe.id,
                "probe_class": p.probe.probe_class.value,
                "description": p.probe.description,
                "expected_relation": p.probe.expected_relation.value,
                "transform": {"kind": p.probe.transform.kind, "params": p.probe.transform.params},
                "method": p.probe.method.value,
                "target": p.probe.target,
                "notes": p.probe.notes,
            }
            for p in profile.pairs if p.probe.method.value == "MODEL_GENERATED"
        ],
        "config": {
            "include_auto_probes": config.include_auto_probes,
            "include_auto_sensitivity": config.include_auto_sensitivity,
            "validate_behavior": config.validate_behavior,
            "validate_behavior_all": config.validate_behavior_all,
            "minimize_counterfactuals": config.minimize_counterfactuals,
            "max_minimization_runs": config.max_minimization_runs,
            "seed": config.seed,
            "inherit_secrets": config.inherit_secrets,
            "max_workers": config.max_workers,
            "validate_invariance_behavior": config.validate_invariance_behavior,
            "memoize_minimization": config.memoize_minimization,
            "baseline_repeats_override": config.baseline_repeats_override,
            "execution_slots": config.execution_slots,
            "include_model_probes": config.include_model_probes,
            "max_model_proposals": config.max_model_proposals,
        },
    }


def write_replay_manifest(task: Any, profile: BoundaryIntegrityProfile, profile_path: Path, config: RunConfig, path: Path, task_file: Path | None = None) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    manifest = build_replay_manifest(task, profile, profile_path, config, task_file=task_file)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def replay_bundle(bundle_path: str | Path, *, out_dir: str | Path | None = None, allow_source_drift: bool = False) -> dict[str, Any]:
    bundle = Path(bundle_path).resolve()
    manifest = json.loads(bundle.read_text(encoding="utf-8"))
    if manifest.get("schema") != "graderprobe.replay_bundle.v1":
        raise ValueError("unsupported replay bundle schema")
    task_file = Path(str(manifest["task_file"])).resolve()
    source_root = Path(str(manifest["source_root"])).resolve()
    if not task_file.is_file() or not source_root.is_dir():
        raise FileNotFoundError("replay source/task is no longer available")
    current_digest = merkle_like(hash_tree(source_root))
    expected_digest = str(manifest.get("source_tree_digest"))
    if not allow_source_drift and current_digest != expected_digest:
        raise ValueError(
            "source tree changed since the recorded run; use --allow-source-drift "
            "only when intentional"
        )
    raw = manifest.get("config") or {}
    config_values = {k: v for k, v in raw.items() if k in RunConfig.__dataclass_fields__}
    config_values["include_model_probes"] = False
    config_values["model_provider"] = None
    config_values["replay_probes"] = list(manifest.get("model_probes") or [])
    config = RunConfig(**config_values)
    task = load_task(task_file)
    profile = run_task(task, config=config)
    actual = outcome_fingerprint(profile)
    expected = str(manifest["outcome_fingerprint"])
    return {
        "matched": actual == expected,
        "expected_fingerprint": expected,
        "actual_fingerprint": actual,
        "task_id": task.id,
        "verdict": profile.verdict.value,
        "source_tree_digest": current_digest,
        "drift_allowed": allow_source_drift,
        "profile": profile,
        "out_dir": None if out_dir is None else str(Path(out_dir).resolve()),
    }
