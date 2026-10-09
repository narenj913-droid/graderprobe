"""Non-cryptographic evidence manifest.

This is not a new cryptographic standard. It records SHA-256 hashes of the
artifacts that produced a profile so a later reader can answer: what exactly
was executed? It does not prove that an evaluator is correct.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from graderprobe import __version__
from graderprobe.hashes import hash_tree, merkle_like, sha256_file, sha256_json, sha256_text
from graderprobe.profile import BoundaryIntegrityProfile
from graderprobe.types import TaskSpec


def build_certificate(
    task: TaskSpec,
    profile: BoundaryIntegrityProfile,
    *,
    result_path: Path | None = None,
) -> dict[str, Any]:
    source = Path(task.source_path)
    files = hash_tree(source)
    result_hash = sha256_file(result_path) if result_path and result_path.is_file() else sha256_json(profile.to_dict())
    return {
        "schema": "graderprobe.certificate.v1",
        "disclaimer": (
            "This manifest records hashes of artifacts that were executed. "
            "It is not a cryptographic proof of evaluator correctness and "
            "does not use a novel signature standard."
        ),
        "created_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "graderprobe_version": __version__,
        "task_id": task.id,
        "profile_verdict": profile.verdict.value,
        "hashes": {
            "task_tree": files,
            "task_tree_digest": merkle_like(files),
            "task_id": sha256_text(task.id),
            "evaluator_contract": sha256_json({
                "command": task.evaluator.command,
                "working_dir": task.evaluator.working_dir,
                "timeout_seconds": task.evaluator.timeout_seconds,
                "pass_exit_codes": task.evaluator.pass_exit_codes,
                "fail_exit_codes": task.evaluator.fail_exit_codes,
                "inconclusive_exit_codes": task.evaluator.inconclusive_exit_codes,
                "verdict_protocol": task.evaluator.verdict_protocol,
                "environment": task.evaluator.environment,
                "network": task.evaluator.network,
                "backend": task.evaluator.backend,
                "container_image": task.evaluator.container_image,
                "container_network": task.evaluator.container_network,
                "container_memory": task.evaluator.container_memory,
                "container_cpus": task.evaluator.container_cpus,
            }),
            "behavior_validator_contract": (
                None if task.behavior_validator is None
                else sha256_json({
                    "command": task.behavior_validator.command,
                    "working_dir": task.behavior_validator.working_dir,
                    "timeout_seconds": task.behavior_validator.timeout_seconds,
                    "verdict_protocol": task.behavior_validator.verdict_protocol,
                    "network": task.behavior_validator.network,
                    "backend": task.behavior_validator.backend,
                    "container_image": task.behavior_validator.container_image,
                    "container_network": task.behavior_validator.container_network,
                })
            ),
            "probe_ids": sha256_json([p.id for p in task.all_probes()]),
            "probe_catalog": sha256_json([
                {
                    "id": p.id,
                    "class": p.probe_class.value,
                    "method": p.method.value,
                    "transform": p.transform.kind,
                    "params": p.transform.params,
                }
                for p in task.all_probes()
            ]),
            "result": result_hash,
            "environment": sha256_json(profile.environment),
        },
        "environment": profile.environment,
    }


def write_certificate(
    task: TaskSpec,
    profile: BoundaryIntegrityProfile,
    path: str | Path,
    *,
    result_path: Path | None = None,
) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    cert = build_certificate(task, profile, result_path=result_path)
    path.write_text(json.dumps(cert, indent=2) + "\n", encoding="utf-8")
    return path
