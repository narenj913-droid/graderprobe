"""Frozen-candidate causal attribution across evaluator revisions.

This module compares the *same candidate bytes* against base/head evaluation
snapshots. A verdict or boundary-profile change with an unchanged candidate
hash is evidence of evaluation-stack drift, not model/candidate drift.
"""
from __future__ import annotations

import json
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from graderprobe.assurance import (
    _cleanup_materialized,
    _materialize_task_dir,
    _probe_to_dict,
    _rebase_task_to_repo_snapshot,
    _resolve_ref,
)
from graderprobe.hashes import hash_tree, merkle_like, sha256_bytes, sha256_json
from graderprobe.runner import RunConfig, run_task
from graderprobe.task import load_task


@dataclass(frozen=True)
class FrozenAnchor:
    task: str
    candidate: str
    label: str = ""


@dataclass(frozen=True)
class CausalComparison:
    task: str
    candidate: str
    label: str
    candidate_sha256: str | None
    base_candidate_sha256: str | None
    candidate_unchanged: bool
    base_verdict: str
    head_verdict: str
    base_outcome: str | None
    head_outcome: str | None
    evaluator_categories: tuple[str, ...]
    status: str
    decision: str
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "task": self.task,
            "candidate": self.candidate,
            "label": self.label,
            "candidate_sha256": self.candidate_sha256,
            "base_candidate_sha256": self.base_candidate_sha256,
            "candidate_unchanged": self.candidate_unchanged,
            "base_verdict": self.base_verdict,
            "head_verdict": self.head_verdict,
            "base_outcome": self.base_outcome,
            "head_outcome": self.head_outcome,
            "evaluator_categories": list(self.evaluator_categories),
            "status": self.status,
            "decision": self.decision,
            "notes": list(self.notes),
        }


@dataclass(frozen=True)
class CausalAuditReport:
    schema: str
    graderprobe_version: str
    repository: str
    base_ref: str
    head_ref: str
    base_commit: str | None
    head_commit: str | None
    cohort_id: str
    comparisons: tuple[CausalComparison, ...]
    decision: str
    fingerprint: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "graderprobe_version": self.graderprobe_version,
            "repository": self.repository,
            "base_ref": self.base_ref,
            "head_ref": self.head_ref,
            "base_commit": self.base_commit,
            "head_commit": self.head_commit,
            "cohort_id": self.cohort_id,
            "comparisons": [c.to_dict() for c in self.comparisons],
            "decision": self.decision,
            "fingerprint": self.fingerprint,
        }


def load_cohort(path: str | Path) -> tuple[FrozenAnchor, ...]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if raw.get("schema") != "graderprobe.frozen_cohort.v1":
        raise ValueError("unsupported frozen cohort schema")
    try:
        import jsonschema
        candidates = [
            Path(__file__).resolve().parent / "schemas" / "frozen_cohort.schema.json",
            Path(__file__).resolve().parents[2] / "schemas" / "frozen_cohort.schema.json",
        ]
        schema_path = next((candidate for candidate in candidates if candidate.is_file()), None)
        if schema_path is not None:
            jsonschema.validate(raw, json.loads(schema_path.read_text(encoding="utf-8")))
    except ImportError:
        pass
    anchors = []
    for item in raw.get("anchors", []):
        anchors.append(FrozenAnchor(task=str(item["task"]), candidate=str(item["candidate"]), label=str(item.get("label", ""))))
    if not anchors:
        raise ValueError("frozen cohort contains no anchors")
    return tuple(anchors)


def _git_file_bytes(repo: Path, ref: str, rel: str) -> bytes | None:
    proc = subprocess.run(
        ["git", "-C", str(repo), "show", f"{ref}:{rel}"],
        capture_output=True,
        check=False,
        timeout=20,
    )
    if proc.returncode != 0:
        return None
    return proc.stdout


def _task_rel(root: Path, task_file: Path) -> str:
    return task_file.parent.relative_to(root).as_posix()


def _profile_fingerprint(profile: Any) -> str:
    """Stable semantic fingerprint that ignores absolute workspace paths/timestamps."""
    return sha256_json(
        {
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
                    "probe_id": p.probe.id,
                    "expected_relation": p.expected_relation.value,
                    "actual_verdict": p.actual_verdict.value,
                    "relation_held": p.relation_held,
                    "evidence_level": p.evidence_level.value,
                }
                for p in profile.pairs
            ],
        }
    )


def _classify_categories(repo: Path, base_ref: str, head_ref: str, task_rel: str) -> tuple[str, ...]:
    from graderprobe.assurance import changed_file_manifest, _categories_for_task

    manifest = changed_file_manifest(repo, base_ref=base_ref, head_ref=head_ref)
    task_path = repo / task_rel / "task.yaml"
    # If the current head task is unavailable, derive coarse categories from paths.
    return tuple(sorted(set(_categories_for_task(task_path, manifest, repo))))


def causal_audit(
    repo: str | Path,
    *,
    cohort: str | Path,
    base_ref: str = "HEAD~1",
    head_ref: str = "HEAD",
    config: RunConfig | None = None,
) -> CausalAuditReport:
    root = Path(repo).resolve()
    anchors = load_cohort(cohort)
    config = config or RunConfig(max_workers=1, execution_slots=1, include_auto_probes=False, include_model_probes=False)
    base_commit = _resolve_ref(root, base_ref)
    head_commit = _resolve_ref(root, head_ref)
    if not base_commit or not head_commit:
        raise RuntimeError("unable to resolve base/head git revision")

    cohort_id = "sha256:" + sha256_json(
        {
            "base": base_commit,
            "head": head_commit,
            "anchors": [{"task": a.task, "candidate": a.candidate, "label": a.label} for a in anchors],
        }
    )

    base_snapshot = _materialize_task_dir(root, base_ref, root, full_repo=True)
    head_snapshot = _materialize_task_dir(root, head_ref, root, full_repo=True)
    if base_snapshot is None or head_snapshot is None:
        if base_snapshot:
            _cleanup_materialized(base_snapshot)
        if head_snapshot:
            _cleanup_materialized(head_snapshot)
        raise RuntimeError("unable to materialize base/head repository snapshots")

    comparisons: list[CausalComparison] = []
    try:
        for anchor in anchors:
            task_rel = Path(anchor.task).as_posix()
            if not task_rel.endswith("task.yaml"):
                task_rel = f"{task_rel.rstrip('/')}/task.yaml"
            task_parent = str(Path(task_rel).parent).replace("\\", "/")
            candidate_rel = Path(anchor.candidate).as_posix()
            head_bytes = _git_file_bytes(root, head_ref, candidate_rel)
            base_bytes = _git_file_bytes(root, base_ref, candidate_rel)
            head_hash = sha256_bytes(head_bytes) if head_bytes is not None else None
            base_hash = sha256_bytes(base_bytes) if base_bytes is not None else None
            if head_bytes is None:
                comparisons.append(CausalComparison(anchor.task, anchor.candidate, anchor.label, None, base_hash, False, "NOT_AVAILABLE", "NOT_RUN", None, None, (), "MISSING_HEAD_CANDIDATE", "WARN", ("head candidate is missing",)))
                continue
            if base_hash != head_hash:
                comparisons.append(CausalComparison(anchor.task, anchor.candidate, anchor.label, head_hash, base_hash, False, "NOT_COMPARABLE", "NOT_COMPARABLE", None, None, _classify_categories(root, base_ref, head_ref, task_parent), "CANDIDATE_DRIFT", "WARN", ("candidate bytes changed across revisions",)))
                continue

            base_task_path = base_snapshot / task_rel
            head_task_path = head_snapshot / task_rel
            if not base_task_path.is_file() or not head_task_path.is_file():
                comparisons.append(CausalComparison(anchor.task, anchor.candidate, anchor.label, head_hash, base_hash, True, "NOT_AVAILABLE", "NOT_AVAILABLE", None, None, _classify_categories(root, base_ref, head_ref, task_parent), "TASK_MISSING", "WARN", ("task missing from one snapshot",)))
                continue

            # Inject identical candidate bytes into both snapshots. This prevents candidate/model drift
            # from masquerading as evaluator drift, while leaving the rest of each revision intact.
            for snap in (base_snapshot, head_snapshot):
                target = snap / candidate_rel
                target.parent.mkdir(parents=True, exist_ok=True)
                if target.resolve() != (snap / candidate_rel).resolve():
                    raise RuntimeError("candidate path resolution failure")
                target.write_bytes(head_bytes)

            base_task = load_task(base_task_path)
            head_task = load_task(head_task_path)
            base_exec = _rebase_task_to_repo_snapshot(base_task, task_parent, base_snapshot)
            head_exec = _rebase_task_to_repo_snapshot(head_task, task_parent, head_snapshot)
            head_profile = run_task(head_exec, config=config)
            replay = [_probe_to_dict(p.probe) for p in head_profile.pairs]
            base_cfg = RunConfig(**{**config.__dict__, "replay_probes": replay, "include_auto_probes": False, "include_auto_sensitivity": False, "include_model_probes": False, "model_provider": None})
            base_profile = run_task(base_exec, config=base_cfg)
            base_outcome = _profile_fingerprint(base_profile)
            head_outcome = _profile_fingerprint(head_profile)
            drift = base_outcome != head_outcome
            status = "EVALUATOR_DRIFT" if drift else "STABLE"
            decision = "WARN" if drift else "ALLOW"
            notes = ("same candidate bytes were injected into both revisions", "profile fingerprint ignores workspace/timestamp noise")
            comparisons.append(CausalComparison(anchor.task, anchor.candidate, anchor.label, head_hash, base_hash, True, base_profile.verdict.value, head_profile.verdict.value, base_outcome, head_outcome, _classify_categories(root, base_ref, head_ref, task_parent), status, decision, notes))
    finally:
        _cleanup_materialized(base_snapshot)
        _cleanup_materialized(head_snapshot)

    decision = "WARN" if any(c.decision == "WARN" for c in comparisons) else "ALLOW"
    fingerprint = "sha256:" + sha256_json({"cohort_id": cohort_id, "decision": decision, "comparisons": [c.to_dict() for c in comparisons]})
    return CausalAuditReport(
        schema="graderprobe.causal_audit.v1",
        graderprobe_version=__import__("graderprobe").__version__,
        repository=str(root),
        base_ref=base_ref,
        head_ref=head_ref,
        base_commit=base_commit,
        head_commit=head_commit,
        cohort_id=cohort_id,
        comparisons=tuple(comparisons),
        decision=decision,
        fingerprint=fingerprint,
    )


def write_causal_report(report: CausalAuditReport, out_dir: str | Path) -> tuple[Path, Path]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    json_path = out / "causal-audit.json"
    md_path = out / "causal-audit.md"
    json_path.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# GraderProbe Causal Attribution",
        "",
        f"**Decision:** `{report.decision}`",
        f"**Base:** `{report.base_ref}` ({report.base_commit})",
        f"**Head:** `{report.head_ref}` ({report.head_commit})",
        f"**Cohort:** `{report.cohort_id}`",
        "",
        "| Anchor | Candidate unchanged | Base | Head | Status | Decision |",
        "|---|---|---|---|---|---|",
    ]
    for c in report.comparisons:
        lines.append(f"| `{c.task}` | `{c.candidate_unchanged}` | `{c.base_verdict}` | `{c.head_verdict}` | `{c.status}` | `{c.decision}` |")
    lines += ["", f"**Fingerprint:** `{report.fingerprint}`", ""]
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, md_path
