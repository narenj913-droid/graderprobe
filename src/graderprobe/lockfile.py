"""Persistent evaluation-contract lock and verification.

A lockfile makes the benchmark/evaluator contract explicit in source control.
It does not freeze legitimate changes; instead it turns them into an explicit
maintainer decision by pairing contract digests with the existing release audit.
"""
from __future__ import annotations

import json
import subprocess
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from graderprobe import __version__
from graderprobe.assurance import _cohort_id, _resolve_ref, _task_digest, release_assurance
from graderprobe.hashes import sha256_file, sha256_json
from graderprobe.runner import RunConfig, run_task
from graderprobe.task import load_task

LOCK_SCHEMA = "graderprobe.contract_lock.v1"


def _git_status_clean(repo: Path) -> bool:
    proc = subprocess.run(["git", "-C", str(repo), "status", "--porcelain"], capture_output=True, text=True, check=False, timeout=20)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "git status failed")
    return not proc.stdout.strip()


def _task_inventory(task_root: Path, repo: Path) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for path in sorted(task_root.rglob("task.yaml")):
        task = load_task(path)
        digest = _task_digest(path.parent)
        cohort = _cohort_id(digest, task)
        items.append(
            {
                "id": task.id,
                "path": path.relative_to(repo).as_posix(),
                "digest": digest,
                "cohort_id": cohort,
                "probe_ids": [p.id for p in task.all_probes()],
                "probe_set_digest": sha256_json([
                    {
                        "id": p.id,
                        "class": p.probe_class.value,
                        "relation": p.expected_relation.value,
                        "method": p.method.value,
                        "transform": {"kind": p.transform.kind, "params": p.transform.params},
                    }
                    for p in task.all_probes()
                ]),
                "evaluator_contract": {
                    "command": list(task.evaluator.command),
                    "working_dir": task.evaluator.working_dir,
                    "timeout_seconds": task.evaluator.timeout_seconds,
                    "verdict_protocol": task.evaluator.verdict_protocol,
                    "pass_exit_codes": list(task.evaluator.pass_exit_codes),
                    "fail_exit_codes": list(task.evaluator.fail_exit_codes),
                    "inconclusive_exit_codes": list(task.evaluator.inconclusive_exit_codes),
                    "backend": task.evaluator.backend,
                    "network": task.evaluator.network,
                    "container_image": task.evaluator.container_image,
                },
            }
        )
    return items


def create_lock(
    repo: str | Path,
    *,
    task_root: str | Path,
    out: str | Path,
    anchor_count: int = 0,
    config: RunConfig | None = None,
) -> dict[str, Any]:
    root = Path(repo).resolve()
    task_root_path = Path(task_root).resolve()
    if not task_root_path.is_dir():
        raise ValueError(f"task root does not exist: {task_root_path}")
    if not _git_status_clean(root):
        raise RuntimeError("working tree is dirty; create a lock from a clean Git revision")
    commit = _resolve_ref(root, "HEAD")
    if not commit:
        raise RuntimeError("unable to resolve HEAD")
    inventory = _task_inventory(task_root_path, root)
    anchors: list[dict[str, Any]] = []
    if anchor_count > 0:
        cfg = config or RunConfig(max_workers=1, execution_slots=1, include_auto_probes=False, include_model_probes=False)
        for item in inventory[:anchor_count]:
            task_path = root / item["path"]
            profile = run_task(load_task(task_path), config=cfg)
            anchors.append(
                {
                    "task_id": item["id"],
                    "task_path": item["path"],
                    "profile_fingerprint": sha256_json({
                        "verdict": profile.verdict.value,
                        "metrics": profile.metrics.to_dict(),
                        "findings": [
                            {"type": f.type.value, "severity": f.severity.value, "probe_id": f.probe_id}
                            for f in profile.findings
                        ],
                        "pairs": [
                            {"probe_id": p.probe.id, "actual": p.actual_verdict.value, "held": p.relation_held}
                            for p in profile.pairs
                        ],
                    }),
                }
            )
    payload = {
        "schema": LOCK_SCHEMA,
        "graderprobe_version": __version__,
        # Keep lockfiles portable and safe to publish. The repository root is
        # represented relative to itself instead of leaking a maintainer's
        # local absolute filesystem path.
        "repository": ".",
        "locked_commit": commit,
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "task_root": task_root_path.relative_to(root).as_posix(),
        "task_inventory": inventory,
        "anchors": anchors,
    }
    payload["lock_fingerprint"] = "sha256:" + sha256_json(payload)
    try:
        import jsonschema
        schema_candidates = [
            Path(__file__).resolve().parent / "schemas" / "contract_lock.schema.json",
            Path(__file__).resolve().parents[2] / "schemas" / "contract_lock.schema.json",
        ]
        schema_path = next((candidate for candidate in schema_candidates if candidate.is_file()), None)
        if schema_path is not None:
            jsonschema.validate(payload, json.loads(schema_path.read_text(encoding="utf-8")))
    except ImportError:
        pass
    out_path = Path(out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def verify_lock(
    repo: str | Path,
    *,
    lock: str | Path,
    config: RunConfig | None = None,
) -> dict[str, Any]:
    root = Path(repo).resolve()
    lock_path = Path(lock).resolve()
    payload = json.loads(lock_path.read_text(encoding="utf-8"))
    if payload.get("schema") != LOCK_SCHEMA:
        raise ValueError("unsupported contract lock schema")
    expected = str(payload.get("lock_fingerprint", ""))
    unsigned = dict(payload)
    unsigned.pop("lock_fingerprint", None)
    actual = "sha256:" + sha256_json(unsigned)
    if actual != expected:
        return {"decision": "BLOCK", "reason": "lockfile fingerprint mismatch", "lock_fingerprint": expected, "computed_fingerprint": actual}
    locked_commit = str(payload.get("locked_commit", ""))
    current_commit = _resolve_ref(root, "HEAD")
    if not locked_commit or not current_commit:
        return {"decision": "BLOCK", "reason": "unable to resolve locked/current commit"}
    if locked_commit == current_commit:
        return {"decision": "ALLOW", "reason": "HEAD matches locked commit", "locked_commit": locked_commit, "current_commit": current_commit}

    task_root = root / str(payload["task_root"])
    current_inventory = _task_inventory(task_root, root)
    old_by_id = {x["id"]: x for x in payload.get("task_inventory", [])}
    current_by_id = {x["id"]: x for x in current_inventory}
    inventory_changes: list[dict[str, Any]] = []
    for tid in sorted(set(old_by_id) | set(current_by_id)):
        old = old_by_id.get(tid)
        cur = current_by_id.get(tid)
        if old is None:
            inventory_changes.append({"task_id": tid, "kind": "added"})
        elif cur is None:
            inventory_changes.append({"task_id": tid, "kind": "deleted"})
        elif old.get("digest") != cur.get("digest"):
            inventory_changes.append({"task_id": tid, "kind": "changed", "old_digest": old.get("digest"), "new_digest": cur.get("digest")})
    if not inventory_changes:
        # Non-task changes still matter, but if Git says nothing under the task
        # root/evaluator surface changed, no execution is necessary.
        diff = subprocess.run(["git", "-C", str(root), "diff", "--name-only", f"{locked_commit}...HEAD"], capture_output=True, text=True, check=False, timeout=30)
        changed = [x.strip() for x in diff.stdout.splitlines() if x.strip()]
        high_signal = any(
            "/evaluators/" in f or "/graders/" in f or "/verifiers/" in f or "/environments/" in f or "/probes/" in f or f.startswith(".github/")
            for f in changed
        )
        if not high_signal:
            return {"decision": "ALLOW", "reason": "no evaluation-contract paths changed", "locked_commit": locked_commit, "current_commit": current_commit, "changed_files": changed}

    cfg = config or RunConfig(max_workers=1, execution_slots=1, include_auto_probes=False, include_model_probes=False)
    report = release_assurance(root, task_root=task_root, base_ref=locked_commit, head_ref=current_commit, config=cfg)
    return {
        "decision": report.decision,
        "reason": "release assurance evaluated changes against the contract lock",
        "locked_commit": locked_commit,
        "current_commit": current_commit,
        "lock_fingerprint": expected,
        "inventory_changes": inventory_changes,
        "release_fingerprint": report.release_fingerprint,
        "release_report": report.to_dict(),
    }
